from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app.adapters.repositories import BattleRepository
from app.domain.entities import Pokemon
from app.models import Battle, UserPokemon
from app.application.use_cases import BATTLE_TTL_SECONDS


class LobbyAndBattleApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.u1 = User.objects.create_user(username="u1", password="pass12345")
        self.u2 = User.objects.create_user(username="u2", password="pass12345")

        self.c1 = APIClient()
        self.c2 = APIClient()
        t1 = self.c1.post("/auth/login", {"username": "u1", "password": "pass12345"}, format="json").json()
        t2 = self.c2.post("/auth/login", {"username": "u2", "password": "pass12345"}, format="json").json()
        self.c1.credentials(HTTP_AUTHORIZATION=f"Bearer {t1['access']}")
        self.c2.credentials(HTTP_AUTHORIZATION=f"Bearer {t2['access']}")

        for pid, spd in ((1, 100), (2, 10), (3, 10)):
            UserPokemon.objects.create(
                user=self.u1,
                pokemon_id=pid,
                name=f"u1p{pid}",
                stats={"hp": 30, "attack": 50, "defense": 10, "speed": spd},
                types=["normal"],
            )
        for pid, spd in ((4, 10), (5, 10), (6, 10)):
            UserPokemon.objects.create(
                user=self.u2,
                pokemon_id=pid,
                name=f"u2p{pid}",
                stats={"hp": 30, "attack": 10, "defense": 10, "speed": spd},
                types=["normal"],
            )

    @patch("app.adapters.notification_client.requests.post")
    @patch("app.adapters.pokeapi_client.PokeApiHttp.fetch_type_chart", return_value={})
    def test_fast_lobby_creates_battle_and_enforces_turn_order(self, _type_chart, _notify_post):
        team1 = [1, 2, 3]
        team2 = [4, 5, 6]

        self.assertEqual(
            self.c1.post("/catalog/team", {"pokemon_ids": team1}, format="json").status_code,
            200,
        )
        self.assertEqual(
            self.c2.post("/catalog/team", {"pokemon_ids": team2}, format="json").status_code,
            200,
        )

        r1 = self.c1.post("/lobby", {"pokemon_ids": team1}, format="json")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], "queued")

        r2 = self.c2.post("/lobby", {"pokemon_ids": team2}, format="json")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], "matched")
        battle_id = int(r2.json()["battle_id"])

        not_your_turn = self.c2.post(
            f"/battle/{battle_id}/turn", {"type": "attack", "attack_type": "normal"}, format="json"
        )
        self.assertEqual(not_your_turn.status_code, 409)

        a1 = self.c1.post(f"/battle/{battle_id}/turn", {"type": "attack", "attack_type": "normal"}, format="json")
        self.assertEqual(a1.status_code, 200)
        self.assertEqual(a1.json()["status"], "resolved")
        self.assertEqual(a1.json()["turn"]["actor"], "a")

        a_twice = self.c1.post(f"/battle/{battle_id}/turn", {"type": "attack", "attack_type": "normal"}, format="json")
        self.assertEqual(a_twice.status_code, 409)

        b1 = self.c2.post(f"/battle/{battle_id}/turn", {"type": "attack", "attack_type": "normal"}, format="json")
        self.assertEqual(b1.status_code, 200)
        self.assertEqual(b1.json()["status"], "resolved")
        self.assertEqual(b1.json()["turn"]["actor"], "b")

    @patch("app.adapters.notification_client.requests.post")
    @patch("app.adapters.pokeapi_client.PokeApiHttp.fetch_type_chart", return_value={})
    def test_code_lobby_join_or_create_and_match(self, _type_chart, _notify_post):
        team1 = [1, 2, 3]
        team2 = [4, 5, 6]

        self.c1.post("/catalog/team", {"pokemon_ids": team1}, format="json")
        self.c2.post("/catalog/team", {"pokemon_ids": team2}, format="json")

        open_resp = self.c1.post("/lobby/code", {"code": "7", "pokemon_ids": team1}, format="json")
        self.assertEqual(open_resp.status_code, 200)
        self.assertEqual(open_resp.json(), {"status": "open", "code": "0007"})

        match_resp = self.c2.post("/lobby/code", {"code": "0007", "pokemon_ids": team2}, format="json")
        self.assertEqual(match_resp.status_code, 200)
        self.assertEqual(match_resp.json()["status"], "matched")
        self.assertEqual(int(match_resp.json()["opponent_id"]), self.u1.id)

    @patch("app.adapters.notification_client.requests.post")
    def test_battle_expires_after_ttl(self, _notify_post):
        repo = BattleRepository()
        p1_team = [
            Pokemon(id=1, name="p1a", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
        ]
        p2_team = [
            Pokemon(id=4, name="p2a", types=["normal"], stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10}),
        ]
        battle_id = repo.create_battle(
            p1=self.u1.id,
            p2=self.u2.id,
            p1_team=p1_team,
            p2_team=p2_team,
            seed=123,
            type_chart={},
            order=["a", "b"],
            initiative={"seed": 123, "winner": "a", "method": "speed", "a_speed": 10, "b_speed": 10},
        )
        Battle.objects.filter(id=battle_id).update(
            created_at=timezone.now() - timedelta(seconds=BATTLE_TTL_SECONDS + 5)
        )

        self.c1.force_authenticate(self.u1)
        resp = self.c1.post(f"/battle/{battle_id}/turn", {"type": "defend"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "finished")
        self.assertTrue(resp.json()["outcome"]["draw"])
        self.assertEqual(resp.json()["outcome"]["reason"], "timeout")
