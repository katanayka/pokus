import requests
from django.core.cache import cache

from app.domain.entities import Pokemon
from app.ports.pokeapi import PokeApiPort


class PokeApiHttp(PokeApiPort):
    _INDEX_CACHE_KEY = "poke:index:v1"
    _INDEX_TTL_SECONDS = 24 * 3600

    def _all_pokemon_index(self) -> list[tuple[int, str]]:
        cached = cache.get(self._INDEX_CACHE_KEY)
        if cached is not None:
            return cached

        resp = requests.get("https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        index: list[tuple[int, str]] = []
        for item in data.get("results", []):
            name = str(item.get("name") or "").strip().lower()
            url = str(item.get("url") or "")
            if not name or not url:
                continue
            try:
                pokemon_id = int(url.rstrip("/").split("/")[-1])
            except ValueError:
                continue
            index.append((pokemon_id, name))

        index.sort(key=lambda it: it[0])
        cache.set(self._INDEX_CACHE_KEY, index, timeout=self._INDEX_TTL_SECONDS)
        return index

    def search_pokemon_ids(self, query: str, limit: int = 20, offset: int = 0) -> list[int]:
        query = str(query or "").strip().lower()
        if not query:
            raise ValueError("Search query is required.")

        limit = max(1, min(int(limit), 50))
        offset = max(0, int(offset))

        index = self._all_pokemon_index()
        matches = [pokemon_id for pokemon_id, name in index if query in name]
        return matches[offset : offset + limit]

    def fetch_pokemon_by_name(self, name: str) -> Pokemon:
        name = str(name or "").strip().lower()
        if not name:
            raise ValueError("Pokemon name is required.")

        cached = cache.get(f"poke:name:{name}")
        if cached is not None:
            return cached

        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        types = [t["type"]["name"] for t in data["types"]]
        pokemon = Pokemon(
            id=data["id"],
            name=data["name"],
            types=types,
            stats={"hp": stats["hp"], "attack": stats["attack"], "defense": stats["defense"], "speed": stats["speed"]},
        )
        cache.set(f"poke:{pokemon.id}", pokemon, timeout=3600)
        cache.set(f"poke:name:{name}", pokemon, timeout=3600)
        return pokemon

    def list_pokemon_ids(self, limit: int = 20, offset: int = 0) -> list[int]:
        limit = max(1, min(int(limit), 50))
        offset = max(0, int(offset))

        cache_key = f"pokelist:{limit}:{offset}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon?limit={limit}&offset={offset}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        ids: list[int] = []
        for item in data.get("results", []):
            url = str(item.get("url") or "")
            if not url:
                continue
            try:
                pokemon_id = int(url.rstrip("/").split("/")[-1])
            except ValueError:
                continue
            ids.append(pokemon_id)

        cache.set(cache_key, ids, timeout=10 * 60)
        return ids

    def fetch_pokemon(self, pokemon_id: int) -> Pokemon:
        cached = cache.get(f"poke:{pokemon_id}")
        if cached is not None:
            return cached
        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        types = [t["type"]["name"] for t in data["types"]]
        pokemon = Pokemon(
            id=data["id"],
            name=data["name"],
            types=types,
            stats={"hp": stats["hp"], "attack": stats["attack"], "defense": stats["defense"], "speed": stats["speed"]},
        )
        cache.set(f"poke:{pokemon_id}", pokemon, timeout=3600)
        return pokemon

    def fetch_type_chart(self, attack_type: str) -> dict[str, float]:
        attack_type = attack_type.lower()
        cached = cache.get(f"typechart:{attack_type}")
        if cached is not None:
            return cached

        resp = requests.get(f"https://pokeapi.co/api/v2/type/{attack_type}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        rel = data.get("damage_relations", {})

        chart: dict[str, float] = {}
        for entry in rel.get("double_damage_to", []):
            chart[entry["name"]] = 2.0
        for entry in rel.get("half_damage_to", []):
            chart[entry["name"]] = 0.5
        for entry in rel.get("no_damage_to", []):
            chart[entry["name"]] = 0.0

        cache.set(f"typechart:{attack_type}", chart, timeout=24 * 3600)
        return chart
