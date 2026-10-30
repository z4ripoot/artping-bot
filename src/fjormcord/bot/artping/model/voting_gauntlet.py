from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Entrant:
    # A character in a Voting Gauntlet matchup, with the votes counted so far; None before the first count, as the
    # page shows a round's matchups before it starts
    name: str
    score: int | None
    # Whether the site shows the character as behind (the game's "Weaker"); at most one side of a matchup is
    behind: bool


@dataclass(frozen=True)
class Round:
    # In UTC; end is the first minute after the round, which the page shows as e.g. "3:59 a.m."
    start: datetime
    end: datetime
    # The two entrants of each matchup, in the page's order
    matchups: list[tuple[Entrant, Entrant]]
