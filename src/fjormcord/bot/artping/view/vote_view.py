import logging
import re

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.service import character_vote_service  # A module: it imports this one too

VOTE_BUTTON_ID = "character_vote"


class VoteButton(discord.ui.DynamicItem[discord.ui.Button], template=VOTE_BUTTON_ID):
    # The Vote button under a vote message. Every vote message has the same custom_id, the one vote messages had before
    # they were laid out, so their clicks still arrive; the vote is found by the clicked message's ID. Registered with
    # Client.add_dynamic_items, so a click is handled after a restart too
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
        # The count isn't needed to handle a click
        return cls()

    async def callback(self, interaction: discord.Interaction):
        # Deferred first: passing a vote edits every vote message for the name, which may take longer than the
        # 3 seconds Discord waits for an answer
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            reply = await character_vote_service.toggle_vote(interaction.client, interaction.message, interaction.user)
        except Exception:
            # Answered here, since after the defer the view's on_error would only log and leave the clicker waiting
            logging.exception("Vote click on message %s failed", interaction.message.id)
            reply = "Something went wrong while voting"
        await interaction.followup.send(reply, ephemeral=True)
