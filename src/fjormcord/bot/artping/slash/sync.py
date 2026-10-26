import logging

import discord
from discord import app_commands


async def sync_commands(tree: app_commands.CommandTree, guild_id: int | None) -> None:
    # Registers the slash commands with Discord. With a guild they are registered there, which takes effect at once,
    # and the global copy is cleared so the commands don't show up twice. A failure is logged, never raised: the
    # bot still works, with the commands Discord already has.
    try:
        if guild_id is None:
            await tree.sync()
            return

        guild = discord.Object(id=guild_id)
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        tree.clear_commands(guild=None)
        await tree.sync()
    except discord.HTTPException:
        logging.exception("Syncing the slash commands failed")
