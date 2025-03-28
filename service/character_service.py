import logging
import discord

from repository import character_repository
from repository.art_ping_repository import get_art_ping_users
from repository.character_repository import get_character_name, add_character, get_character_row
from util.message_util import get_first


def add_character_ping(message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to add character"
        logging.warning(out)
        return out

    if get_character_name(entry):
        out = f"Failed to add character {entry}. Character {entry} already exists"
        logging.warning(out)
        return out

    logging.info("Adding character %s", entry)

    is_added = add_character(entry)

    if is_added:
        out = f"{entry} has been added"
        logging.warning(out)
        return out
    else:
        out = f"Failed to add character {entry}"
        logging.warning(out)
        return out


def remove_character(message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = f"Failed to remove character"
        logging.warning(out)
        return out

    character = get_character_name(entry)

    if character is None:
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    logging.info("Removing character %s", character)

    is_removed = character_repository.remove_character(character)

    if is_removed:
        out = f"{character} has been removed"
        logging.info(out)
        return out
    else:
        out = f"Failed to remove character {character}"
        logging.warning(out)
        return out


async def check_character(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to check character"
        logging.warning(out)
        return out

    logging.info("Checking for character %s", entry)

    characters = get_character_row(entry)

    if characters is None:
        out = f"Failed to check character {entry}"
        logging.warning(out)
        return out

    character_id = characters[0]
    character_name = characters[1]

    logging.info("Character %s has been found", character_name)

    user_ids = get_art_ping_users((character_id,))
    usernames = []

    for userId in user_ids:
        try:
            user: discord.User = await client.fetch_user(userId)
            usernames.append(user.global_name)
        except (Exception,):
            continue

    if character_id:
        user_list = ", ".join(usernames)
        return f"Character entry found for {character_name}\n" \
            + f"Users: {user_list}"
    else:
        return f"Failed to check character {entry}"
