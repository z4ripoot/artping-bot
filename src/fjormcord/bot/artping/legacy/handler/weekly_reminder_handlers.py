import discord

from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.service import weekly_reminder_service


def get_closing_times(client: discord.Client, message: discord.Message) -> Layout:
    return weekly_reminder_service.get_closing_times()


async def send_reminders(client: discord.Client, message: discord.Message) -> str:
    return await weekly_reminder_service.send_reminders(client)
