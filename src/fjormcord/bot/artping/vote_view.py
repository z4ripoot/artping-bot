import discord

from fjormcord.bot.artping import config
# Imported as a module, since character_vote_service imports this one too
from fjormcord.bot.artping.service import character_vote_service

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
        reply = await character_vote_service.toggle_vote(interaction.client, interaction.message, interaction.user)
        await interaction.response.send_message(reply, ephemeral=True)
