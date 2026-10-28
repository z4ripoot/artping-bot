import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.currency import Currency
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.util.message_util import log_info
from fjormcord.bot.artping.util.page_util import PAGE_SIZE, get_page, paged_header
from fjormcord.bot.artping.util.user_util import get_username
from fjormcord.bot.artping.view import page_view, scoreboard_view  # Modules: they import this one too

# Discord allows a dropdown 25 options at most
MAX_CURRENCY_OPTIONS = 25

# The largest number SQLite can store in an INTEGER column
MAX_AMOUNT = 2**63 - 1


def require_currency(name: str) -> Currency:
    currency = currency_repository.get_currency(name)
    if currency is None:
        raise CommandError(f"Currency {name} doesn't exist")
    return currency


def add_currency(name: str) -> str:
    existing = currency_repository.get_currency(name)
    if existing:
        raise CommandError(f"Currency {existing.name} already exists")

    currency_repository.add_currency(name)

    return log_info(f"Currency {name} has been added")


def remove_currency(name: str) -> str:
    currency = require_currency(name)

    currency_repository.remove_currency(currency.id)

    return log_info(f"Currency {currency.name} has been removed")


def set_currency(user_id: str, name: str, amount: int) -> str:
    if amount < 0:
        raise CommandError("Failed to set currency. The amount can't be negative")
    if amount > MAX_AMOUNT:
        raise CommandError("Failed to set currency. The amount is too large")

    currency = require_currency(name)

    currency_repository.set_currency(user_id, currency.id, amount)

    return log_info(f"Your {currency.name} has been set to {amount}")


def clear_currency(user_id: str, name: str) -> str:
    currency = require_currency(name)

    if not currency_repository.has_wallet_entry(user_id, currency.id):
        raise CommandError(f"You don't have any {currency.name} set")

    currency_repository.clear_currency(user_id, currency.id)

    return log_info(f"Your {currency.name} has been cleared")


def check_wallet(user_id: str, display_name: str, slash: bool = False) -> str:
    wallet = currency_repository.get_wallet(user_id)

    if not wallet:
        set_command = "/setcurrency" if slash else "~setcurrency"
        return f"Your wallet is empty. Use {set_command} to add a currency"

    lines = [f"User {display_name}'s wallet:"]
    lines += [f"{entry.currency_name}: {entry.amount}" for entry in wallet]
    return "\n".join(lines)


async def get_scoreboard(client: discord.Client, name: str, page: int = 1) -> Layout:
    return await _render_scoreboard(client, require_currency(name), page)


async def get_scoreboard_page(client: discord.Client, currency_id: int, page: int) -> Layout:
    # A click on Previous or Next, or a pick in the dropdown; the currency may have been removed since
    currency = currency_repository.get_currency_by_id(currency_id)
    if currency is None:
        raise CommandError("This currency doesn't exist anymore")
    return await _render_scoreboard(client, currency, page)


async def _render_scoreboard(client: discord.Client, currency: Currency, page: int) -> Layout:
    # The header, the ranking, then the dropdown to switch currencies (when there is another) and the page buttons
    # (when there are several pages)
    header = f"### Scoreboard for {currency.name}"
    rows = []
    currencies = currency_repository.get_currencies(MAX_CURRENCY_OPTIONS)
    if len(currencies) >= 2:
        rows.append((scoreboard_view.CurrencySelect.for_currencies(currencies, currency.id),))

    scoreboard = currency_repository.get_scoreboard(currency.id)
    if not scoreboard:
        # Laid out too, so the dropdown can switch away from it
        return Layout((header, f"Nobody has set their {currency.name} yet"), tuple(rows))

    entries, page_count = get_page(scoreboard, page, f"The scoreboard for {currency.name}")
    header = paged_header(header, page, page_count)

    # Only the users on this page are looked up
    first_rank = (page - 1) * PAGE_SIZE + 1
    lines = [
        f"{rank}. {await get_username(client, entry.user_id)} ({entry.amount})"
        for rank, entry in enumerate(entries, start=first_rank)
    ]

    buttons = page_view.page_buttons("scoreboard", currency.id, page, page_count)
    if buttons:
        rows.append(buttons)
    return Layout((header, "\n".join(lines)), tuple(rows))
