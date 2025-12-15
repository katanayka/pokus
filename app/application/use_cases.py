import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from app.domain.services import BattleEngine, type_multiplier
from app.ports.notification import NotificationPort
from app.ports.repos import BattleRepoPort, CatalogPort, LobbyPort
from app.ports.pokeapi import PokeApiPort
from app.ports.stats import StatsPort
from app.ports.users import BOT_USERNAME, UserPort

BATTLE_TTL_SECONDS = 15 * 60
POKEAPI_FETCH_WORKERS = 6
TURN_SEED_STRIDE = 3


class CatalogUC:
    def __init__(self, catalog: CatalogPort, pokeapi: PokeApiPort, seed_limit: int = 20):
        self.catalog = catalog
        self.pokeapi = pokeapi
        self.seed_limit = seed_limit

    def _fetch_pokemons(self, pokemon_ids: list[int]):
        if not pokemon_ids:
            return []

        max_workers = min(POKEAPI_FETCH_WORKERS, len(pokemon_ids))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.pokeapi.fetch_pokemon, pokemon_ids))

    def list(self, user_id: int):
        current = self.catalog.list_user_pokemon(user_id)
        if current:
            return current

        pokemon_ids = self.pokeapi.list_pokemon_ids(limit=self.seed_limit, offset=0)
        for pokemon in self._fetch_pokemons(pokemon_ids):
            self.catalog.upsert_user_pokemon(user_id, pokemon)

        return self.catalog.list_user_pokemon(user_id)

    def page(self, user_id: int, limit: int = 20, offset: int = 0):
        limit = max(1, min(int(limit), 50))
        offset = max(0, int(offset))

        pokemon_ids = self.pokeapi.list_pokemon_ids(limit=limit, offset=offset)

        pokes_by_id = {}
        missing_ids: list[int] = []
        for pokemon_id in pokemon_ids:
            existing = self.catalog.get_user_pokemon(user_id, pokemon_id)
            if existing:
                pokes_by_id[pokemon_id] = existing
            else:
                missing_ids.append(pokemon_id)

        for pokemon in self._fetch_pokemons(missing_ids):
            stored = self.catalog.upsert_user_pokemon(user_id, pokemon)
            pokes_by_id[stored.id] = stored

        return [pokes_by_id[pokemon_id] for pokemon_id in pokemon_ids if pokemon_id in pokes_by_id]


class GetPokemonUC:
    def __init__(self, catalog: CatalogPort, pokeapi: PokeApiPort):
        self.catalog = catalog
        self.pokeapi = pokeapi

    def execute(self, user_id: int, pokemon_id: int):
        pokemon_id = int(pokemon_id)
        existing = self.catalog.get_user_pokemon(user_id, pokemon_id)
        if existing:
            return existing
        pokemon = self.pokeapi.fetch_pokemon(pokemon_id)
        return self.catalog.upsert_user_pokemon(user_id, pokemon)


class SearchPokemonUC:
    def __init__(self, catalog: CatalogPort, pokeapi: PokeApiPort):
        self.catalog = catalog
        self.pokeapi = pokeapi
        self.get_pokemon = GetPokemonUC(catalog, pokeapi)

    def execute(self, user_id: int, query: str, limit: int = 20, offset: int = 0):
        query = str(query or "").strip()
        if not query:
            raise ValueError("Search query is required.")

        if query.isdigit():
            return [self.get_pokemon.execute(user_id, int(query))]

        pokemon_ids = self.pokeapi.search_pokemon_ids(query.lower(), limit=limit, offset=offset)
        if not pokemon_ids:
            return []

        pokes_by_id = {}
        missing_ids: list[int] = []
        for pokemon_id in pokemon_ids:
            existing = self.catalog.get_user_pokemon(user_id, pokemon_id)
            if existing:
                pokes_by_id[pokemon_id] = existing
            else:
                missing_ids.append(pokemon_id)

        if missing_ids:
            max_workers = min(POKEAPI_FETCH_WORKERS, len(missing_ids))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                fetched = list(executor.map(self.pokeapi.fetch_pokemon, missing_ids))
            for pokemon in fetched:
                stored = self.catalog.upsert_user_pokemon(user_id, pokemon)
                pokes_by_id[stored.id] = stored

        return [pokes_by_id[pokemon_id] for pokemon_id in pokemon_ids if pokemon_id in pokes_by_id]


class SelectPokemonUC:
    def __init__(self, catalog: CatalogPort, pokeapi: PokeApiPort):
        self.catalog = catalog
        self.pokeapi = pokeapi

    def execute(self, user_id: int, pokemon_id: int):
        if not self.catalog.get_user_pokemon(user_id, pokemon_id):
            pokemon = self.pokeapi.fetch_pokemon(pokemon_id)
            self.catalog.upsert_user_pokemon(user_id, pokemon)
        self.catalog.set_active(user_id, pokemon_id)
        return self.catalog.get_user_pokemon(user_id, pokemon_id)


class SetTeamUC:
    def __init__(self, catalog: CatalogPort, pokeapi: PokeApiPort):
        self.catalog = catalog
        self.pokeapi = pokeapi
        self.get_pokemon = GetPokemonUC(catalog, pokeapi)

    def execute(self, user_id: int, pokemon_ids: list[int]) -> list:
        ids = [int(x) for x in (pokemon_ids or [])]
        if len(ids) != 3:
            raise ValueError("Team must contain exactly 3 Pokémon.")
        if len(set(ids)) != 3:
            raise ValueError("Team Pokémon must be unique.")

        team = [self.get_pokemon.execute(user_id, pid) for pid in ids]
        self.catalog.set_active_team(user_id, ids)
        self.catalog.set_active(user_id, ids[0])
        return team


class GetTeamUC:
    def __init__(self, catalog: CatalogPort, pokeapi: PokeApiPort):
        self.catalog = catalog
        self.pokeapi = pokeapi
        self.get_pokemon = GetPokemonUC(catalog, pokeapi)

    def execute(self, user_id: int) -> list:
        ids = self.catalog.get_active_team_ids(user_id)
        if not ids:
            return []
        return [self.get_pokemon.execute(user_id, pid) for pid in ids]


class EnterLobbyUC:
    def __init__(
        self,
        catalog: CatalogPort,
        lobby: LobbyPort,
        battles: BattleRepoPort,
        notifier: NotificationPort,
        pokeapi: PokeApiPort,
    ):
        self.catalog = catalog
        self.lobby = lobby
        self.set_team = SetTeamUC(catalog, pokeapi)
        self.get_team = GetTeamUC(catalog, pokeapi)
        self.start_battle = StartBattleUC(battles, notifier, pokeapi)

    def execute(self, user_id: int, pokemon_ids: list[int] | None = None) -> dict:
        if pokemon_ids is not None:
            self.set_team.execute(user_id, pokemon_ids)

        my_team = self.get_team.execute(user_id)
        if not my_team:
            raise ValueError("Active team not set. Select 3 Pokémon in your catalog first.")

        match = self.lobby.try_match(user_id)
        if match:
            opp_team = [self.catalog.get_user_pokemon(match.user_id, pid) for pid in match.pokemon_ids]
            if any(p is None for p in opp_team):
                raise ValueError("Matched Pokémon not found in catalog.")

            battle_id = self.start_battle.execute(match.user_id, user_id, [p for p in opp_team if p], my_team)
            return {"status": "matched", "battle_id": battle_id, "opponent_id": match.user_id}

        self.lobby.enqueue(user_id, [p.id for p in my_team])
        return {"status": "queued"}


class CodeLobbyUC:
    def __init__(
        self,
        catalog: CatalogPort,
        lobby: LobbyPort,
        battles: BattleRepoPort,
        notifier: NotificationPort,
        pokeapi: PokeApiPort,
    ):
        self.catalog = catalog
        self.lobby = lobby
        self.set_team = SetTeamUC(catalog, pokeapi)
        self.get_team = GetTeamUC(catalog, pokeapi)
        self.start_battle = StartBattleUC(battles, notifier, pokeapi)

    @staticmethod
    def _normalize_code(code: str | int) -> str:
        raw = str(code or "").strip()
        if raw.isdigit() and len(raw) <= 4:
            raw = raw.zfill(4)
        if not (len(raw) == 4 and raw.isdigit()):
            raise ValueError("Lobby code must be exactly 4 digits.")
        return raw

    def execute(self, user_id: int, code: str | int, pokemon_ids: list[int] | None = None) -> dict:
        code = self._normalize_code(code)
        if pokemon_ids is not None:
            self.set_team.execute(user_id, pokemon_ids)

        my_team = self.get_team.execute(user_id)
        if not my_team:
            raise ValueError("Active team not set. Select 3 Pokémon in your catalog first.")

        match = self.lobby.try_match_code_lobby(user_id, code)
        if match:
            opp_team = [self.catalog.get_user_pokemon(match.user_id, pid) for pid in match.pokemon_ids]
            if any(p is None for p in opp_team):
                raise ValueError("Matched Pokémon not found in catalog.")
            battle_id = self.start_battle.execute(match.user_id, user_id, [p for p in opp_team if p], my_team)
            return {"status": "matched", "battle_id": battle_id, "opponent_id": match.user_id}

        self.lobby.open_code_lobby(user_id, [p.id for p in my_team], code)
        return {"status": "open", "code": code}


class CloseCodeLobbyUC:
    def __init__(self, lobby: LobbyPort):
        self.lobby = lobby

    def execute(self, user_id: int, code: str | int) -> dict:
        code = CodeLobbyUC._normalize_code(code)
        self.lobby.close_code_lobby(user_id, code)
        return {"status": "closed", "code": code}


class StartBattleUC:
    def __init__(self, repo: BattleRepoPort, notifier: NotificationPort, pokeapi: PokeApiPort):
        self.repo = repo
        self.notifier = notifier
        self.pokeapi = pokeapi

    def execute(self, p1_id: int, p2_id: int, p1_team, p2_team):
        seed = random.randint(1, 10_000_000)
        types = sorted(set([t for p in [*p1_team, *p2_team] for t in (p.types or [])]))

        max_workers = min(POKEAPI_FETCH_WORKERS, max(1, len(types)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            charts = list(executor.map(self.pokeapi.fetch_type_chart, types))
        type_chart = {t: c for t, c in zip(types, charts)}

        initiative_seed = seed + 0 * TURN_SEED_STRIDE
        first_actor, init_detail = BattleEngine(initiative_seed, type_chart).initiative_detail(
            p1_team[0].stats["speed"], p2_team[0].stats["speed"]
        )
        initiative = {"seed": initiative_seed, "winner": first_actor, **init_detail}
        order = ["a", "b"] if first_actor == "a" else ["b", "a"]
        battle_id = self.repo.create_battle(p1_id, p2_id, p1_team, p2_team, seed, type_chart, order, initiative)
        self.notifier.send(p1_id, "battle_started", {"battle_id": battle_id, "opponent_id": p2_id, "role": "a"})
        self.notifier.send(p2_id, "battle_started", {"battle_id": battle_id, "opponent_id": p1_id, "role": "b"})
        return battle_id


class StartPveBattleUC:
    def __init__(
        self,
        catalog: CatalogPort,
        battles: BattleRepoPort,
        notifier: NotificationPort,
        pokeapi: PokeApiPort,
        users: UserPort,
    ):
        self.catalog = catalog
        self.pokeapi = pokeapi
        self.users = users
        self.set_team = SetTeamUC(catalog, pokeapi)
        self.get_team = GetTeamUC(catalog, pokeapi)
        self.start_battle = StartBattleUC(battles, notifier, pokeapi)

    def _pick_bot_team_ids(self, *, exclude: set[int]) -> list[int]:
        offset = random.randint(0, 2000)
        candidates = [int(x) for x in self.pokeapi.list_pokemon_ids(limit=50, offset=offset)]
        ids = [pid for pid in candidates if pid not in exclude]
        if len(ids) < 3:
            fallback = [int(x) for x in self.pokeapi.list_pokemon_ids(limit=50, offset=0)]
            for pid in fallback:
                if pid in exclude or pid in ids:
                    continue
                ids.append(pid)
                if len(ids) >= 3:
                    break
        return ids[:3]

    def execute(self, user_id: int, pokemon_ids: list[int] | None = None) -> dict:
        if pokemon_ids is not None:
            self.set_team.execute(user_id, pokemon_ids)

        my_team = self.get_team.execute(user_id)
        if not my_team:
            raise ValueError("Active team not set. Select 3 Pokémon in your catalog first.")

        bot_id = self.users.get_or_create_bot_user_id()
        bot_team_ids = self._pick_bot_team_ids(exclude={p.id for p in my_team})
        if len(bot_team_ids) != 3:
            raise ValueError("Failed to select a bot team.")
        bot_team = [self.pokeapi.fetch_pokemon(pid) for pid in bot_team_ids]

        battle_id = self.start_battle.execute(bot_id, user_id, bot_team, my_team)
        return {
            "status": "matched",
            "battle_id": battle_id,
            "opponent_id": bot_id,
            "opponent_username": BOT_USERNAME,
            "mode": "pve",
        }


class PlayTurnUC:
    def __init__(self, repo: BattleRepoPort, notifier: NotificationPort, stats: StatsPort):
        self.repo = repo
        self.notifier = notifier
        self.stats = stats

    def execute(self, battle_id: int, user_id: int, action: Dict) -> dict:
        try:
            battle = self.repo.load_battle(battle_id)
        except Exception as exc:
            raise ValueError("Battle not found.") from exc

        expirer = ExpireBattleUC(self.repo, self.notifier)
        if expirer.expire_if_needed(battle):
            return {"status": "finished", "outcome": {"draw": True, "reason": "timeout"}}

        if battle.status != "active" or battle.state.get("finished"):
            raise ValueError("Battle is not active.")

        if user_id == battle.p1_id:
            role = "a"
            attacker = battle.p1_pokemon
        elif user_id == battle.p2_id:
            role = "b"
            attacker = battle.p2_pokemon
        else:
            raise PermissionError("You are not a participant of this battle.")

        normalized_action = self._normalize_action(battle, role, action, attacker)

        state = dict(battle.state or {})
        turn_index = int(state.get("turn", 0) or 0)
        phase = int(state.get("phase", 0) or 0)
        if phase not in (0, 1):
            phase = 0

        order = state.get("order")
        if not (isinstance(order, list) and len(order) == 2 and set(order) == {"a", "b"}):
            initiative_seed = battle.seed.value + (turn_index * TURN_SEED_STRIDE)
            a_spd = battle.p1_pokemon.stats["speed"]
            b_spd = battle.p2_pokemon.stats["speed"]
            first_actor, init_detail = BattleEngine(initiative_seed, battle.type_chart).initiative_detail(a_spd, b_spd)
            order = ["a", "b"] if first_actor == "a" else ["b", "a"]
            state["initiative"] = {"seed": initiative_seed, "winner": first_actor, **init_detail}

        expected = order[phase]
        if role != expected:
            raise ValueError("Not your turn.")

        state["turn"] = turn_index
        state["phase"] = phase
        state["order"] = order
        state["next_actor"] = expected

        action_seed = battle.seed.value + (turn_index * TURN_SEED_STRIDE) + (1 if phase == 0 else 2)
        log, next_state = BattleEngine(action_seed, battle.type_chart).step(battle, role, normalized_action, state)
        next_state["turn"] = turn_index
        next_state["phase"] = phase
        next_state["order"] = order
        next_state["next_actor"] = expected

        turn_record = {
            "turn": turn_index + 1,
            "phase": phase,
            "rng_seed": action_seed,
            "initiative": order[0],
            "actor": role,
            "action": normalized_action,
            "log": log,
            "state": next_state,
        }
        self.repo.save_turn(battle.id, turn_record)

        if next_state.get("finished"):
            outcome = {"winner": next_state.get("winner"), "loser": next_state.get("loser")}
            if outcome["winner"] is None or outcome["loser"] is None:
                outcome = {"draw": True, "reason": "engine"}
            turns = self.repo.list_events(battle.id)
            replay = {
                "battle_id": battle.id,
                "seed": battle.seed.value,
                "type_chart": battle.type_chart,
                "turns": turns,
                "outcome": outcome,
            }
            self.repo.finish(battle.id, {"state": next_state, "outcome": outcome, "replay": replay})

            self.notifier.send(battle.p1_id, "battle_ended", {"battle_id": battle.id, **outcome})
            self.notifier.send(battle.p2_id, "battle_ended", {"battle_id": battle.id, **outcome})

            if outcome.get("draw"):
                return {"status": "finished", "turn": turn_record, "outcome": outcome}

            win_user_id = battle.p1_id if outcome["winner"] == "a" else battle.p2_id
            lose_user_id = battle.p1_id if outcome["loser"] == "a" else battle.p2_id
            self._record_stats(battle, turns, outcome)
            self.notifier.send(win_user_id, "victory", {"battle_id": battle.id, "opponent_id": lose_user_id})
            self.notifier.send(lose_user_id, "defeat", {"battle_id": battle.id, "opponent_id": win_user_id})
            return {"status": "finished", "turn": turn_record, "outcome": outcome}

        if phase == 0:
            next_state["phase"] = 1
            next_state["next_actor"] = order[1]
        else:
            BattleEngine.decay_effects(next_state)
            next_turn = turn_index + 1
            next_state["turn"] = next_turn
            next_state["phase"] = 0

            a_idx = int(next_state.get("a", {}).get("active", 0) or 0) if isinstance(next_state.get("a"), dict) else 0
            b_idx = int(next_state.get("b", {}).get("active", 0) or 0) if isinstance(next_state.get("b"), dict) else 0
            a_idx = max(0, min(a_idx, max(0, len(battle.p1_team) - 1)))
            b_idx = max(0, min(b_idx, max(0, len(battle.p2_team) - 1)))
            a_spd = battle.p1_team[a_idx].stats["speed"] if battle.p1_team else battle.p1_pokemon.stats["speed"]
            b_spd = battle.p2_team[b_idx].stats["speed"] if battle.p2_team else battle.p2_pokemon.stats["speed"]

            initiative_seed = battle.seed.value + (next_turn * TURN_SEED_STRIDE)
            first_actor, init_detail = BattleEngine(initiative_seed, battle.type_chart).initiative_detail(a_spd, b_spd)
            next_order = ["a", "b"] if first_actor == "a" else ["b", "a"]
            next_state["order"] = next_order
            next_state["next_actor"] = next_order[0]
            next_state["initiative"] = {"seed": initiative_seed, "winner": first_actor, **init_detail}

        self.repo.update_state(battle.id, next_state)
        return {"status": "resolved", "turn": turn_record}

    def _normalize_action(self, battle, role: str, action: Dict, attacker) -> Dict:
        if not isinstance(action, dict):
            raise ValueError("Action must be an object.")

        action_type = str(action.get("type") or "attack").lower()
        if action_type not in {"attack", "defend", "buff", "debuff", "switch"}:
            raise ValueError("Unsupported action type.")

        if action_type == "switch":
            team = battle.p1_team if role == "a" else battle.p2_team
            if len(team) < 2:
                raise ValueError("No other Pokémon to switch to.")

            state = battle.state or {}
            side = state.get(role, {}) if isinstance(state, dict) else {}
            current = int(side.get("active", 0)) if isinstance(side, dict) else 0
            hp_list = side.get("hp", []) if isinstance(side, dict) else []
            if not isinstance(hp_list, list):
                hp_list = []

            target = None
            if "pokemon_id" in action:
                try:
                    pokemon_id = int(action.get("pokemon_id"))
                except (TypeError, ValueError):
                    raise ValueError("Invalid pokemon_id for switch.")
                for idx, p in enumerate(team):
                    if int(p.id) == pokemon_id:
                        target = idx
                        break
            elif "slot" in action:
                try:
                    target = int(action.get("slot"))
                except (TypeError, ValueError):
                    raise ValueError("Invalid slot for switch.")
            else:
                raise ValueError("Switch requires pokemon_id or slot.")

            if target is None or target < 0 or target >= len(team):
                raise ValueError("Invalid switch target.")
            if target == current:
                raise ValueError("Already active.")
            if target < len(hp_list):
                try:
                    hp_val = int(hp_list[target])
                except (TypeError, ValueError):
                    hp_val = 0
                if hp_val <= 0:
                    raise ValueError("Cannot switch to a fainted Pokémon.")

            return {"type": "switch", "to": int(target)}

        if action_type != "attack":
            return {"type": action_type}

        attack_type = str(action.get("attack_type") or attacker.types[0]).lower()
        attacker_types = {t.lower() for t in attacker.types}
        if attack_type not in attacker_types:
            raise ValueError("Invalid attack_type for this Pokémon.")

        return {"type": "attack", "attack_type": attack_type}

    def _record_stats(self, battle, turns, outcome):
        damage = sum(entry.get("dmg", 0) for turn in turns for entry in turn.get("log", []))
        crits = sum(1 for turn in turns for entry in turn.get("log", []) if entry.get("crit"))
        win_user = battle.p1_id if outcome["winner"] == "a" else battle.p2_id
        lose_user = battle.p1_id if outcome["loser"] == "a" else battle.p2_id
        self.stats.record_battle_result(win_user, lose_user, damage, crits)


class BotAutoPlayUC:
    def __init__(self, repo: BattleRepoPort, users: UserPort, notifier: NotificationPort, stats: StatsPort):
        self.repo = repo
        self.users = users
        self.play_turn = PlayTurnUC(repo, notifier, stats)

    @staticmethod
    def _pick_attack_type(
        type_chart: dict[str, dict[str, float]], attacker_types: list[str], defender_types: list[str]
    ) -> str | None:
        types = [str(t).strip().lower() for t in (attacker_types or []) if str(t).strip()]
        if not types:
            return None
        best = types[0]
        best_mult = float("-inf")
        for t in types:
            mult = float(type_multiplier(type_chart, t, defender_types))
            if mult > best_mult:
                best_mult = mult
                best = t
        return best

    def execute(self, battle_id: int, max_actions: int = 2) -> int:
        bot_id = self.users.get_or_create_bot_user_id()
        performed = 0
        for _ in range(max(0, int(max_actions))):
            battle = self.repo.load_battle(battle_id)
            if battle.status != "active" or battle.state.get("finished"):
                break
            if bot_id not in (battle.p1_id, battle.p2_id):
                break

            bot_role = "a" if battle.p1_id == bot_id else "b"
            state = battle.state or {}
            next_actor = state.get("next_actor")
            if next_actor != bot_role:
                break

            team = battle.p1_team if bot_role == "a" else battle.p2_team
            opp_team = battle.p2_team if bot_role == "a" else battle.p1_team
            side = state.get(bot_role, {}) if isinstance(state, dict) else {}
            opp = "b" if bot_role == "a" else "a"
            opp_side = state.get(opp, {}) if isinstance(state, dict) else {}

            try:
                a_idx = int(side.get("active", 0)) if isinstance(side, dict) else 0
            except (TypeError, ValueError):
                a_idx = 0
            try:
                d_idx = int(opp_side.get("active", 0)) if isinstance(opp_side, dict) else 0
            except (TypeError, ValueError):
                d_idx = 0

            a_idx = max(0, min(a_idx, max(0, len(team) - 1)))
            d_idx = max(0, min(d_idx, max(0, len(opp_team) - 1)))

            attacker = team[a_idx] if team else (battle.p1_pokemon if bot_role == "a" else battle.p2_pokemon)
            defender = opp_team[d_idx] if opp_team else (battle.p2_pokemon if bot_role == "a" else battle.p1_pokemon)

            attack_type = self._pick_attack_type(battle.type_chart, attacker.types, defender.types)
            action = {"type": "attack", "attack_type": attack_type} if attack_type else {"type": "defend"}
            self.play_turn.execute(battle_id, bot_id, action)
            performed += 1

        return performed


class StatsUC:
    def __init__(self, stats: StatsPort):
        self.stats = stats

    def get(self, user_id: int) -> dict:
        return self.stats.get_user_stats(user_id)


class ExpireBattleUC:
    def __init__(self, repo: BattleRepoPort, notifier: NotificationPort):
        self.repo = repo
        self.notifier = notifier

    def expire_if_needed(self, battle) -> bool:
        if battle.status != "active" or battle.state.get("finished"):
            return False
        if battle.created_at is None:
            return False

        now = int(time.time())
        if now - int(battle.created_at) < BATTLE_TTL_SECONDS:
            return False

        state = dict(battle.state or {})
        state["finished"] = True
        state["draw"] = True
        state["winner"] = None
        state["loser"] = None
        state["finished_reason"] = "timeout"
        state["finished_at"] = now

        outcome = {"draw": True, "reason": "timeout"}
        turns = self.repo.list_events(battle.id)
        replay = {
            "battle_id": battle.id,
            "seed": battle.seed.value,
            "type_chart": battle.type_chart,
            "turns": turns,
            "outcome": outcome,
        }
        self.repo.finish(battle.id, {"state": state, "outcome": outcome, "replay": replay})

        self.notifier.send(battle.p1_id, "battle_ended", {"battle_id": battle.id, **outcome})
        self.notifier.send(battle.p2_id, "battle_ended", {"battle_id": battle.id, **outcome})
        return True

    def expire_for_user(self, user_id: int) -> int:
        expired = 0
        for row in self.repo.list_battles(user_id):
            if row.get("status") != "active":
                continue
            battle_id = row.get("id")
            if not isinstance(battle_id, int):
                continue
            try:
                battle = self.repo.load_battle(battle_id)
            except Exception:
                continue
            if self.expire_if_needed(battle):
                expired += 1
        return expired


class RegisterUserUC:
    def __init__(self, users: UserPort):
        self.users = users

    def execute(self, username: str, password: str) -> dict:
        username = str(username or "").strip()
        password = str(password or "")

        if not username:
            raise ValueError("Username is required.")
        if username.lower() == BOT_USERNAME.lower():
            raise ValueError("Username is reserved.")
        if not password:
            raise ValueError("Password is required.")
        if len(username) > 150:
            raise ValueError("Username is too long.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")

        user_id, stored_username = self.users.create_user(username=username, password=password)
        return {"id": user_id, "username": stored_username}
