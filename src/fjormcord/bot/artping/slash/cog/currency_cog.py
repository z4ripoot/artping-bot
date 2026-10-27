import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping.service import currency_service
from fjormcord.bot.artping.slash.options import currency_choices, to_name
from fjormcord.bot.artping.slash.runner import admin_command, run

CURRENCY_DESCRIPTION = "The currency's name"


class CurrencyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setcurrency", description="Set the number of orbs, primos or any other currency you have"
    )
    @app_commands.describe(currency=CURRENCY_DESCRIPTION, amount="How many you have")
    @app_commands.autocomplete(currency=currency_choices)
    async def set_currency(
        self, interaction: discord.Interaction, currency: str, amount: app_commands.Range[int, 0, None]
    ):
        await run(
            interaction, lambda: currency_service.set_currency(str(interaction.user.id), to_name(currency), amount)
        )

    @app_commands.command(name="clearcurrency", description="Clear the number you have saved for this currency")
    @app_commands.describe(currency=CURRENCY_DESCRIPTION)
    @app_commands.autocomplete(currency=currency_choices)
    async def clear_currency(self, interaction: discord.Interaction, currency: str):
        await run(interaction, lambda: currency_service.clear_currency(str(interaction.user.id), to_name(currency)))

    @app_commands.command(name="checkwallet", description="Shows a list of all currencies you have and their count")
    async def check_wallet(self, interaction: discord.Interaction):
        await run(
            interaction,
            lambda: currency_service.check_wallet(str(interaction.user.id), interaction.user.display_name, slash=True),
        )

    @app_commands.command(name="scoreboard", description="Shows a leaderboard of this currency, 10 users per page")
    @app_commands.describe(currency=CURRENCY_DESCRIPTION, page="The page to show; the first by default")
    @app_commands.autocomplete(currency=currency_choices)
    async def scoreboard(
        self, interaction: discord.Interaction, currency: str, page: app_commands.Range[int, 1, None] = 1
    ):
        await run(
            interaction,
            lambda: currency_service.get_scoreboard(interaction.client, to_name(currency), page, slash=True),
            defer=True,
        )

    @admin_command(name="addcurrency", description="Add a currency that users can track")
    @app_commands.describe(currency="The new currency's name; spaces are fine")
    async def add_currency(self, interaction: discord.Interaction, currency: str):
        await run(interaction, lambda: currency_service.add_currency(to_name(currency)))

    @admin_command(name="removecurrency", description="Remove a currency and clear it from all wallets")
    @app_commands.describe(currency=CURRENCY_DESCRIPTION)
    @app_commands.autocomplete(currency=currency_choices)
    async def remove_currency(self, interaction: discord.Interaction, currency: str):
        await run(interaction, lambda: currency_service.remove_currency(to_name(currency)))
