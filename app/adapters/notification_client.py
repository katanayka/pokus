import requests
from django.conf import settings

from app.ports.notification import NotificationPort


class NotificationHttp(NotificationPort):
    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = base_url or settings.NOTIFICATION_SERVICE_URL
        self.token = token or settings.NOTIFICATION_SERVICE_TOKEN

    def send(self, user_id: int, event: str, payload: dict) -> None:
        try:
            requests.post(
                f"{self.base_url}/notify",
                json={"user_id": user_id, "event": event, "payload": payload},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=3,
            )
        except Exception:
            return
