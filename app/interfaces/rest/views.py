import requests
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from app.adapters.notification_client import NotificationHttp
from app.adapters.pokeapi_client import PokeApiHttp
from app.adapters.repositories import (
    BattleRepository,
    CatalogRepository,
    LobbyRepository,
    StatisticsRepository,
    UserRepository,
)
from app.application.use_cases import (
    CloseCodeLobbyUC,
    CodeLobbyUC,
    BotAutoPlayUC,
    CatalogUC,
    EnterLobbyUC,
    ExpireBattleUC,
    GetPokemonUC,
    GetTeamUC,
    PlayTurnUC,
    RegisterUserUC,
    SearchPokemonUC,
    SelectPokemonUC,
    StartPveBattleUC,
    SetTeamUC,
    StatsUC,
)


def _int_query_param(
    request, name: str, default: int, *, min_value: int | None = None, max_value: int | None = None
) -> int:
    raw = request.query_params.get(name, None)
    if raw is None or raw == "":
        value = default
    else:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = default

    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def catalog(request):
    limit = _int_query_param(request, "limit", 20, min_value=1, max_value=50)
    offset = _int_query_param(request, "offset", 0, min_value=0)

    uc = CatalogUC(CatalogRepository(), PokeApiHttp())
    pokes = uc.page(request.user.id, limit=limit, offset=offset)
    return Response([{"id": p.id, "name": p.name, "types": p.types, "stats": p.stats} for p in pokes])


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("username")
    password = request.data.get("password")
    uc = RegisterUserUC(UserRepository())
    try:
        data = uc.execute(username=username, password=password)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    return Response(data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def battle_pve(request):
    pokemon_ids = request.data.get("pokemon_ids", None)
    if pokemon_ids is not None and not isinstance(pokemon_ids, list):
        return Response({"error": "pokemon_ids must be a list."}, status=400)

    uc = StartPveBattleUC(CatalogRepository(), BattleRepository(), NotificationHttp(), PokeApiHttp(), UserRepository())
    try:
        result = uc.execute(request.user.id, pokemon_ids)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except requests.RequestException:
        return Response({"error": "PokeAPI unavailable."}, status=502)
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def catalog_search(request):
    q = str(request.query_params.get("q") or "").strip()
    if not q:
        return Response({"error": "Query parameter 'q' is required."}, status=400)

    limit = _int_query_param(request, "limit", 20, min_value=1, max_value=50)
    offset = _int_query_param(request, "offset", 0, min_value=0)

    uc = SearchPokemonUC(CatalogRepository(), PokeApiHttp())
    try:
        pokes = uc.execute(request.user.id, q, limit=limit, offset=offset)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except requests.RequestException:
        return Response({"error": "PokeAPI unavailable."}, status=502)
    return Response([{"id": p.id, "name": p.name, "types": p.types, "stats": p.stats} for p in pokes])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pokemon_detail(request, pokemon_id: int):
    uc = GetPokemonUC(CatalogRepository(), PokeApiHttp())
    p = uc.execute(request.user.id, pokemon_id)
    return Response({"id": p.id, "name": p.name, "types": p.types, "stats": p.stats})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def select_pokemon(request):
    pokemon_id = int(request.data["pokemon_id"])
    uc = SelectPokemonUC(CatalogRepository(), PokeApiHttp())
    uc.execute(request.user.id, pokemon_id)
    return Response({"status": "selected", "active_pokemon_id": pokemon_id, "redirect": "lobby"})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def team(request):
    catalog = CatalogRepository()
    pokeapi = PokeApiHttp()

    if request.method == "POST":
        pokemon_ids = request.data.get("pokemon_ids")
        if not isinstance(pokemon_ids, list):
            return Response({"error": "pokemon_ids must be a list of 3 integers."}, status=400)
        uc = SetTeamUC(catalog, pokeapi)
        try:
            team_pokemons = uc.execute(request.user.id, pokemon_ids)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response({"status": "selected", "pokemon_ids": [p.id for p in team_pokemons]})

    uc = GetTeamUC(catalog, pokeapi)
    team_pokemons = uc.execute(request.user.id)
    return Response([{"id": p.id, "name": p.name, "types": p.types, "stats": p.stats} for p in team_pokemons])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enter_lobby(request):
    pokemon_ids = request.data.get("pokemon_ids", None)
    if pokemon_ids is not None and not isinstance(pokemon_ids, list):
        return Response({"error": "pokemon_ids must be a list."}, status=400)
    uc = EnterLobbyUC(CatalogRepository(), LobbyRepository(), BattleRepository(), NotificationHttp(), PokeApiHttp())
    try:
        result = uc.execute(request.user.id, pokemon_ids)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def code_lobby(request):
    code = request.data.get("code")
    pokemon_ids = request.data.get("pokemon_ids", None)
    if pokemon_ids is not None and not isinstance(pokemon_ids, list):
        return Response({"error": "pokemon_ids must be a list."}, status=400)

    uc = CodeLobbyUC(CatalogRepository(), LobbyRepository(), BattleRepository(), NotificationHttp(), PokeApiHttp())
    try:
        result = uc.execute(request.user.id, code=code, pokemon_ids=pokemon_ids)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except requests.RequestException:
        return Response({"error": "PokeAPI unavailable."}, status=502)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def close_code_lobby(request):
    code = request.data.get("code")
    uc = CloseCodeLobbyUC(LobbyRepository())
    try:
        result = uc.execute(request.user.id, code=code)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_battle(request):
    pokemon_ids = request.data.get("pokemon_ids", None)
    if pokemon_ids is not None and not isinstance(pokemon_ids, list):
        return Response({"error": "pokemon_ids must be a list."}, status=400)
    uc = EnterLobbyUC(CatalogRepository(), LobbyRepository(), BattleRepository(), NotificationHttp(), PokeApiHttp())
    try:
        result = uc.execute(request.user.id, pokemon_ids)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def play_turn(request, battle_id: int):
    action = request.data
    uc = PlayTurnUC(BattleRepository(), NotificationHttp(), StatisticsRepository())
    try:
        result = uc.execute(battle_id, request.user.id, action)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)
    except ValueError as exc:
        msg = str(exc)
        if msg == "Battle not found.":
            return Response({"error": msg}, status=404)
        if msg == "Not your turn.":
            return Response({"error": msg}, status=409)
        return Response({"error": msg}, status=400)
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history(request):
    repo = BattleRepository()
    ExpireBattleUC(repo, NotificationHttp()).expire_for_user(request.user.id)
    rows = repo.list_battles(request.user.id)
    return Response(rows)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def replay(request, battle_id: int):
    repo = BattleRepository()
    try:
        battle = repo.load_battle(battle_id)
    except Exception:
        return Response({"error": "Battle not found."}, status=404)
    if request.user.id not in (battle.p1_id, battle.p2_id):
        return Response({"error": "Battle not found."}, status=404)

    role = "a" if request.user.id == battle.p1_id else "b"
    opponent_id = battle.p2_id if role == "a" else battle.p1_id
    opponent_username = None
    try:
        opponent_username = str(get_user_model().objects.only("username").get(id=opponent_id).username)
    except Exception:
        opponent_username = None

    ExpireBattleUC(repo, NotificationHttp()).expire_if_needed(battle)

    try:
        replay_data = repo.get_replay(battle_id)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=409)
    if replay_data:
        replay_data["finished"] = True
        replay_data["role"] = role
        replay_data["opponent_id"] = opponent_id
        replay_data["opponent_username"] = opponent_username
        replay_data["p1_pokemon_id"] = battle.p1_pokemon.id
        replay_data["p2_pokemon_id"] = battle.p2_pokemon.id
        replay_data["p1_team_ids"] = [p.id for p in battle.p1_team]
        replay_data["p2_team_ids"] = [p.id for p in battle.p2_team]
        return Response(replay_data)
    return Response(
        {
            "battle_id": battle_id,
            "seed": battle.seed.value,
            "type_chart": battle.type_chart,
            "turns": repo.list_events(battle_id),
            "finished": False,
            "role": role,
            "opponent_id": opponent_id,
            "opponent_username": opponent_username,
            "p1_pokemon_id": battle.p1_pokemon.id,
            "p2_pokemon_id": battle.p2_pokemon.id,
            "p1_team_ids": [p.id for p in battle.p1_team],
            "p2_team_ids": [p.id for p in battle.p2_team],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def battle_detail(request, battle_id: int):
    repo = BattleRepository()
    try:
        battle = repo.load_battle(battle_id)
    except Exception:
        return Response({"error": "Battle not found."}, status=404)
    if request.user.id not in (battle.p1_id, battle.p2_id):
        return Response({"error": "Battle not found."}, status=404)

    ExpireBattleUC(repo, NotificationHttp()).expire_if_needed(battle)

    try:
        BotAutoPlayUC(repo, UserRepository(), NotificationHttp(), StatisticsRepository()).execute(battle_id)
    except Exception:
        pass

    item = repo.get_battle_item(request.user.id, battle_id)
    if not item:
        return Response({"error": "Battle not found."}, status=404)
    return Response(item)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats(request):
    ExpireBattleUC(BattleRepository(), NotificationHttp()).expire_for_user(request.user.id)
    uc = StatsUC(StatisticsRepository())
    return Response(uc.get(request.user.id))
