import logging

import discord

# Arguments are split on whitespace, so names of several words are written with underscores
MULTI_WORD_HINT = "Use underscores for multi-word names, e.g. Black_Knight"
MESSAGE_ONE_NAME_ONLY = f"Only one name is allowed. {MULTI_WORD_HINT}"
# Replies echo user input, so never let a message trigger @everyone/@here or role pings
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)
# Discord rejects messages longer than this
MAX_MESSAGE_LENGTH = 2000


class MissingArgument(Exception):
    # Raised by a handler; the client answers with what is missing and the command's usage from ~help
    def __init__(self, argument):
        super().__init__(f"{argument} is missing")
        self.argument = argument


class CommandError(Exception):
    # Raised by a handler to turn a command down; the client logs the message and sends it as the reply
    pass


def logged(reply):
    # Logs the reply of a command that changed something, and returns it
    logging.info(reply)
    return reply


def get_entries(content):
    # Everything after the command, empty when there is nothing; split() also ignores repeated whitespace
    return content.split()[1:]


def get_single_name(content, argument):
    # For commands that take exactly one name; argument says what it is, e.g. "character name"
    entries = get_entries(content)
    if not entries:
        raise MissingArgument(argument)
    if len(entries) > 1:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    return entries[0]


def get_two_entries(content, first, second):
    # For commands that take exactly two arguments; first and second say what they are, e.g. "currency name", "amount"
    entries = get_entries(content)
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    if len(entries) < 2:
        raise MissingArgument(second if entries else first)
    return entries[0], entries[1]


# Splits text into chunks within Discord's message length limit; each chunk is sent as a separate message
def split_message(text, limit=MAX_MESSAGE_LENGTH):
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


def _pieces(text, limit):
    # Yields (separator, piece) pairs, each piece at most limit long
    for line_index, line in enumerate(text.split("\n")):
        line_separator = "\n" if line_index else ""
        if len(line) <= limit:
            yield line_separator, line
            continue

        for word_index, word in enumerate(line.split(" ")):
            separator = " " if word_index else line_separator
            for start in range(0, len(word), limit):
                yield separator if start == 0 else "", word[start:start + limit]
