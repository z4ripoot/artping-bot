import re

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.service import character_vote_service  # A module: it imports this one too
from fjormcord.bot.artping.util.interaction_util import answer_click

VOTE_BUTTON_ID = "character_vote"


class VoteButton(discord.ui.DynamicItem[discord.ui.Button], template=VOTE_BUTTON_ID):
    def __init__(self, count: int = 0):
        settings = config.read_settings()
        super().__init__(
            discord.ui.Button(
                label=f"Vote ({count}/{settings.character_votes_needed})",
                emoji=settings.character_vote_emoji,
                style=discord.ButtonStyle.primary,
                custom_id=VOTE_BUTTON_ID,
            )
        )

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls()

    async def callback(self, interaction: discord.Interaction):
        await answer_click(
            self,
            interaction,
            lambda: character_vote_service.toggle_vote(interaction.client, interaction.message, interaction.user),
            "Something went wrong while voting",
            defer=True,
        )
