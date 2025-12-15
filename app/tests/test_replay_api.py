from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from app.adapters.repositories import BattleRepository
from app.domain.entities import Pokemon
from app.models import Battle


class ReplayApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.u1 = User.objects.create_user(username="u1", password="pass12345")
        self.u2 = User.objects.create_user(username="u2", password="pass12345")
        self.client = APIClient()
        self.repo = BattleRepository()

    def _create_finished_battle(self) -> int:
        p1_team = [
            Pokemon(id=1, name="p1a", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
            Pokemon(id=2, name="p1b", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
            Pokemon(id=3, name="p1c", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
        ]
        p2_team = [
            Pokemon(id=4, name="p2a", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
            Pokemon(id=5, name="p2b", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
            Pokemon(id=6, name="p2c", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
        ]
        battle_id = self.repo.create_battle(
            p1=self.u1.id,
            p2=self.u2.id,
            p1_team=p1_team,
            p2_team=p2_team,
            seed=123,
            type_chart={},
            order=["a", "b"],
            initiative={"seed": 123, "winner": "a", "method": "speed", "a_speed": 10, "b_speed": 10},
        )
        replay = {
            "battle_id": battle_id,
            "seed": 123,
            "type_chart": {},
            "turns": [],
            "outcome": {"draw": True, "reason": "test"},
        }
        self.repo.finish(
            battle_id, {"state": {"finished": True, "draw": True}, "outcome": replay["outcome"], "replay": replay}
        )
        return battle_id

    def test_replay_includes_team_ids_and_signature(self):
        battle_id = self._create_finished_battle()
        self.client.force_authenticate(self.u1)
        resp = self.client.get(f"/battles/{battle_id}/replay")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["finished"])
        self.assertEqual(data["p1_team_ids"], [1, 2, 3])
        self.assertEqual(data["p2_team_ids"], [4, 5, 6])
        self.assertIn("signature", data)

    def test_replay_integrity_check_rejects_tampering(self):
        battle_id = self._create_finished_battle()
        b = Battle.objects.get(id=battle_id)
        b.result["replay"]["seed"] = 999  # tamper replay without updating sig
        b.save(update_fields=["result"])

        self.client.force_authenticate(self.u1)
        resp = self.client.get(f"/battles/{battle_id}/replay")
        self.assertEqual(resp.status_code, 409)
        self.assertIn("Replay integrity check failed", resp.json().get("error", ""))
