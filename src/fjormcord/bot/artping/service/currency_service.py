import math

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.currency import Currency
from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.util.message_util import log_info
from fjormcord.bot.artping.util.user_util import get_username

SCOREBOARD_PAGE_SIZE = 10

# The largest number SQLite can store in an INTEGER column
MAX_AMOUNT = 2 ** 63 - 1


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

    out = f"User {display_name}'s wallet:\n"

    for entry in wallet:
        out += f"{entry.currency_name}: {entry.amount}\n"

    return out


async def get_scoreboard(client: discord.Client, name: str, page: int = 1, slash: bool = False) -> str:
    currency = require_currency(name)
    currency_name = currency.name
    scoreboard = currency_repository.get_scoreboard(currency.id)

    if not scoreboard:
        return f"Nobody has set their {currency_name} yet"

    page_count = math.ceil(len(scoreboard) / SCOREBOARD_PAGE_SIZE)

    if not 1 <= page <= page_count:
        raise CommandError(f"Page {page} doesn't exist. The scoreboard for {currency_name} has {page_count} pages")

    if page_count == 1:
        out = f"Scoreboard for {currency_name}:\n"
    else:
        out = f"Scoreboard for {currency_name} (page {page}/{page_count}):\n"

    # Only the users on this page are looked up
    start = (page - 1) * SCOREBOARD_PAGE_SIZE
    for rank, entry in enumerate(scoreboard[start:start + SCOREBOARD_PAGE_SIZE], start=start + 1):
        out += f"{rank}. {await get_username(client, entry.user_id)} ({entry.amount})\n"

    if page < page_count:
        if slash:
            out += f"Use /scoreboard currency:{currency_name} page:{page + 1} for the next page"
        else:
            out += f"Use ~scoreboard {currency_name} {page + 1} for the next page"

    return out
