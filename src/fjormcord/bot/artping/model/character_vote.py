from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CharacterVote:
    message_id: str
    channel_id: str
    character_name: str
    proposer: str


@dataclass(frozen=True)
class VoteChannel:
    channel_id: str
    in_guild: bool
    send: Callable[[Any], Awaitable[Any]]
