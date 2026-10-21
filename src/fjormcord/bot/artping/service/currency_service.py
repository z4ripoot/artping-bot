import logging

import discord

from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.repository.currency_repository import get_currency_row, get_wallet_row, get_wallet_rows, get_scoreboard_rows
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, get_first, get_entries, has_extra_entries
from fjormcord.bot.artping.util.user_util import get_username

SCOREBOARD_PAGE_SIZE = 10


def add_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to add currency"
        logging.warning(out)
        return out

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    if get_currency_row(entry):
        out = f"Failed to add currency {entry}. Currency {entry} already exists"
        logging.warning(out)
        return out

    currency_repository.add_currency(entry)

    out = f"Currency {entry} has been added"
    logging.info(out)
    return out


def remove_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to remove currency"
        logging.warning(out)
        return out

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Failed to remove currency {entry}. Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_repository.remove_currency(currency['GACHA_CURRENCY_ID'])

    out = f"Currency {currency['NAME']} has been removed"
    logging.info(out)
    return out


def set_currency(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if entries is not None and len(entries) > 2:
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    if entries is None or len(entries) != 2:
        out = "Failed to set currency"
        logging.warning(out)
        return out

    entry = entries[0]

    try:
        amount = int(entries[1])
    except ValueError:
        out = f"Failed to set currency. Please enter a valid amount for your {entry}."
        logging.warning(out)
        return out

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Failed to set currency {entry} for user. Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_repository.set_currency(str(message.author.id), currency['GACHA_CURRENCY_ID'], amount)

    out = f"Your {currency['NAME']} has been set to {amount}"
    logging.info(out)
    return out


def clear_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to clear currency"
        logging.warning(out)
        return out

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Failed to clear currency {entry} for user. Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_id = currency['GACHA_CURRENCY_ID']
    currency_name = currency['NAME']
    user_id = str(message.author.id)

    if get_wallet_row(user_id, currency_id) is None:
        out = f"Failed to clear currency {currency_name} for user. Currency {currency_name} for user doesn't exist"
        logging.warning(out)
        return out

    currency_repository.clear_currency(user_id, currency_id)

    out = f"Your {currency_name} has been cleared"
    logging.info(out)
    return out


def check_wallet(client: discord.Client, message: discord.Message):
    out = f"User {message.author.display_name}'s wallet:\n"

    for wallet in get_wallet_rows(str(message.author.id)):
        out += f"{wallet['NAME']}: {wallet['AMOUNT']}\n"

    return out


async def get_scoreboard(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if entries is None:
        out = "Failed to check scoreboard"
        logging.warning(out)
        return out

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
        out = f"Failed to check scoreboard for {entry}. Currency {entry} doesn't exist"
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
