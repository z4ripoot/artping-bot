from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    name: str
    # What ~<name> posts: the text copied from a Discord message, or a website link
    content: str
    # The link the content came from
    source: str
