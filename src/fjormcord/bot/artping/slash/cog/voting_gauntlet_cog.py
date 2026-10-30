import discord
from discord.ext import commands

from fjormcord.bot.artping.service import voting_gauntlet_service
from fjormcord.bot.artping.slash.runner import admin_command, run


class VotingGauntletCog(commands.Cog):
    @admin_command(
        name="sendvotinggauntlet", description="Debug: post the Voting Gauntlet scores now, as the hourly task does"
    )
    async def send_voting_gauntlet(self, interaction: discord.Interaction):
        # Reading the site can take longer than Discord's 3 seconds
        await run(
            interaction,
            lambda: voting_gauntlet_service.send_scores(interaction.client),
            defer=True,
            ephemeral=True,
        )
