import logging
import re

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.resource import Resource
from fjormcord.bot.artping.repository import resource_repository
from fjormcord.bot.artping.util.message_util import logged

# Plain ASCII, so names are easy to type and can't hold mention syntax
_RESOURCE_NAME = re.compile(r"[A-Za-z0-9_-]+")
# https://discord.com/channels/<server>/<channel>/<message>, also from the test clients and the old domain
_DISCORD_MESSAGE_LINK = re.compile(r"https://(?:(?:ptb|canary)\.)?discord(?:app)?\.com/channels/(?:\d+|@me)/(\d+)/(\d+)")
_WEBSITE_LINK = re.compile(r"https?://\S+")


def _parse_name(entry: str) -> str:
    # ~setresource ~hof works too
    name = entry.removeprefix("~")
    if not _RESOURCE_NAME.fullmatch(name):
        raise CommandError("Resource names can only contain letters, digits, _ and -")
    return name


def _require_not_a_command(name: str):
    # Imported here: commands imports this module for its handlers
    from fjormcord.bot.artping.legacy.commands import COMMAND_PREFIX, COMMANDS_BY_NAME

    command_name = COMMAND_PREFIX + name.lower()
    if command_name in COMMANDS_BY_NAME:
        raise CommandError(f"{command_name} is a command, so it can't be a resource")


async def _get_content(client: discord.Client, link: str) -> str:
    # The text of a linked Discord message as it is now, or a website link itself
    match = _DISCORD_MESSAGE_LINK.fullmatch(link)
    if match:
        channel_id, message_id = int(match[1]), int(match[2])
        try:
            linked = await client.get_partial_messageable(channel_id).fetch_message(message_id)
        except discord.HTTPException as e:
            logging.warning("Failed to fetch message %s. %s", link, e)
            raise CommandError("Couldn't read that message. Check the link, and that the bot can read that channel")
        # Messages with only images or files, and forwarded messages, have no text of their own
        if not linked.content:
            raise CommandError("That message has no text")
        return linked.content

    if _WEBSITE_LINK.fullmatch(link):
        return link

    raise CommandError("That isn't a link to a Discord message or a website")


async def set_resource(client: discord.Client, name: str, link: str) -> str:
    name = _parse_name(name)
    _require_not_a_command(name)
    # <link> keeps Discord from showing a preview of the link in the admin's own message
    link = link.removeprefix("<").removesuffix(">")

    resource_repository.set_resource(Resource(name, await _get_content(client, link), link))

    return logged(f"Resource {name} has been set")


def remove_resource(name: str) -> str:
    name = _parse_name(name)

    resource = resource_repository.get_resource(name)
    if resource is None:
        raise CommandError(f"Resource {name} doesn't exist")

    resource_repository.remove_resource(resource.name)

    return logged(f"Resource {resource.name} has been removed")


def list_resources(slash: bool = False) -> str:
    names = resource_repository.get_resource_names()

    if not names:
        return "No resources have been set yet"

    if slash:
        return "Resources: " + ", ".join(names) + " (post one with /resource)"
    return "Resources: " + ", ".join(f"~{name}" for name in names)


def post_resource(name: str) -> str:
    content = get_resource_content(name)
    if content is None:
        raise CommandError(f"Resource {name} doesn't exist")
    return content


def get_resource_content(name: str) -> str | None:
    # What ~<name> posts; None when there is no such resource
    resource = resource_repository.get_resource(name)
    return resource.content if resource else None
