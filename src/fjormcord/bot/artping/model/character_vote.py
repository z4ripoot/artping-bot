from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CharacterVote:
    # Discord IDs as text, like the user IDs of pings
    message_id: str
    channel_id: str
    character_name: str
    proposer: str


@dataclass(frozen=True)
class VoteChannel:
    # Where a vote message goes: legacy sends to the message's channel, slash as the interaction's follow-up
    channel_id: str
    in_guild: bool
    # send(view) -> the sent message, whose ID the vote is stored by; view is the vote's layout
    send: Callable[[Any], Awaitable[Any]]
