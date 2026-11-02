import asyncio
import logging

import discord
from discord import app_commands


def registered_commands(tree: app_commands.CommandTree, guild_id: int | None) -> list[app_commands.Command]:
    guild = discord.Object(id=guild_id) if guild_id is not None else None
    return [command for command in tree.get_commands(guild=guild) if isinstance(command, app_commands.Command)]


async def sync_commands(tree: app_commands.CommandTree, guild_id: int | None) -> None:
    try:
        if guild_id is None:
            await tree.sync()
            return

        guild = discord.Object(id=guild_id)
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        tree.clear_commands(guild=None)
        await tree.sync()
    except (discord.DiscordException, OSError, asyncio.TimeoutError):
        logging.exception("Syncing the slash commands failed")
