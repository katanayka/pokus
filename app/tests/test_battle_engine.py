from django.test import SimpleTestCase

from app.domain.entities import BattleContext, BattleSeed, Pokemon
from app.domain.services import BattleEngine
from app.application.use_cases import CatalogUC


class BattleEngineTests(SimpleTestCase):
    def test_damage_uses_type_chart_multiplier(self):
        engine = BattleEngine(0, {"fire": {"grass": 2.0}})
        dmg, mult = engine.damage(atk=50, defense=20, att_type="fire", def_types=["grass"], mod=1.0)
        self.assertEqual(mult, 2.0)
        self.assertGreater(dmg, 0)

    def test_step_is_deterministic_for_same_seed(self):
        p1 = Pokemon(
            id=4, name="charmander", types=["fire"], stats={"hp": 39, "attack": 52, "defense": 43, "speed": 65}
        )
        p2 = Pokemon(
            id=1, name="bulbasaur", types=["grass"], stats={"hp": 45, "attack": 49, "defense": 49, "speed": 45}
        )
        type_chart = {"fire": {"grass": 2.0}}
        battle = BattleContext(
            id=1,
            status="active",
            p1_id=10,
            p2_id=20,
            p1_team=[p1],
            p2_team=[p2],
            p1_pokemon=p1,
            p2_pokemon=p2,
            seed=BattleSeed(123),
            type_chart=type_chart,
            pending_actions={"a": None, "b": None},
            log=[],
            state={},
        )

        engine1 = BattleEngine(123, type_chart)
        log1, state1 = engine1.step(battle, "a", {"type": "attack", "attack_type": "fire"}, state={})
        engine2 = BattleEngine(123, type_chart)
        log2, state2 = engine2.step(battle, "a", {"type": "attack", "attack_type": "fire"}, state={})

        self.assertEqual(log1, log2)
        self.assertEqual(state1, state2)

    def test_switch_resets_effects(self):
        p1a = Pokemon(id=10, name="p1a", types=["normal"], stats={"hp": 30, "attack": 10, "defense": 10, "speed": 50})
        p1b = Pokemon(id=11, name="p1b", types=["normal"], stats={"hp": 30, "attack": 10, "defense": 10, "speed": 50})
        p2 = Pokemon(id=20, name="p2", types=["normal"], stats={"hp": 30, "attack": 10, "defense": 10, "speed": 50})

        battle = BattleContext(
            id=1,
            status="active",
            p1_id=10,
            p2_id=20,
            p1_team=[p1a, p1b],
            p2_team=[p2],
            p1_pokemon=p1a,
            p2_pokemon=p2,
            seed=BattleSeed(0),
            type_chart={},
            pending_actions={"a": None, "b": None},
            log=[],
            state={},
        )

        _log1, state1 = BattleEngine(0, {}).step(battle, "a", {"type": "buff"}, state={})
        self.assertGreater(float(state1["a"]["effects"]["atk_mod"]), 1.0)

        battle.state = state1
        _log2, state2 = BattleEngine(1, {}).step(battle, "a", {"type": "switch", "to": 1}, state=state1)
        self.assertEqual(int(state2["a"]["active"]), 1)
        self.assertEqual(float(state2["a"]["effects"]["atk_mod"]), 1.0)
        self.assertEqual(int(state2["a"]["effects"]["atk_turns"]), 0)
        self.assertEqual(int(state2["a"]["effects"]["defend"]), 0)

    def test_auto_switch_on_faint_continues_battle(self):
        p1 = Pokemon(id=1, name="p1", types=["normal"], stats={"hp": 50, "attack": 200, "defense": 1, "speed": 100})
        p2a = Pokemon(id=2, name="p2a", types=["normal"], stats={"hp": 10, "attack": 1, "defense": 1, "speed": 1})
        p2b = Pokemon(id=3, name="p2b", types=["normal"], stats={"hp": 10, "attack": 1, "defense": 1, "speed": 1})

        battle = BattleContext(
            id=1,
            status="active",
            p1_id=10,
            p2_id=20,
            p1_team=[p1],
            p2_team=[p2a, p2b],
            p1_pokemon=p1,
            p2_pokemon=p2a,
            seed=BattleSeed(0),
            type_chart={},
            pending_actions={"a": None, "b": None},
            log=[],
            state={},
        )

        log, state = BattleEngine(0, {}).step(battle, "a", {"type": "attack", "attack_type": "normal"}, state={})
        self.assertFalse(bool(state.get("finished")))
        self.assertEqual(int(state["b"]["hp"][0]), 0)
        self.assertEqual(int(state["b"]["active"]), 1)
        self.assertTrue(any(entry.get("actor") == "b" and entry.get("action") == "autoswitch" for entry in log))


class CatalogUCTests(SimpleTestCase):
    def test_catalog_seeds_from_pokeapi_when_empty(self):
        class FakeCatalog:
            def __init__(self):
                self.items = []

            def list_user_pokemon(self, _user_id):
                return list(self.items)

            def upsert_user_pokemon(self, _user_id, pokemon):
                self.items.append(pokemon)
                return pokemon

        class FakePokeApi:
            def list_pokemon_ids(self, limit=20, offset=0):
                return [1, 2][:limit]

            def fetch_pokemon(self, pokemon_id: int):
                return Pokemon(
                    id=pokemon_id,
                    name=f"p{pokemon_id}",
                    types=["normal"],
                    stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10},
                )

            def fetch_type_chart(self, _attack_type: str):
                return {}

        uc = CatalogUC(FakeCatalog(), FakePokeApi(), seed_limit=2)
        pokes = uc.list(user_id=123)
        self.assertEqual([p.id for p in pokes], [1, 2])
