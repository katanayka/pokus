from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class JwtAuthTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="ash", password="pikachu123")
        self.client = APIClient()

    def test_login_returns_access_and_refresh(self):
        resp = self.client.post("/auth/login", {"username": "ash", "password": "pikachu123"}, format="json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_refresh_rotates_access_token(self):
        login = self.client.post("/auth/login", {"username": "ash", "password": "pikachu123"}, format="json").json()
        resp = self.client.post("/auth/refresh", {"refresh": login["refresh"]}, format="json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access", data)

    def test_protected_endpoint_requires_auth(self):
        resp = self.client.get("/catalog")
        self.assertEqual(resp.status_code, 401)
