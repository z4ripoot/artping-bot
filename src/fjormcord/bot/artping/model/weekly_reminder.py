from collections.abc import Callable
from dataclasses import dataclass
from datetime import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fjormcord.bot.artping.config import Settings


@dataclass(frozen=True)
class WeeklyReminder:
    name: str
    weekday: int
    closing_time: time
    text: str
    channel_id: "Callable[[Settings], int | None]"
