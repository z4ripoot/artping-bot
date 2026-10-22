from collections.abc import Callable
from time import monotonic


class Cooldowns:
    # When each user may use each command again; kept in memory, so cooldowns reset when the bot restarts

    def __init__(self, clock: Callable[[], float] = monotonic):
        self._clock = clock
        # (command name, user ID) -> clock() time at which the cooldown ends
        self._ends: dict[tuple[str, int], float] = {}

    def remaining(self, command_name: str, user_id: int) -> float:
        # Seconds until the user can use the command again; 0 when they can use it now
        now = self._clock()
        return max(0.0, self._ends.get((command_name, user_id), now) - now)

    def start(self, command_name: str, user_id: int, seconds: float):
        self._ends[(command_name, user_id)] = self._clock() + seconds
