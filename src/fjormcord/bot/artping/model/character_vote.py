from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterVote:
    # Discord IDs as text, like the user IDs of pings
    message_id: str
    channel_id: str
    character_name: str
    proposer: str
