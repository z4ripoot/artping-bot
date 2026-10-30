from collections.abc import Callable
from dataclasses import dataclass
from datetime import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only for the annotation, so models still import nothing from the project when the bot runs
    from fjormcord.bot.artping.config import Settings


@dataclass(frozen=True)
class WeeklyReminder:
    # Used in the logs, e.g. 'Coliseum notification'
    name: str
    # The day it closes, as datetime.weekday(): Monday is 0
    weekday: int
    # When it closes, in UTC
    closing_time: time
    # The start of the message, followed by when it closes, e.g. 'Divine Games closes'
    text: str
    # The channel to post to, read from the settings when the reminder runs; None disables the reminder
    channel_id: "Callable[[Settings], int | None]"
