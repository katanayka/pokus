from django.test import SimpleTestCase

from app.application.use_cases import CodeLobbyUC, PlayTurnUC, RegisterUserUC, SearchPokemonUC, SetTeamUC, BotAutoPlayUC
from app.domain.entities import BattleContext, BattleSeed, Pokemon


class _FakeCatalog:
    def __init__(self):
        self.items: dict[int, Pokemon] = {}
        self.active: int | None = None
        self.active_team: list[int] = []

    def list_user_pokemon(self, _user_id: int):
        return list(self.items.values())

    def get_user_pokemon(self, _user_id: int, pokemon_id: int):
        return self.items.get(int(pokemon_id))

    def upsert_user_pokemon(self, _user_id: int, pokemon: Pokemon):
        self.items[int(pokemon.id)] = pokemon
        return pokemon

    def set_active(self, _user_id: int, pokemon_id: int) -> None:
        self.active = int(pokemon_id)

    def get_active(self, _user_id: int):
        return self.items.get(int(self.active or 0))

    def set_active_team(self, _user_id: int, pokemon_ids: list[int]) -> None:
        self.active_team = [int(x) for x in pokemon_ids]

    def get_active_team_ids(self, _user_id: int):
        return list(self.active_team)


class _FakePokeApi:
    def fetch_pokemon(self, pokemon_id: int) -> Pokemon:
        pid = int(pokemon_id)
        return Pokemon(
            id=pid, name=f"p{pid}", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}
        )

    def list_pokemon_ids(self, limit: int = 20, offset: int = 0) -> list[int]:
        return list(range(int(offset) + 1, int(offset) + 1 + int(limit)))

    def search_pokemon_ids(self, query: str, limit: int = 20, offset: int = 0) -> list[int]:
        if query == "saur":
            return [1, 2, 3][int(offset) : int(offset) + int(limit)]
        return []

    def fetch_type_chart(self, _attack_type: str) -> dict[str, float]:
        return {}


class _FakeUsers:
    def __init__(self):
        self.created: list[tuple[str, str]] = []
        self.next_id = 1

    def create_user(self, username: str, password: str) -> tuple[int, str]:
        self.created.append((username, password))
        uid = self.next_id
        self.next_id += 1
        return uid, username


class UseCaseUnitTests(SimpleTestCase):
    def test_set_team_sets_active_team_and_active_pokemon(self):
        catalog = _FakeCatalog()
        uc = SetTeamUC(catalog, _FakePokeApi())
        team = uc.execute(user_id=1, pokemon_ids=[1, 2, 3])
        self.assertEqual([p.id for p in team], [1, 2, 3])
        self.assertEqual(catalog.get_active_team_ids(1), [1, 2, 3])
        self.assertEqual(catalog.active, 1)

    def test_set_team_validates_team_size_and_uniqueness(self):
        catalog = _FakeCatalog()
        uc = SetTeamUC(catalog, _FakePokeApi())
        with self.assertRaises(ValueError):
            uc.execute(user_id=1, pokemon_ids=[1, 2])
        with self.assertRaises(ValueError):
            uc.execute(user_id=1, pokemon_ids=[1, 1, 2])

    def test_search_numeric_query_fetches_single_pokemon(self):
        catalog = _FakeCatalog()
        uc = SearchPokemonUC(catalog, _FakePokeApi())
        results = uc.execute(user_id=1, query="25")
        self.assertEqual([p.id for p in results], [25])

    def test_code_lobby_normalizes_code(self):
        self.assertEqual(CodeLobbyUC._normalize_code("7"), "0007")
        self.assertEqual(CodeLobbyUC._normalize_code(7), "0007")
        with self.assertRaises(ValueError):
            CodeLobbyUC._normalize_code("abcd")

    def test_register_user_validates_and_calls_repo(self):
        users = _FakeUsers()
        uc = RegisterUserUC(users)
        data = uc.execute(username="ash", password="pikachu123")
        self.assertEqual(data["username"], "ash")
        self.assertEqual(users.created[0][0], "ash")

    def test_bot_attack_type_picks_best_multiplier(self):
        chart = {"fire": {"grass": 2.0}, "normal": {"grass": 1.0}}
        best = BotAutoPlayUC._pick_attack_type(chart, ["normal", "fire"], ["grass"])
        self.assertEqual(best, "fire")

    def test_play_turn_normalize_action_rejects_invalid_attack_type(self):
        p = Pokemon(id=1, name="p", types=["fire"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10})
        battle = BattleContext(
            id=1,
            status="active",
            p1_id=1,
            p2_id=2,
            p1_team=[p],
            p2_team=[p],
            p1_pokemon=p,
            p2_pokemon=p,
            seed=BattleSeed(1),
            type_chart={},
            pending_actions={"a": None, "b": None},
            log=[],
            state={},
        )
        uc = PlayTurnUC(repo=None, notifier=None, stats=None)
        with self.assertRaises(ValueError):
            uc._normalize_action(battle, "a", {"type": "attack", "attack_type": "water"}, p)
