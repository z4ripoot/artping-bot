from dataclasses import dataclass


@dataclass(frozen=True)
class Character:
    id: int
    name: str
