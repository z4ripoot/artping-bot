import inspect
import logging
from collections.abc import Awaitable, Callable

import discord
from discord import app_commands

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS, split_message
from fjormcord.bot.artping.util.user_util import is_administrator


def admin_command(name: str, description: str):
    # An admin command: Discord hides it from non-admins and outside servers, and run checks it again, since server
    # admins can change who sees a command
    def decorator(callback) -> app_commands.Command:
        command = app_commands.command(name=name, description=description)(callback)
        return app_commands.guild_only()(app_commands.default_permissions(administrator=True)(command))
    return decorator


def _is_admin_command(interaction: discord.Interaction) -> bool:
    permissions = getattr(interaction.command, "default_permissions", None)
    return permissions is not None and permissions.administrator


async def run(interaction: discord.Interaction, command_name: str, call: Callable[[], str | Awaitable[str]], *,
              defer: bool = False, allowed_mentions: discord.AllowedMentions = ALLOWED_MENTIONS) -> None:
    # Runs a slash command the way legacy.dispatch runs a ~ command: checks, the call, and the reply. call does the
    # command's work and returns the reply, directly or as a coroutine; it raises CommandError to turn the user down.
    try:
        if _is_admin_command(interaction) and not is_administrator(interaction.user):
            raise CommandError("This command is for admins only")
        # One cooldown per user, shared with the ~ commands
        interaction.client.cooldowns.check(interaction.user.id)

        if defer:
            await interaction.response.defer()
        out = call()
        if inspect.isawaitable(out):
            out = await out
        # Only a command that succeeded starts the cooldown, so a mistake can be corrected right away
        _start_cooldown(interaction)
    except CommandError as e:
        logging.warning(str(e))
        await _send(interaction, str(e), ephemeral=True)
        return
    except Exception:
        logging.exception("Command /%s failed", command_name)
        await _send(interaction, f"Something went wrong while running /{command_name}", ephemeral=True)
        return

    # Replies longer than Discord allows are sent as several messages; an empty reply sends nothing
    for chunk in split_message(out):
        await _send(interaction, chunk, allowed_mentions=allowed_mentions)


async def _send(interaction: discord.Interaction, text: str, ephemeral: bool = False,
                allowed_mentions: discord.AllowedMentions = ALLOWED_MENTIONS):
    # The first message answers the interaction, or follows up on the defer; the rest are follow-ups
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=ephemeral, allowed_mentions=allowed_mentions)
    else:
        await interaction.response.send_message(text, ephemeral=ephemeral, allowed_mentions=allowed_mentions)


def _start_cooldown(interaction: discord.Interaction):
    # Admins never get a cooldown, so checking it doesn't have to exempt them
    if not is_administrator(interaction.user):
        interaction.client.cooldowns.start(interaction.user.id)
