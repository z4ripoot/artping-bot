import inspect
import logging
from collections.abc import Awaitable, Iterator

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.exception.missing_argument import MissingArgument
from fjormcord.bot.artping.model.layout import Layout

MULTI_WORD_HINT = "Use underscores for multi-word names, e.g. Black_Knight"
MESSAGE_ONE_NAME_ONLY = f"Only one name is allowed. {MULTI_WORD_HINT}"
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)
MAX_MESSAGE_LENGTH = 2000
MAX_LAYOUT_TEXT_LENGTH = 4000


def log_and_reply(reply: str) -> str:
    logging.info(reply)
    return reply


def command_name(name: str, slash: bool) -> str:
    return f"/{name}" if slash else f"~{name}"


async def await_reply(reply: str | Layout | Awaitable[str | Layout]) -> str | Layout:
    return await reply if inspect.isawaitable(reply) else reply


def get_entries(content: str) -> list[str]:
    return content.split()[1:]


def get_single_name(content: str, argument: str) -> str:
    entries = get_entries(content)
    if not entries:
        raise MissingArgument(argument)
    if len(entries) > 1:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    return entries[0]


def get_two_entries(content: str, first: str, second: str) -> tuple[str, str]:
    entries = get_entries(content)
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    if len(entries) < 2:
        raise MissingArgument(second if entries else first)
    return entries[0], entries[1]


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
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
    for line_index, line in enumerate(text.split("\n")):
        line_separator = "\n" if line_index else ""
        if len(line) <= limit:
            yield line_separator, line
            continue

        for word_index, word in enumerate(line.split(" ")):
            separator = " " if word_index else line_separator
            for start in range(0, len(word), limit):
                yield separator if start == 0 else "", word[start : start + limit]
