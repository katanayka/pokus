import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import TruncDate
from django.utils import timezone

from app.domain.entities import BattleContext, BattleSeed, LobbyEntry as LobbyEntryEntity, Pokemon
from app.models import ActivePokemon, ActiveTeam, Battle, BattleEvent, LobbyEntry, Statistics, UserPokemon
from app.ports.repos import BattleRepoPort, CatalogPort, LobbyPort
from app.ports.stats import StatsPort
from app.ports.users import BOT_USERNAME, UserPort


def _to_pokemon(instance: UserPokemon) -> Pokemon:
    return Pokemon(id=instance.pokemon_id, name=instance.name, types=instance.types, stats=instance.stats.copy())


_USER_POKEMON_CACHE_TTL_SECONDS = 24 * 3600


def _user_pokemon_cache_key(user_id: int, pokemon_id: int) -> str:
    return f"userpoke:v1:{user_id}:{pokemon_id}"


def _replay_signature(replay: dict) -> str:
    payload = json.dumps(replay, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), payload, hashlib.sha256).hexdigest()


class CatalogRepository(CatalogPort):
    def list_user_pokemon(self, user_id: int) -> List[Pokemon]:
        pokes = [_to_pokemon(p) for p in UserPokemon.objects.filter(user_id=user_id).order_by("pokemon_id")]
        for p in pokes:
            cache.set(_user_pokemon_cache_key(user_id, p.id), p, timeout=_USER_POKEMON_CACHE_TTL_SECONDS)
        return pokes

    def get_user_pokemon(self, user_id: int, pokemon_id: int) -> Pokemon | None:
        cached = cache.get(_user_pokemon_cache_key(user_id, pokemon_id))
        if isinstance(cached, Pokemon):
            return cached

        instance = UserPokemon.objects.filter(user_id=user_id, pokemon_id=pokemon_id).first()
        if not instance:
            return None
        pokemon = _to_pokemon(instance)
        cache.set(_user_pokemon_cache_key(user_id, pokemon_id), pokemon, timeout=_USER_POKEMON_CACHE_TTL_SECONDS)
        return pokemon

    def upsert_user_pokemon(self, user_id: int, pokemon: Pokemon) -> Pokemon:
        instance, _ = UserPokemon.objects.update_or_create(
            user_id=user_id,
            pokemon_id=pokemon.id,
            defaults={"name": pokemon.name, "stats": pokemon.stats, "types": pokemon.types},
        )
        stored = _to_pokemon(instance)
        cache.set(_user_pokemon_cache_key(user_id, pokemon.id), stored, timeout=_USER_POKEMON_CACHE_TTL_SECONDS)
        return stored

    def set_active(self, user_id: int, pokemon_id: int) -> None:
        pokemon = UserPokemon.objects.get(user_id=user_id, pokemon_id=pokemon_id)
        ActivePokemon.objects.update_or_create(user=pokemon.user, defaults={"pokemon": pokemon})

    def get_active(self, user_id: int) -> Pokemon | None:
        try:
            ap = ActivePokemon.objects.select_related("pokemon").get(user_id=user_id)
        except ActivePokemon.DoesNotExist:
            return None
        return _to_pokemon(ap.pokemon)

    def set_active_team(self, user_id: int, pokemon_ids: List[int]) -> None:
        ids = [int(x) for x in pokemon_ids]
        ActiveTeam.objects.update_or_create(user_id=user_id, defaults={"pokemon_ids": ids})

    def get_active_team_ids(self, user_id: int) -> List[int]:
        try:
            team = ActiveTeam.objects.get(user_id=user_id)
        except ActiveTeam.DoesNotExist:
            return []
        ids = team.pokemon_ids or []
        if not isinstance(ids, list):
            return []
        out: List[int] = []
        for x in ids:
            try:
                out.append(int(x))
            except (TypeError, ValueError):
                continue
        return out


class BattleRepository(BattleRepoPort):
    def create_battle(
        self,
        p1: int,
        p2: int,
        p1_team: List[Pokemon],
        p2_team: List[Pokemon],
        seed: int,
        type_chart: dict[str, dict[str, float]],
        order: List[str],
        initiative: Dict,
    ) -> int:
        if not p1_team or not p2_team:
            raise ValueError("Both teams must contain at least 1 Pokémon.")
        p1_team_ids = [p.id for p in p1_team]
        p2_team_ids = [p.id for p in p2_team]
        if not (isinstance(order, list) and len(order) == 2 and set(order) == {"a", "b"}):
            raise ValueError("Invalid turn order.")
        if not isinstance(initiative, dict):
            initiative = {}
        battle = Battle.objects.create(
            p1_id=p1,
            p2_id=p2,
            p1_pokemon_id=p1_team[0].id,
            p2_pokemon_id=p2_team[0].id,
            p1_team_ids=p1_team_ids,
            p2_team_ids=p2_team_ids,
            seed=seed,
            status="active",
            result={
                "state": {
                    "a": {
                        "active": 0,
                        "hp": [p.stats["hp"] for p in p1_team],
                        "effects": {"atk_mod": 1.0, "atk_turns": 0, "defend": 0},
                    },
                    "b": {
                        "active": 0,
                        "hp": [p.stats["hp"] for p in p2_team],
                        "effects": {"atk_mod": 1.0, "atk_turns": 0, "defend": 0},
                    },
                    "turn": 0,
                    "phase": 0,
                    "order": order,
                    "next_actor": order[0],
                    "initiative": initiative,
                },
                "type_chart": type_chart,
                "teams": {
                    "a": [{"id": p.id, "name": p.name, "types": p.types, "stats": p.stats} for p in p1_team],
                    "b": [{"id": p.id, "name": p.name, "types": p.types, "stats": p.stats} for p in p2_team],
                },
            },
        )
        return battle.id

    def load_battle(self, battle_id: int) -> BattleContext:
        b = Battle.objects.get(id=battle_id)
        result = b.result or {}
        teams = result.get("teams") or {}

        def _team_from_result(role: str) -> List[Pokemon]:
            raw_team = teams.get(role, [])
            if isinstance(raw_team, list) and raw_team:
                out: List[Pokemon] = []
                for item in raw_team:
                    if not isinstance(item, dict):
                        continue
                    try:
                        pid = int(item.get("id"))
                    except (TypeError, ValueError):
                        continue
                    name = str(item.get("name") or "")
                    types = list(item.get("types") or [])
                    stats = dict(item.get("stats") or {})
                    out.append(Pokemon(id=pid, name=name, types=types, stats=stats))
                if out:
                    return out
            return []

        p1_team = _team_from_result("a")
        p2_team = _team_from_result("b")

        if not p1_team:
            ids = b.p1_team_ids or [b.p1_pokemon_id]
            rows = UserPokemon.objects.filter(user_id=b.p1_id, pokemon_id__in=ids)
            by_id = {r.pokemon_id: r for r in rows}
            p1_team = [_to_pokemon(by_id[pokemon_id]) for pokemon_id in ids if pokemon_id in by_id]
        if not p2_team:
            ids = b.p2_team_ids or [b.p2_pokemon_id]
            rows = UserPokemon.objects.filter(user_id=b.p2_id, pokemon_id__in=ids)
            by_id = {r.pokemon_id: r for r in rows}
            p2_team = [_to_pokemon(by_id[pokemon_id]) for pokemon_id in ids if pokemon_id in by_id]

        state = result.get("state", {}) or {}
        a_state = state.get("a") if isinstance(state, dict) else None
        b_state = state.get("b") if isinstance(state, dict) else None
        a_active = int(a_state.get("active", 0)) if isinstance(a_state, dict) else 0
        b_active = int(b_state.get("active", 0)) if isinstance(b_state, dict) else 0
        a_active = max(0, min(a_active, max(0, len(p1_team) - 1)))
        b_active = max(0, min(b_active, max(0, len(p2_team) - 1)))
        p1_active = (
            p1_team[a_active]
            if p1_team
            else _to_pokemon(UserPokemon.objects.get(user_id=b.p1_id, pokemon_id=b.p1_pokemon_id))
        )
        p2_active = (
            p2_team[b_active]
            if p2_team
            else _to_pokemon(UserPokemon.objects.get(user_id=b.p2_id, pokemon_id=b.p2_pokemon_id))
        )

        return BattleContext(
            id=b.id,
            status=b.status,
            p1_id=b.p1_id,
            p2_id=b.p2_id,
            p1_team=p1_team or [p1_active],
            p2_team=p2_team or [p2_active],
            p1_pokemon=p1_active,
            p2_pokemon=p2_active,
            seed=BattleSeed(b.seed),
            type_chart=result.get("type_chart", {}),
            pending_actions=result.get("pending_actions", {"a": None, "b": None}),
            log=[],
            state=state,
            created_at=int(b.created_at.timestamp()) if b.created_at else None,
        )

    def save_turn(self, battle_id: int, turn: Dict) -> None:
        BattleEvent.objects.create(battle_id=battle_id, turn=turn.get("turn", 0), payload=turn)

    def update_state(self, battle_id: int, state: Dict) -> None:
        battle = Battle.objects.get(id=battle_id)
        result = battle.result or {}
        result["state"] = state
        Battle.objects.filter(id=battle_id).update(result=result)

    def finish(self, battle_id: int, result: Dict) -> None:
        battle = Battle.objects.get(id=battle_id)
        prev = battle.result or {}
        prev.update(result)
        if "replay" in prev:
            prev["replay_sig"] = _replay_signature(prev["replay"])
        Battle.objects.filter(id=battle_id).update(status="finished", result=prev)

    def update_pending_actions(self, battle_id: int, pending_actions: Dict[str, Dict | None]) -> None:
        battle = Battle.objects.get(id=battle_id)
        result = battle.result or {}
        result["pending_actions"] = pending_actions
        Battle.objects.filter(id=battle_id).update(result=result)

    def list_battles(self, user_id: int) -> List[Dict]:
        rows = Battle.objects.filter(Q(p1_id=user_id) | Q(p2_id=user_id)).select_related("p1", "p2")
        items: List[Dict] = []
        for b in rows.order_by("-created_at"):
            role = "a" if b.p1_id == user_id else "b"
            opponent_user = b.p2 if role == "a" else b.p1
            opponent_id = int(opponent_user.id)
            opponent_username = str(getattr(opponent_user, "username", "") or "")
            items.append(
                {
                    "id": b.id,
                    "status": b.status,
                    "result": b.result,
                    "role": role,
                    "opponent_id": opponent_id,
                    "opponent_username": opponent_username,
                    "created_at": b.created_at.isoformat(),
                }
            )
        return items

    def list_events(self, battle_id: int) -> List[Dict]:
        return [evt.payload for evt in BattleEvent.objects.filter(battle_id=battle_id).order_by("id")]

    def get_replay(self, battle_id: int) -> Dict | None:
        battle = Battle.objects.get(id=battle_id)
        result = battle.result or {}
        replay = result.get("replay")
        if not replay:
            return None
        sig = result.get("replay_sig")
        expected = _replay_signature(replay)
        if not sig or not hmac.compare_digest(sig, expected):
            raise ValueError("Replay integrity check failed.")
        replay_with_sig = dict(replay)
        replay_with_sig["signature"] = sig
        return replay_with_sig

    def get_battle_item(self, user_id: int, battle_id: int) -> Dict | None:
        try:
            b = Battle.objects.select_related("p1", "p2").get(id=battle_id)
        except Battle.DoesNotExist:
            return None

        if user_id not in (b.p1_id, b.p2_id):
            return None

        role = "a" if b.p1_id == user_id else "b"
        opponent_user = b.p2 if role == "a" else b.p1
        opponent_id = int(opponent_user.id)
        opponent_username = str(getattr(opponent_user, "username", "") or "")
        return {
            "id": b.id,
            "status": b.status,
            "result": b.result,
            "role": role,
            "opponent_id": opponent_id,
            "opponent_username": opponent_username,
            "created_at": b.created_at.isoformat(),
        }


class LobbyRepository(LobbyPort):
    def enqueue(self, user_id: int, pokemon_ids: List[int]) -> None:
        ids = [int(x) for x in pokemon_ids]
        if not ids:
            raise ValueError("Team is required.")
        LobbyEntry.objects.filter(user_id=user_id).delete()
        LobbyEntry.objects.create(user_id=user_id, pokemon_id=ids[0], team_ids=ids, code=None)

    @transaction.atomic
    def try_match(self, user_id: int) -> LobbyEntryEntity | None:
        LobbyEntry.objects.filter(user_id=user_id).delete()
        entry = (
            LobbyEntry.objects.select_for_update(skip_locked=True)
            .filter(code__isnull=True)
            .exclude(user_id=user_id)
            .order_by("created_at")
            .first()
        )
        if not entry:
            return None
        ids = entry.team_ids if isinstance(entry.team_ids, list) and entry.team_ids else [entry.pokemon_id]
        match = LobbyEntryEntity(user_id=entry.user_id, pokemon_ids=[int(x) for x in ids])
        entry.delete()
        return match

    def open_code_lobby(self, user_id: int, pokemon_ids: List[int], code: str) -> None:
        ids = [int(x) for x in pokemon_ids]
        if not ids:
            raise ValueError("Team is required.")
        code = str(code or "").strip()
        if not (len(code) == 4 and code.isdigit()):
            raise ValueError("Lobby code must be exactly 4 digits.")

        LobbyEntry.objects.filter(user_id=user_id).delete()
        try:
            LobbyEntry.objects.create(user_id=user_id, pokemon_id=ids[0], team_ids=ids, code=code)
        except IntegrityError as exc:
            raise ValueError("Lobby code is already in use.") from exc

    @transaction.atomic
    def try_match_code_lobby(self, user_id: int, code: str) -> LobbyEntryEntity | None:
        code = str(code or "").strip()
        if not (len(code) == 4 and code.isdigit()):
            raise ValueError("Lobby code must be exactly 4 digits.")

        LobbyEntry.objects.filter(user_id=user_id).delete()
        entry = (
            LobbyEntry.objects.select_for_update(skip_locked=True)
            .filter(code=code)
            .exclude(user_id=user_id)
            .order_by("created_at")
            .first()
        )
        if not entry:
            return None
        ids = entry.team_ids if isinstance(entry.team_ids, list) and entry.team_ids else [entry.pokemon_id]
        match = LobbyEntryEntity(user_id=entry.user_id, pokemon_ids=[int(x) for x in ids])
        entry.delete()
        return match

    def close_code_lobby(self, user_id: int, code: str) -> bool:
        code = str(code or "").strip()
        if not (len(code) == 4 and code.isdigit()):
            raise ValueError("Lobby code must be exactly 4 digits.")
        deleted, _ = LobbyEntry.objects.filter(user_id=user_id, code=code).delete()
        return deleted > 0


class UserRepository(UserPort):
    def create_user(self, username: str, password: str) -> tuple[int, str]:
        User = get_user_model()
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
        except IntegrityError as exc:
            raise ValueError("Username already exists.") from exc
        return int(user.id), str(getattr(user, "username", username))

    def get_or_create_bot_user_id(self) -> int:
        User = get_user_model()
        with transaction.atomic():
            user, created = User.objects.get_or_create(username=BOT_USERNAME)
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
        return int(user.id)


class StatisticsRepository(StatsPort):
    def get_user_stats(self, user_id: int) -> dict:
        stats_obj, _ = Statistics.objects.get_or_create(user_id=user_id)

        battles_qs = Battle.objects.filter(status="finished").filter(Q(p1_id=user_id) | Q(p2_id=user_id))

        win_expr = Case(
            When(Q(p1_id=user_id, result__outcome__winner="a"), then=Value(1)),
            When(Q(p2_id=user_id, result__outcome__winner="b"), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
        loss_expr = Case(
            When(Q(p1_id=user_id, result__outcome__winner="b"), then=Value(1)),
            When(Q(p2_id=user_id, result__outcome__winner="a"), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
        draw_expr = Case(
            When(result__outcome__draw=True, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )

        draws = battles_qs.filter(result__outcome__draw=True).count()
        total_battles = battles_qs.count()

        per_pokemon: dict[int, dict] = {}
        for b in battles_qs.only(
            "id", "p1_id", "p2_id", "p1_pokemon_id", "p2_pokemon_id", "p1_team_ids", "p2_team_ids", "result"
        ):
            role = "a" if b.p1_id == user_id else "b"
            team_ids = b.p1_team_ids if role == "a" else b.p2_team_ids
            if not isinstance(team_ids, list) or not team_ids:
                team_ids = [b.p1_pokemon_id] if role == "a" else [b.p2_pokemon_id]

            ids: list[int] = []
            for x in team_ids:
                try:
                    ids.append(int(x))
                except (TypeError, ValueError):
                    continue
            ids = list(dict.fromkeys(ids))
            if not ids:
                continue

            outcome = {}
            if isinstance(b.result, dict):
                outcome = b.result.get("outcome") or {}

            win = loss = draw = 0
            if isinstance(outcome, dict) and outcome.get("draw") is True:
                draw = 1
            else:
                winner = outcome.get("winner")
                if winner in ("a", "b"):
                    if winner == role:
                        win = 1
                    else:
                        loss = 1

            for pokemon_id in ids:
                row = per_pokemon.get(pokemon_id)
                if not row:
                    row = {"pokemon_id": pokemon_id, "battles": 0, "wins": 0, "losses": 0, "draws": 0}
                    per_pokemon[pokemon_id] = row
                row["battles"] += 1
                row["wins"] += win
                row["losses"] += loss
                row["draws"] += draw

        top_rows = sorted(
            per_pokemon.values(), key=lambda r: (-int(r["battles"]), -int(r["wins"]), int(r["pokemon_id"]))
        )[:3]
        top_ids = [row["pokemon_id"] for row in top_rows if isinstance(row.get("pokemon_id"), int)]
        names_by_id = {
            p.pokemon_id: p.name
            for p in UserPokemon.objects.filter(user_id=user_id, pokemon_id__in=top_ids).only("pokemon_id", "name")
        }
        top_pokemons = []
        for row in top_rows:
            pokemon_id = row.get("pokemon_id")
            if not isinstance(pokemon_id, int):
                continue
            wins = int(row.get("wins") or 0)
            losses = int(row.get("losses") or 0)
            p_draws = int(row.get("draws") or 0)
            battles = int(row.get("battles") or 0)
            den = max(1, wins + losses)
            win_rate = (wins * 100.0) / den
            top_pokemons.append(
                {
                    "pokemon_id": pokemon_id,
                    "name": names_by_id.get(pokemon_id),
                    "battles": battles,
                    "wins": wins,
                    "losses": losses,
                    "draws": p_draws,
                    "win_rate": win_rate,
                }
            )

        days = 14
        start_dt = timezone.now() - timedelta(days=days - 1)
        daily_rows = (
            battles_qs.filter(created_at__gte=start_dt)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                battles=Count("id"),
                wins=Sum(win_expr),
                losses=Sum(loss_expr),
                draws=Sum(draw_expr),
            )
        )
        daily_by_day = {row["day"].isoformat(): row for row in daily_rows if row.get("day")}
        start_date = start_dt.date()
        daily = []
        for i in range(days):
            day = (start_date + timedelta(days=i)).isoformat()
            row = daily_by_day.get(day, {})
            daily.append(
                {
                    "date": day,
                    "battles": int(row.get("battles") or 0),
                    "wins": int(row.get("wins") or 0),
                    "losses": int(row.get("losses") or 0),
                    "draws": int(row.get("draws") or 0),
                }
            )

        return {
            "wins": stats_obj.wins,
            "losses": stats_obj.losses,
            "draws": draws,
            "battles_total": total_battles,
            "damage": stats_obj.damage,
            "crits": stats_obj.crits,
            "win_rate": float(stats_obj.win_rate),
            "top_pokemons": top_pokemons,
            "daily": daily,
        }

    @transaction.atomic
    def record_battle_result(
        self, winner_user_id: int, loser_user_id: int, total_damage: int, total_crits: int
    ) -> None:
        win_stats, _ = Statistics.objects.select_for_update().get_or_create(user_id=winner_user_id)
        lose_stats, _ = Statistics.objects.select_for_update().get_or_create(user_id=loser_user_id)

        win_stats.wins += 1
        win_stats.damage += total_damage
        win_stats.crits += total_crits
        lose_stats.losses += 1

        win_den = Decimal(max(1, win_stats.wins + win_stats.losses))
        lose_den = Decimal(max(1, lose_stats.wins + lose_stats.losses))
        win_stats.win_rate = (Decimal(win_stats.wins) * Decimal("100")) / win_den
        lose_stats.win_rate = (Decimal(lose_stats.wins) * Decimal("100")) / lose_den

        win_stats.save()
        lose_stats.save()
