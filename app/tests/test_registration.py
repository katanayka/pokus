from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from app.ports.users import BOT_USERNAME


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        resp = self.client.post("/auth/register", {"username": "ash", "password": "pikachu123"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(username="ash").exists())

    def test_register_rejects_duplicate_username(self):
        get_user_model().objects.create_user(username="misty", password="starmie123")
        resp = self.client.post("/auth/register", {"username": "misty", "password": "another123"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_register_requires_password(self):
        resp = self.client.post("/auth/register", {"username": "brock"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_register_rejects_reserved_bot_username(self):
        resp = self.client.post("/auth/register", {"username": BOT_USERNAME, "password": "password123"}, format="json")
        self.assertEqual(resp.status_code, 400)
