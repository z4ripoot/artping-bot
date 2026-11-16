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


SUBSCRIBE_SELECT_ID = "subscribe_select"
MAX_SELECT_OPTIONS = 25  # Discord's limit of options in a dropdown


class SubscribeSelect(discord.ui.DynamicItem[discord.ui.Select], template=SUBSCRIBE_SELECT_ID):
    def __init__(self, select: discord.ui.Select):
        super().__init__(select)

    @classmethod
    def for_characters(cls, characters: list[Character]) -> "SubscribeSelect":
        options = [
            discord.SelectOption(label=character.name[:100], value=str(character.id))
            for character in characters[:MAX_SELECT_OPTIONS]
        ]
        select = discord.ui.Select(
            custom_id=SUBSCRIBE_SELECT_ID,
            placeholder="Subscribe to characters",
            min_values=1,
            max_values=len(options),
            options=options,
        )
        return cls(select)

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Select, match: re.Match[str], /):
        return cls(item)

    async def callback(self, interaction: discord.Interaction):
        await answer_click(
            self,
            interaction,
            lambda: art_ping_service.subscribe_many(
                str(interaction.user.id), [int(value) for value in self.item.values]
            ),
            "Something went wrong while subscribing",
        )
