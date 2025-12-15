from typing import Protocol


class StatsPort(Protocol):
    def get_user_stats(self, user_id: int) -> dict: ...

    def record_battle_result(
        self, winner_user_id: int, loser_user_id: int, total_damage: int, total_crits: int
    ) -> None: ...
