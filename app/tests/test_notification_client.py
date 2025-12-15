from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from app.adapters.notification_client import NotificationHttp


class NotificationHttpTests(SimpleTestCase):
    @override_settings(NOTIFICATION_SERVICE_URL="http://notify.test", NOTIFICATION_SERVICE_TOKEN="secret")
    @patch("app.adapters.notification_client.requests.post")
    def test_send_posts_with_bearer_token(self, post: Mock):
        client = NotificationHttp()
        client.send(10, "battle_started", {"battle_id": 123})

        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://notify.test/notify")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(kwargs["json"]["user_id"], 10)
        self.assertEqual(kwargs["json"]["event"], "battle_started")

    @patch("app.adapters.notification_client.requests.post", side_effect=Exception("boom"))
    def test_send_swallows_errors(self, _post: Mock):
        client = NotificationHttp(base_url="http://notify.test", token="secret")
        client.send(10, "battle_started", {"battle_id": 1})
