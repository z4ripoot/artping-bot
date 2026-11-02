from dataclasses import dataclass


@dataclass(frozen=True)
class Currency:
    id: int
    name: str


@dataclass(frozen=True)
class WalletEntry:
    currency_name: str
    amount: int


@dataclass(frozen=True)
class ScoreboardEntry:
    user_id: str
    amount: int
