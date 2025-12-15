from typing import Protocol

BOT_USERNAME = "__bot__"


class UserPort(Protocol):
    def create_user(self, username: str, password: str) -> tuple[int, str]: ...

    def get_or_create_bot_user_id(self) -> int: ...
