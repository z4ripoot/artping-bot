from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    name: str
    content: str
    source: str
