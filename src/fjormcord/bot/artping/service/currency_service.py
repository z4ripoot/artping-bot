import discord
import logging

from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.repository.currency_repository import get_currency_row, get_wallet_row, get_wallet_rows, get_scoreboard_rows
from fjormcord.bot.artping.util.message_util import get_first, get_entries


def add_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to add currency"
        logging.warning(out)
        return out

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

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Failed to remove currency {entry}. Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_id = currency['GACHA_CURRENCY_ID']
    currency_name = currency['NAME']

    currency_repository.remove_currency(currency_id)

    out = f"Currency {currency_name} has been removed"
    logging.info(out)
    return out


def set_currency(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if entries is None or len(entries) != 2:
        out = "Failed to set currency"
        logging.warning(out)
        return out

    entry = entries[0]

    try:
        amount = int(entries[1])
    except (Exception,):
        out = f"Failed to set currency. Please enter a valid amount for your {entry}."
        logging.warning(out)
        return out

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Failed to set currency {entry} for user. Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_id = currency['GACHA_CURRENCY_ID']
    currency_name = currency['NAME']
    user_id = str(message.author.id)
    wallet = get_wallet_row(user_id, currency_id)

    if wallet:
        currency_repository.set_currency(user_id, currency_id, amount)
    else:
        currency_repository.create_wallet(user_id, currency_id, amount)

    out = f"Your {currency_name} has been set to {amount}"
    logging.info(out)
    return out


def clear_currency(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to clear currency"
        logging.warning(out)
        return out

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Failed to clear currency {entry} for user. Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_id = currency['GACHA_CURRENCY_ID']
    currency_name = currency['NAME']
    user_id = str(message.author.id)
    wallet = get_wallet_row(user_id, currency_id)

    if wallet is None:
        out = f"Failed to clear currency {currency_name} for user. Currency {currency_name} for user doesn't exist"
        logging.warning(out)
        return out

    currency_repository.clear_currency(user_id, currency_id)

    out = f"Your {currency_name} has been cleared"
    logging.info(out)
    return out


def check_wallet(client: discord.Client, message: discord.Message):
    user_id = str(message.author.id)
    wallets = get_wallet_rows(user_id)
    out = f"User {message.author.global_name}'s wallet:\n"

    for wallet in wallets:
        out += f"{wallet['NAME']}: {wallet['AMOUNT']}\n"

    return out


async def get_scoreboard(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = f"Failed to check scoreboard"
        logging.warning(out)
        return out

    currency = get_currency_row(entry)

    if currency is None:
        out = f"Failed to check scoreboard for {entry}. Currency {entry} doesn't exist"
        logging.warning(out)
        return out

    currency_id = currency['GACHA_CURRENCY_ID']
    currency_name = currency['NAME']

    logging.info("Check scoreboard for currency %s", currency_name)

    scoreboard_rows = get_scoreboard_rows(currency_id)
    out = f"Scoreboard for {currency_name}:\n"

    for i, row in enumerate(scoreboard_rows, start=1):
        user: discord.User = await client.fetch_user(row['USER'])
        username = user.global_name
        out += f"{i}. {username} ({row['AMOUNT']})\n"

    logging.info("Checked scoreboard for currency %s", currency_name)
    return out
