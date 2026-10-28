from dataclasses import dataclass

import discord


@dataclass(frozen=True)
class Layout:
    # A reply laid out in a container (view.layout renders it): the texts, a separator between each, then a separator
    # and one row per entry of rows, holding its buttons or dropdown. Services return it instead of a string for the
    # replies that are laid out; a text too long for one message is split by message_util.split_layout
    texts: tuple[str, ...]
    rows: tuple[tuple[discord.ui.Item, ...], ...] = ()
