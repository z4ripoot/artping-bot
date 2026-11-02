import logging
from collections.abc import Awaitable, Callable, Iterable, Iterator

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.util.message_util import await_reply


async def answer_click(
    item: discord.ui.DynamicItem,
    interaction: discord.Interaction,
    call: Callable[[], str | Awaitable[str]],
    failure: str,
    *,
    defer: bool = False,
):
    if defer:
        await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        reply = await await_reply(call())
    except CommandError as e:
        logging.warning(str(e))
        reply = str(e)
    except Exception:
        logging.exception("The click on %s failed", item.custom_id)
        reply = failure
    await answer_privately(interaction, reply)


async def answer_privately(interaction: discord.Interaction, text: str):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)
    except discord.HTTPException as e:
        logging.warning("Could not answer the click on %s. %s", getattr(interaction.message, "id", None), e)


def walk_components(components: Iterable) -> Iterator:
    for component in components:
        yield component
        yield from walk_components(getattr(component, "children", []))
