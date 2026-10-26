import inspect
import logging
import math
from collections.abc import Awaitable, Callable

import discord

from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS, CommandError, split_message
from fjormcord.bot.artping.util.user_util import is_administrator


async def run(interaction: discord.Interaction, command_name: str, call: Callable[[], str | Awaitable[str]], *,
              admin_only: bool = False, cooldown_seconds: float = 0, defer: bool = False,
              allowed_mentions: discord.AllowedMentions = ALLOWED_MENTIONS) -> None:
    # Runs a slash command the way legacy.dispatch runs a ~ command: checks, the call, and the reply. call does the
    # command's work and returns the reply, directly or as a coroutine; it raises CommandError to turn the user down.
    try:
        if admin_only and not is_administrator(interaction.user):
            raise CommandError("This command is for admins only")
        _check_cooldown(interaction, command_name)

        if defer:
            await interaction.response.defer()
        out = call()
        if inspect.isawaitable(out):
            out = await out
        # Only a command that succeeded starts the cooldown, so a mistake can be corrected right away
        _start_cooldown(interaction, command_name, cooldown_seconds)
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


def _check_cooldown(interaction: discord.Interaction, command_name: str):
    # Turns the command down while the user's cooldown for it runs; shared with the ~ command of the same name
    remaining = interaction.client.cooldowns.remaining(command_name, interaction.user.id)
    if remaining > 0:
        seconds = math.ceil(remaining)
        raise CommandError(
            f"You used /{command_name} recently. Try again in {seconds} second{'' if seconds == 1 else 's'}")


def _start_cooldown(interaction: discord.Interaction, command_name: str, cooldown_seconds: float):
    # Admins never get a cooldown, so _check_cooldown doesn't have to exempt them
    if cooldown_seconds > 0 and not is_administrator(interaction.user):
        interaction.client.cooldowns.start(command_name, interaction.user.id, cooldown_seconds)
