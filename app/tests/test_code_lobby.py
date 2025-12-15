from django.contrib.auth import get_user_model
from django.test import TestCase

from app.adapters.repositories import LobbyRepository


class CodeLobbyRepositoryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.u1 = User.objects.create_user(username="u1", password="pass12345")
        self.u2 = User.objects.create_user(username="u2", password="pass12345")
        self.repo = LobbyRepository()

    def test_fast_match_ignores_code_lobbies(self):
        self.repo.open_code_lobby(self.u2.id, [1, 2, 3], "1234")
        self.assertIsNone(self.repo.try_match(self.u1.id))

    def test_code_lobby_matches_by_code(self):
        self.repo.open_code_lobby(self.u2.id, [10, 11, 12], "4321")
        match = self.repo.try_match_code_lobby(self.u1.id, "4321")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.user_id, self.u2.id)
        self.assertEqual(match.pokemon_ids, [10, 11, 12])

    def test_code_lobby_unique_code(self):
        self.repo.open_code_lobby(self.u2.id, [1, 2, 3], "9999")
        with self.assertRaises(ValueError):
            self.repo.open_code_lobby(self.u1.id, [4, 5, 6], "9999")

    def test_close_code_lobby_deletes_entry(self):
        self.repo.open_code_lobby(self.u1.id, [1, 2, 3], "0007")
        self.assertTrue(self.repo.close_code_lobby(self.u1.id, "0007"))
        self.assertFalse(self.repo.close_code_lobby(self.u1.id, "0007"))
