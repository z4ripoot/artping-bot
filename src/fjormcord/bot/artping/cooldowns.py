import math
from collections.abc import Callable
from time import monotonic

from fjormcord.bot.artping.util.message_util import CommandError


class Cooldowns:
    # When each user may use a command again: one cooldown per user, whichever command they used, shared by the ~ and
    # slash commands. Kept in memory, so cooldowns reset when the bot restarts

    def __init__(self, seconds: float, clock: Callable[[], float] = monotonic):
        # 0 means no cooldown
        self._seconds = seconds
        self._clock = clock
        # user ID -> clock() time at which the cooldown ends
        self._ends: dict[int, float] = {}

    def remaining(self, user_id: int) -> float:
        # Seconds until the user can use a command again; 0 when they can use one now
        now = self._clock()
        return max(0.0, self._ends.get(user_id, now) - now)

    def check(self, user_id: int):
        # Turns the user down while their cooldown runs
        remaining = self.remaining(user_id)
        if remaining > 0:
            seconds = math.ceil(remaining)
            raise CommandError(
                f"You used a command recently. Try again in {seconds} second{'' if seconds == 1 else 's'}")

    def start(self, user_id: int):
        if self._seconds > 0:
            self._ends[user_id] = self._clock() + self._seconds
