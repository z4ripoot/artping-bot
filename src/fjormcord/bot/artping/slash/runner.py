import logging
from collections.abc import Awaitable, Callable

import discord
from discord import app_commands

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.model.reply import Reply
from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS, await_reply
from fjormcord.bot.artping.util.user_util import is_administrator
from fjormcord.bot.artping.view.layout import message_options


def admin_command(name: str, description: str):
    # An admin command: Discord hides it from non-admins and outside servers, and run checks it again, since server
    # admins can change who sees a command
    def decorator(callback: Callable) -> app_commands.Command:
        command = app_commands.command(name=name, description=description)(callback)
        return app_commands.guild_only()(app_commands.default_permissions(administrator=True)(command))

    return decorator


def _is_admin_command(interaction: discord.Interaction) -> bool:
    permissions = getattr(interaction.command, "default_permissions", None)
    return permissions is not None and permissions.administrator


async def run(
    interaction: discord.Interaction,
    call: Callable[[], str | Reply | Layout | Awaitable[str | Reply | Layout]],
    *,
    defer: bool = False,
    ephemeral: bool = False,
    allowed_mentions: discord.AllowedMentions = ALLOWED_MENTIONS,
) -> None:
    # Runs a slash command the way legacy.dispatch runs a ~ command: checks, the call, and the reply. call does the
    # command's work and returns the reply, directly or as a coroutine; it raises CommandError to turn the user down.
    # ephemeral makes the reply private, and the defer's placeholder with it.
    try:
        if _is_admin_command(interaction) and not is_administrator(interaction.user):
            raise CommandError("This command is for admins only")
        # One cooldown per user, shared with the ~ commands
        with interaction.client.cooldowns.command(interaction.user):
            if defer:
                await interaction.response.defer(**({"ephemeral": True} if ephemeral else {}))
            out = await await_reply(call())
    except CommandError as e:
        logging.warning(str(e))
        await _send_error(interaction, e.layout or str(e))
        return
    except Exception:
        command_name = interaction.command.name
        logging.exception("Command /%s failed", command_name)
        await _send_error(interaction, f"Something went wrong while running /{command_name}")
        return

    # Replies longer than Discord allows are sent as several messages; an empty reply sends nothing
    for options in message_options(out):
        await _send(interaction, options, ephemeral=ephemeral, allowed_mentions=allowed_mentions)


async def _send_error(interaction: discord.Interaction, error: str | Layout):
    # The first follow-up after a public defer replaces its "is thinking" placeholder and would show the error to
    # everyone, so the placeholder is deleted first. A follow-up that already replaced it (a vote message) stays.
    if interaction.response.is_done():
        try:
            if (await interaction.original_response()).flags.loading:
                await interaction.delete_original_response()
        except discord.HTTPException:
            logging.exception("Could not delete the deferred reply of /%s", interaction.command.name)
    for options in message_options(error):
        await _send(interaction, options, ephemeral=True)


async def _send(
    interaction: discord.Interaction,
    options: dict,
    ephemeral: bool = False,
    allowed_mentions: discord.AllowedMentions = ALLOWED_MENTIONS,
):
    # One message, its content or view as message_options gives them. The first message answers the interaction, or
    # follows up on the defer; the rest are follow-ups
    options = {**options, "ephemeral": ephemeral, "allowed_mentions": allowed_mentions}
    if interaction.response.is_done():
        await interaction.followup.send(**options)
    else:
        await interaction.response.send_message(**options)
