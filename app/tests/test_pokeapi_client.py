from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from app.adapters.pokeapi_client import PokeApiHttp


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class PokeApiHttpTests(SimpleTestCase):
    def _resp(self, payload: dict):
        resp = Mock()
        resp.raise_for_status = Mock()
        resp.json = Mock(return_value=payload)
        return resp

    @patch("app.adapters.pokeapi_client.requests.get")
    def test_search_pokemon_ids_matches_substring_and_uses_cached_index(self, get: Mock):
        get.return_value = self._resp(
            {
                "results": [
                    {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
                    {"name": "ivysaur", "url": "https://pokeapi.co/api/v2/pokemon/2/"},
                    {"name": "venusaur", "url": "https://pokeapi.co/api/v2/pokemon/3/"},
                    {"name": "charmander", "url": "https://pokeapi.co/api/v2/pokemon/4/"},
                ]
            }
        )

        api = PokeApiHttp()
        self.assertEqual(api.search_pokemon_ids("saur", limit=50, offset=0), [1, 2, 3])
        self.assertEqual(api.search_pokemon_ids("saur", limit=50, offset=1), [2, 3])
        self.assertEqual(get.call_count, 1)

    @patch("app.adapters.pokeapi_client.requests.get")
    def test_list_pokemon_ids_parses_urls(self, get: Mock):
        get.return_value = self._resp(
            {
                "results": [
                    {"url": "https://pokeapi.co/api/v2/pokemon/25/"},
                    {"url": "https://pokeapi.co/api/v2/pokemon/26/"},
                ]
            }
        )
        api = PokeApiHttp()
        self.assertEqual(api.list_pokemon_ids(limit=20, offset=0), [25, 26])

    @patch("app.adapters.pokeapi_client.requests.get")
    def test_fetch_pokemon_by_name_parses_stats_types_and_caches(self, get: Mock):
        get.return_value = self._resp(
            {
                "id": 25,
                "name": "pikachu",
                "stats": [
                    {"base_stat": 35, "stat": {"name": "hp"}},
                    {"base_stat": 55, "stat": {"name": "attack"}},
                    {"base_stat": 40, "stat": {"name": "defense"}},
                    {"base_stat": 90, "stat": {"name": "speed"}},
                ],
                "types": [{"type": {"name": "electric"}}],
            }
        )
        api = PokeApiHttp()
        p = api.fetch_pokemon_by_name("pikachu")
        self.assertEqual(p.id, 25)
        self.assertEqual(p.name, "pikachu")
        self.assertEqual(p.types, ["electric"])
        self.assertEqual(p.stats["hp"], 35)
        self.assertEqual(api.fetch_pokemon_by_name("pikachu").id, 25)
        self.assertEqual(get.call_count, 1)

    @patch("app.adapters.pokeapi_client.requests.get")
    def test_fetch_type_chart_parses_damage_relations(self, get: Mock):
        get.return_value = self._resp(
            {
                "damage_relations": {
                    "double_damage_to": [{"name": "grass"}],
                    "half_damage_to": [{"name": "fire"}],
                    "no_damage_to": [{"name": "ghost"}],
                }
            }
        )
        api = PokeApiHttp()
        chart = api.fetch_type_chart("normal")
        self.assertEqual(chart["grass"], 2.0)
        self.assertEqual(chart["fire"], 0.5)
        self.assertEqual(chart["ghost"], 0.0)
