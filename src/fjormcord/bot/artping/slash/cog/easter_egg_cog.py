import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping import easter_eggs
from fjormcord.bot.artping.slash.runner import run


class EasterEggCog(commands.Cog):
    # The slash versions of the easter eggs that are triggered by words, such as "thanks lorenz"
    @app_commands.command(name="lorenz")
    async def lorenz(self, interaction: discord.Interaction):
        await run(interaction, easter_eggs.lorenz_smile)

    @app_commands.command(name="chromk", description="Chromk")
    async def chromk(self, interaction: discord.Interaction):
        await run(interaction, easter_eggs.chromk)
