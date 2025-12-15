from typing import Protocol


class NotificationPort(Protocol):
    def send(self, user_id: int, event: str, payload: dict) -> None: ...
