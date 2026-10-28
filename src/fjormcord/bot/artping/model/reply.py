from dataclasses import dataclass

import discord


@dataclass(frozen=True)
class Reply:
    # A reply with buttons; a service whose reply has none returns the text alone. A long reply is split into several
    # messages, with the buttons on the last one
    content: str
    view: discord.ui.View
