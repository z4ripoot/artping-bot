import discord

from fjormcord.bot.artping.service import voting_gauntlet_service


async def send_voting_gauntlet(client: discord.Client, message: discord.Message) -> str:
    return await voting_gauntlet_service.send_scores(client)
