from dataclasses import dataclass


@dataclass(frozen=True)
class Currency:
    id: int
    name: str


@dataclass(frozen=True)
class WalletEntry:
    # One currency in a user's wallet
    currency_name: str
    amount: int


@dataclass(frozen=True)
class ScoreboardEntry:
    # One user's amount of the currency the scoreboard is for
    user_id: str
    amount: int
