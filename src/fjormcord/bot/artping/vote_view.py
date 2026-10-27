import logging

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.service import character_vote_service  # A module: it imports this one too

VOTE_BUTTON_ID = "character_vote"


class VoteView(discord.ui.View):
    # Persistent: a fixed custom_id and no timeout, so the button still works after a restart. The vote is found
    # by the clicked message's ID, so the one view registered at startup serves every vote message.
    def __init__(self, count: int = 0):
        super().__init__(timeout=None)
        settings = config.read_settings()
        self.vote.label = f"Vote ({count}/{settings.character_votes_needed})"
        self.vote.emoji = settings.character_vote_emoji

    @discord.ui.button(custom_id=VOTE_BUTTON_ID, style=discord.ButtonStyle.primary)
    async def vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Deferred first: passing a vote edits every vote message for the name, which may take longer than the
        # 3 seconds Discord waits for an answer
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            reply = await character_vote_service.toggle_vote(interaction.client, interaction.message, interaction.user)
        except Exception:
            # Answered here, since after the defer View.on_error would only log and leave the clicker waiting
            logging.exception("Vote click on message %s failed", interaction.message.id)
            reply = "Something went wrong while voting"
        await interaction.followup.send(reply, ephemeral=True)
