import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping import easter_eggs
from fjormcord.bot.artping.slash.runner import run


class EasterEggCog(commands.Cog):
    @app_commands.command(name="lorenz")
    async def lorenz(self, interaction: discord.Interaction):
        await run(interaction, easter_eggs.lorenz_smile)

    @app_commands.command(name="chromk", description="Chromk")
    async def chromk(self, interaction: discord.Interaction):
        await run(interaction, easter_eggs.chromk)
