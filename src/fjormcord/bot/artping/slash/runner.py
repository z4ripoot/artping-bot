import logging
from collections.abc import Awaitable, Callable

import discord
from discord import app_commands

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS, await_reply
from fjormcord.bot.artping.util.user_util import is_administrator
from fjormcord.bot.artping.view.layout import message_options


def admin_command(name: str, description: str):
    def decorator(callback: Callable) -> app_commands.Command:
        command = app_commands.command(name=name, description=description)(callback)
        return app_commands.guild_only()(app_commands.default_permissions(administrator=True)(command))

    return decorator


def is_admin_command(command: app_commands.Command | None) -> bool:
    permissions = getattr(command, "default_permissions", None)
    return permissions is not None and permissions.administrator


async def run(
    interaction: discord.Interaction,
    call: Callable[[], str | Layout | Awaitable[str | Layout]],
    *,
    defer: bool = False,
    ephemeral: bool = False,
    allowed_mentions: discord.AllowedMentions = ALLOWED_MENTIONS,
) -> None:
    try:
        if is_admin_command(interaction.command) and not is_administrator(interaction.user):
            raise CommandError("This command is for admins only")

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

    for options in message_options(out):
        await _send(interaction, options, ephemeral=ephemeral, allowed_mentions=allowed_mentions)


async def _send_error(interaction: discord.Interaction, error: str | Layout):
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
    options = {**options, "ephemeral": ephemeral, "allowed_mentions": allowed_mentions}
    if interaction.response.is_done():
        await interaction.followup.send(**options)
    else:
        await interaction.response.send_message(**options)
