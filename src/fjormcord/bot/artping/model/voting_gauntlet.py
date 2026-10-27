from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Entrant:
    # A character in a Voting Gauntlet matchup, with the votes counted so far
    name: str
    score: int


@dataclass(frozen=True)
class Round:
    # In UTC; end is the first minute after the round, which the page shows as e.g. "3:59 a.m."
    start: datetime
    end: datetime
    # The two entrants of each matchup, in the page's order
    matchups: list[tuple[Entrant, Entrant]]
