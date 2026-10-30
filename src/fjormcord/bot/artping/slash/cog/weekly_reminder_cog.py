import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping.service import weekly_reminder_service
from fjormcord.bot.artping.slash.runner import admin_command, run


class WeeklyReminderCog(commands.Cog):
    @app_commands.command(name="closingtimes", description="See when Coliseum/Aether Raids and Divine Games close next")
    async def closing_times(self, interaction: discord.Interaction):
        await run(interaction, weekly_reminder_service.get_closing_times)

    @admin_command(name="sendreminders", description="Debug: send the weekly reminders to their channels now")
    async def send_reminders(self, interaction: discord.Interaction):
        await run(
            interaction,
            lambda: weekly_reminder_service.send_reminders(interaction.client),
            defer=True,
            ephemeral=True,
        )
