from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from app.adapters.pokeapi_client import PokeApiHttp
from app.models import UserPokemon


class CatalogApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="ash", password="pikachu123")
        self.client = APIClient()
        login = self.client.post("/auth/login", {"username": "ash", "password": "pikachu123"}, format="json").json()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access']}")

        UserPokemon.objects.create(
            user=self.user,
            pokemon_id=1,
            name="bulbasaur",
            stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10},
            types=["grass"],
        )
        UserPokemon.objects.create(
            user=self.user,
            pokemon_id=2,
            name="ivysaur",
            stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10},
            types=["grass"],
        )

    def test_catalog_offset_nan_is_handled(self):
        with patch.object(PokeApiHttp, "list_pokemon_ids", autospec=True, return_value=[1, 2]):
            resp = self.client.get("/catalog?limit=20&offset=NaN")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertEqual([p["id"] for p in items], [1, 2])

    def test_catalog_limit_is_clamped(self):
        called = {}

        def fake_list(_self, limit=20, offset=0):
            called["limit"] = limit
            called["offset"] = offset
            return [1]

        with patch.object(PokeApiHttp, "list_pokemon_ids", autospec=True, side_effect=fake_list):
            resp = self.client.get("/catalog?limit=999&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(called["limit"], 50)

    def test_catalog_search_returns_matches(self):
        with patch.object(PokeApiHttp, "search_pokemon_ids", autospec=True, return_value=[1, 2]):
            resp = self.client.get("/catalog/search?q=saur&limit=20&offset=0")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertEqual([p["id"] for p in items], [1, 2])
