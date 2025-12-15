from django.contrib.auth import get_user_model
from django.test import TestCase

from app.adapters.repositories import StatisticsRepository
from app.models import Battle, UserPokemon


class StatisticsRepositoryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.u1 = User.objects.create_user(username="u1", password="pass12345")
        self.u2 = User.objects.create_user(username="u2", password="pass12345")

        for pid in (1, 2, 3, 4):
            UserPokemon.objects.create(
                user=self.u1,
                pokemon_id=pid,
                name=f"p{pid}",
                stats={"hp": 10, "attack": 10, "defense": 10, "speed": 10},
                types=["normal"],
            )

    def test_top_pokemons_counts_whole_team_not_only_lead(self):
        Battle.objects.create(
            p1=self.u1,
            p2=self.u2,
            p1_pokemon_id=1,
            p2_pokemon_id=10,
            p1_team_ids=[1, 2, 3],
            p2_team_ids=[10, 11, 12],
            seed=1,
            status="finished",
            result={"outcome": {"winner": "a", "loser": "b"}},
        )
        Battle.objects.create(
            p1=self.u2,
            p2=self.u1,
            p1_pokemon_id=20,
            p2_pokemon_id=2,
            p1_team_ids=[20, 21, 22],
            p2_team_ids=[2, 3, 4],
            seed=2,
            status="finished",
            result={"outcome": {"winner": "a", "loser": "b"}},
        )

        stats = StatisticsRepository().get_user_stats(self.u1.id)
        top_ids = [row["pokemon_id"] for row in stats["top_pokemons"]]

        self.assertIn(2, top_ids)
        self.assertIn(3, top_ids)
        self.assertIn(1, top_ids)
