import re

import discord

from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.service import art_ping_service  # A module: it imports this one too, via character_service
from fjormcord.bot.artping.util.interaction_util import answer_click


class SubscribeButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"subscribe:(?P<character_id>\d+)",
):
    def __init__(self, character_id: int, label: str):
        super().__init__(
            discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=f"subscribe:{character_id}")
        )
        self.character_id = character_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls(int(match["character_id"]), item.label)

    async def callback(self, interaction: discord.Interaction):
        await answer_click(
            self,
            interaction,
            lambda: art_ping_service.subscribe(str(interaction.user.id), self.character_id),
            "Something went wrong while subscribing",
        )

    @classmethod
    def for_character(cls, character: Character) -> "SubscribeButton":
        return cls(character.id, f"Subscribe to {character.name}"[:80])
