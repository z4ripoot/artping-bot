from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Entrant:
    name: str
    score: int | None
    behind: bool


@dataclass(frozen=True)
class Round:
    start: datetime
    end: datetime
    matchups: list[tuple[Entrant, Entrant]]
