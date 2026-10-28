import re

import discord

from fjormcord.bot.artping.model.currency import Currency
from fjormcord.bot.artping.service import currency_service  # A module: it imports this one too
from fjormcord.bot.artping.view import page_view

CURRENCY_SELECT_ID = "scoreboard_currency"


class CurrencySelect(discord.ui.DynamicItem[discord.ui.Select], template=CURRENCY_SELECT_ID):
    # The dropdown of currencies under a scoreboard: picking one turns the message to page 1 of its scoreboard. The
    # options' values are the currencies' IDs. Registered with Client.add_dynamic_items, so a pick is handled after a
    # restart too
    def __init__(self, select: discord.ui.Select):
        super().__init__(select)

    @classmethod
    def for_currencies(cls, currencies: list[Currency], current_id: int) -> "CurrencySelect":
        # Discord allows option labels of 100 characters at most
        options = [
            discord.SelectOption(label=currency.name[:100], value=str(currency.id), default=currency.id == current_id)
            for currency in currencies
        ]
        select = discord.ui.Select(custom_id=CURRENCY_SELECT_ID, placeholder="Show another currency", options=options)
        return cls(select)

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Select, match: re.Match[str], /):
        return cls(item)

    async def callback(self, interaction: discord.Interaction):
        currency_id = int(self.item.values[0])
        # The scoreboard the message shows: its selected option, on the page its buttons say
        current_id = next((int(option.value) for option in self.item.options if option.default), None)
        page = page_view.shown_page(interaction.message)
        await page_view.show_page(
            interaction,
            lambda: currency_service.get_scoreboard_page(interaction.client, currency_id, 1),
            "Something went wrong while showing that scoreboard",
            # A refused pick is drawn away; without a selected option there is nothing to draw
            redraw=None
            if current_id is None
            else lambda: currency_service.get_scoreboard_page(interaction.client, current_id, page),
        )
