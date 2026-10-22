import logging
import math

import discord

from fjormcord.bot.artping.model.currency import Currency
from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, CommandError, MissingArgument, \
    get_entries, get_single_name
from fjormcord.bot.artping.util.user_util import get_username

SCOREBOARD_PAGE_SIZE = 10

# The largest number SQLite can store in an INTEGER column
MAX_AMOUNT = 2 ** 63 - 1


def require_currency(name: str) -> Currency:
    currency = currency_repository.get_currency(name)
    if currency is None:
        raise CommandError(f"Currency {name} doesn't exist")
    return currency


def add_currency(client: discord.Client, message: discord.Message) -> str:
    entry = get_single_name(message.content, "currency name")

    existing = currency_repository.get_currency(entry)
    if existing:
        raise CommandError(f"Currency {existing.name} already exists")

    currency_repository.add_currency(entry)

    out = f"Currency {entry} has been added"
    logging.info(out)
    return out


def remove_currency(client: discord.Client, message: discord.Message) -> str:
    currency = require_currency(get_single_name(message.content, "currency name"))

    currency_repository.remove_currency(currency.id)

    out = f"Currency {currency.name} has been removed"
    logging.info(out)
    return out


def set_currency(client: discord.Client, message: discord.Message) -> str:
    entries = get_entries(message.content)

    if not entries:
        raise MissingArgument("currency name")
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    if len(entries) == 1:
        raise MissingArgument("amount")

    entry, amount_entry = entries

    try:
        amount = int(amount_entry)
    except ValueError:
        raise CommandError(f"Failed to set currency. Please enter a valid amount for your {entry}.")

    if amount < 0:
        raise CommandError("Failed to set currency. The amount can't be negative")
    if amount > MAX_AMOUNT:
        raise CommandError("Failed to set currency. The amount is too large")

    currency = require_currency(entry)

    currency_repository.set_currency(str(message.author.id), currency.id, amount)

    out = f"Your {currency.name} has been set to {amount}"
    logging.info(out)
    return out


def clear_currency(client: discord.Client, message: discord.Message) -> str:
    currency = require_currency(get_single_name(message.content, "currency name"))
    currency_id = currency.id
    user_id = str(message.author.id)

    if not currency_repository.has_wallet_entry(user_id, currency_id):
        raise CommandError(f"You don't have any {currency.name} set")

    currency_repository.clear_currency(user_id, currency_id)

    out = f"Your {currency.name} has been cleared"
    logging.info(out)
    return out


def check_wallet(client: discord.Client, message: discord.Message) -> str:
    wallet = currency_repository.get_wallet(str(message.author.id))

    if not wallet:
        return "Your wallet is empty. Use ~setcurrency to add a currency"

    out = f"User {message.author.display_name}'s wallet:\n"

    for entry in wallet:
        out += f"{entry.currency_name}: {entry.amount}\n"

    return out


async def get_scoreboard(client: discord.Client, message: discord.Message) -> str:
    entries = get_entries(message.content)

    if not entries:
        raise MissingArgument("currency name")
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)

    try:
        page = int(entries[1]) if len(entries) == 2 else 1
    except ValueError:
        # The optional second argument is the page; anything else is most likely a name with spaces
        raise CommandError(MESSAGE_ONE_NAME_ONLY)

    currency = require_currency(entries[0])
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
        out += f"Use ~scoreboard {currency_name} {page + 1} for the next page"

    return out
