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
    # False for a vote still counted by its reactions
    uses_button: bool = True


@dataclass(frozen=True)
class VoteChannel:
    # Where a vote message goes: legacy sends to the message's channel, slash as the interaction's follow-up
    channel_id: str
    in_guild: bool
    # send(content, view) -> the sent message, whose ID the vote is stored by
    send: Callable[[str, Any], Awaitable[Any]]
