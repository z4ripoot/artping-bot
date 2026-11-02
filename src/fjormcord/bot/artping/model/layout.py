from dataclasses import dataclass

import discord


@dataclass(frozen=True)
class Layout:
    texts: tuple[str, ...]
    rows: tuple[tuple[discord.ui.Item, ...], ...] = ()
