from django.test import SimpleTestCase

from app.domain.entities import BattleContext, BattleSeed, Pokemon
from app.domain.services import BattleEngine, type_multiplier


class BattleEngineMechanicsTests(SimpleTestCase):
    def test_type_multiplier_multiplies_for_dual_types(self):
        chart = {"fire": {"grass": 2.0, "poison": 1.0}}
        self.assertEqual(type_multiplier(chart, "fire", ["grass", "poison"]), 2.0)

    def test_initiative_tiebreak_is_deterministic_for_seed(self):
        e1 = BattleEngine(123, {})
        e2 = BattleEngine(123, {})
        w1, d1 = e1.initiative_detail(10, 10)
        w2, d2 = e2.initiative_detail(10, 10)
        self.assertEqual(w1, w2)
        self.assertEqual(d1, d2)
        self.assertEqual(d1["method"], "tiebreak")

    def test_defend_halves_damage_and_counts_down(self):
        p1 = Pokemon(id=1, name="a", types=["normal"], stats={"hp": 50, "attack": 50, "defense": 10, "speed": 10})
        p2 = Pokemon(id=2, name="b", types=["normal"], stats={"hp": 50, "attack": 10, "defense": 10, "speed": 10})
        battle = BattleContext(
            id=1,
            status="active",
            p1_id=1,
            p2_id=2,
            p1_team=[p1],
            p2_team=[p2],
            p1_pokemon=p1,
            p2_pokemon=p2,
            seed=BattleSeed(0),
            type_chart={},
            pending_actions={"a": None, "b": None},
            log=[],
            state={},
        )

        _log_def, state_def = BattleEngine(0, {}).step(battle, "b", {"type": "defend"}, state={})
        self.assertEqual(int(state_def["b"]["effects"]["defend"]), 2)

        log_hit, state_after = BattleEngine(0, {}).step(
            battle, "a", {"type": "attack", "attack_type": "normal"}, state=state_def
        )
        self.assertTrue(any(e.get("action") == "hit" for e in log_hit))
        hit = next(e for e in log_hit if e.get("action") == "hit")
        self.assertEqual(int(hit["defend_before"]), 2)
        self.assertEqual(int(state_after["b"]["effects"]["defend"]), 1)

        log_no_def, _ = BattleEngine(0, {}).step(battle, "a", {"type": "attack", "attack_type": "normal"}, state={})
        hit2 = next(e for e in log_no_def if e.get("action") == "hit")
        self.assertEqual(int(hit["dmg"]), int(hit2["dmg"]) // 2)

    def test_buff_decays_and_resets(self):
        p1 = Pokemon(id=1, name="a", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10})
        p2 = Pokemon(id=2, name="b", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10})
        battle = BattleContext(
            id=1,
            status="active",
            p1_id=1,
            p2_id=2,
            p1_team=[p1],
            p2_team=[p2],
            p1_pokemon=p1,
            p2_pokemon=p2,
            seed=BattleSeed(0),
            type_chart={},
            pending_actions={"a": None, "b": None},
            log=[],
            state={},
        )

        _log, state = BattleEngine(0, {}).step(battle, "a", {"type": "buff"}, state={})
        self.assertGreater(float(state["a"]["effects"]["atk_mod"]), 1.0)
        self.assertEqual(int(state["a"]["effects"]["atk_turns"]), 2)

        BattleEngine.decay_effects(state)
        self.assertEqual(int(state["a"]["effects"]["atk_turns"]), 1)

        BattleEngine.decay_effects(state)
        self.assertEqual(int(state["a"]["effects"]["atk_turns"]), 0)
        self.assertEqual(float(state["a"]["effects"]["atk_mod"]), 1.0)
