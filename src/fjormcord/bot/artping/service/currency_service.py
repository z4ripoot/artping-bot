import logging

import discord

from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.repository.currency_repository import get_currency_row, get_wallet_row, get_wallet_rows, get_scoreboard_rows
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, MissingArgument, get_first, get_entries, \
    has_extra_entries
from fjormcord.bot.artping.util.user_util import get_username

SCOREBOARD_PAGE_SIZE = 10

# The largest number SQLite can store in an INTEGER column
MAX_AMOUNT = 2 ** 63 - 1


def add_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        raise MissingArgument("currency name")

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    existing = get_currency_row(entry)
    if existing:
        out = f"Currency {existing['NAME']} already exists"
        logging.warning(out)
        return out

    currency_repository.add_currency(entry)

    out = f"Currency {entry} has been added"
    logging.info(out)
    return out


def remove_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        raise MissingArgument("currency name")

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_repository.remove_currency(currency['GACHA_CURRENCY_ID'])

    out = f"Currency {currency['NAME']} has been removed"
    logging.info(out)
    return out


def set_currency(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if entries is None:
        raise MissingArgument("currency name")

    if len(entries) > 2:
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    if len(entries) == 1:
        raise MissingArgument("amount")

    entry = entries[0]

    try:
        amount = int(entries[1])
    except ValueError:
        out = f"Failed to set currency. Please enter a valid amount for your {entry}."
        logging.warning(out)
        return out

    if amount < 0:
        out = "Failed to set currency. The amount can't be negative"
        logging.warning(out)
        return out

    if amount > MAX_AMOUNT:
        out = "Failed to set currency. The amount is too large"
        logging.warning(out)
        return out

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_repository.set_currency(str(message.author.id), currency['GACHA_CURRENCY_ID'], amount)

    out = f"Your {currency['NAME']} has been set to {amount}"
    logging.info(out)
    return out


def clear_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        raise MissingArgument("currency name")

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_id = currency['GACHA_CURRENCY_ID']
    currency_name = currency['NAME']
    user_id = str(message.author.id)

    if get_wallet_row(user_id, currency_id) is None:
        out = f"You don't have any {currency_name} set"
        logging.warning(out)
        return out

    currency_repository.clear_currency(user_id, currency_id)

    out = f"Your {currency_name} has been cleared"
    logging.info(out)
    return out


def check_wallet(client: discord.Client, message: discord.Message):
    wallet_rows = get_wallet_rows(str(message.author.id))

    if not wallet_rows:
        return "Your wallet is empty. Use ~setcurrency to add a currency"

    out = f"User {message.author.display_name}'s wallet:\n"

    for wallet in wallet_rows:
        out += f"{wallet['NAME']}: {wallet['AMOUNT']}\n"

    return out


async def get_scoreboard(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if entries is None:
        raise MissingArgument("currency name")

    if len(entries) > 2:
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    try:
        page = int(entries[1]) if len(entries) == 2 else 1
    except ValueError:
        # The optional second argument is the page; anything else is most likely a name with spaces
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    entry = entries[0]
    currency = get_currency_row(entry)

    if currency is None:
        out = f"Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_name = currency['NAME']
    rows = get_scoreboard_rows(currency['GACHA_CURRENCY_ID'])

    if not rows:
        return f"Nobody has set their {currency_name} yet"

    page_count = (len(rows) + SCOREBOARD_PAGE_SIZE - 1) // SCOREBOARD_PAGE_SIZE

    if not 1 <= page <= page_count:
        out = f"Page {page} doesn't exist. The scoreboard for {currency_name} has {page_count} pages"
        logging.warning(out)
        return out

    if page_count == 1:
        out = f"Scoreboard for {currency_name}:\n"
    else:
        out = f"Scoreboard for {currency_name} (page {page}/{page_count}):\n"

    # Only the users on this page are looked up
    start = (page - 1) * SCOREBOARD_PAGE_SIZE
    for i, row in enumerate(rows[start:start + SCOREBOARD_PAGE_SIZE], start=start + 1):
        out += f"{i}. {await get_username(client, row['USER'])} ({row['AMOUNT']})\n"

    if page < page_count:
        out += f"Use ~scoreboard {currency_name} {page + 1} for the next page"

    return out
