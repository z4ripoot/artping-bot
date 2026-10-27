import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.exception.missing_argument import MissingArgument
from fjormcord.bot.artping.service import currency_service
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, get_entries, get_single_name, get_two_entries


def add_currency(client: discord.Client, message: discord.Message) -> str:
    return currency_service.add_currency(get_single_name(message.content, "currency name"))


def remove_currency(client: discord.Client, message: discord.Message) -> str:
    return currency_service.remove_currency(get_single_name(message.content, "currency name"))


def set_currency(client: discord.Client, message: discord.Message) -> str:
    entry, amount_entry = get_two_entries(message.content, "currency name", "amount")

    try:
        amount = int(amount_entry)
    except ValueError:
        raise CommandError(f"Failed to set currency. Please enter a valid amount for your {entry}.")

    return currency_service.set_currency(str(message.author.id), entry, amount)


def clear_currency(client: discord.Client, message: discord.Message) -> str:
    return currency_service.clear_currency(str(message.author.id), get_single_name(message.content, "currency name"))


def check_wallet(client: discord.Client, message: discord.Message) -> str:
    return currency_service.check_wallet(str(message.author.id), message.author.display_name)


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

    return await currency_service.get_scoreboard(client, entries[0], page)
