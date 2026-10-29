import inspect
import logging
from collections.abc import Awaitable, Iterator

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.exception.missing_argument import MissingArgument
from fjormcord.bot.artping.model.layout import Layout

# Arguments are split on whitespace, so names of several words are written with underscores
MULTI_WORD_HINT = "Use underscores for multi-word names, e.g. Black_Knight"
MESSAGE_ONE_NAME_ONLY = f"Only one name is allowed. {MULTI_WORD_HINT}"
# Replies echo user input, so never let a message trigger @everyone/@here or role pings
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)
# Discord rejects messages longer than this
MAX_MESSAGE_LENGTH = 2000
# The most text Discord allows across the text displays of one layout message
MAX_LAYOUT_TEXT_LENGTH = 4000


def log_info(reply: str) -> str:
    # Logs the reply of a command that changed something, and returns it
    logging.info(reply)
    return reply


def command_name(name: str, slash: bool) -> str:
    # A command as a reply tells the user to type it, in the syntax they used: ~addping or /addping
    return f"/{name}" if slash else f"~{name}"


async def await_reply(reply: str | Layout | Awaitable[str | Layout]) -> str | Layout:
    # Handlers and services return their reply directly, or as a coroutine when they wait on Discord
    return await reply if inspect.isawaitable(reply) else reply


def get_entries(content: str) -> list[str]:
    # Everything after the command, empty when there is nothing; split() also ignores repeated whitespace
    return content.split()[1:]


def get_single_name(content: str, argument: str) -> str:
    # For commands that take exactly one name; argument says what it is, e.g. "character name"
    entries = get_entries(content)
    if not entries:
        raise MissingArgument(argument)
    if len(entries) > 1:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    return entries[0]


def get_two_entries(content: str, first: str, second: str) -> tuple[str, str]:
    # For commands that take exactly two arguments; first and second say what they are, e.g. "currency name", "amount"
    entries = get_entries(content)
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    if len(entries) < 2:
        raise MissingArgument(second if entries else first)
    return entries[0], entries[1]


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    # Splits text into chunks within Discord's message length limit; each chunk is sent as a separate message
    chunks = []
    current = ""

    for separator, piece in _pieces(text, limit):
        if current and len(current) + len(separator) + len(piece) <= limit:
            current += separator + piece
        else:
            if current:
                chunks.append(current)
            current = piece

    if current:
        chunks.append(current)
    return chunks


def split_layout(layout: Layout, limit: int = MAX_LAYOUT_TEXT_LENGTH) -> list[Layout]:
    # A layout with more text than one message allows is sent as several, in order: a text that doesn't fit next to
    # the texts before it starts the next message, and one longer than a whole message is split as split_message
    # splits a reply. The controls go on the last message
    if sum(map(len, layout.texts)) <= limit:
        return [layout]

    parts: list[list[str]] = [[]]
    for text in layout.texts:
        if parts[-1] and sum(map(len, parts[-1])) + len(text) > limit:
            parts.append([])
        while len(text) > limit:
            first, *rest = split_message(text, limit)
            parts[-1].append(first)
            parts.append([])
            text = "\n".join(rest)
        parts[-1].append(text)

    return [Layout(tuple(texts)) for texts in parts[:-1]] + [Layout(tuple(parts[-1]), layout.rows)]


def _pieces(text: str, limit: int) -> Iterator[tuple[str, str]]:
    # Yields (separator, piece) pairs, each piece at most limit long
    for line_index, line in enumerate(text.split("\n")):
        line_separator = "\n" if line_index else ""
        if len(line) <= limit:
            yield line_separator, line
            continue

        for word_index, word in enumerate(line.split(" ")):
            separator = " " if word_index else line_separator
            for start in range(0, len(word), limit):
                yield separator if start == 0 else "", word[start : start + limit]
