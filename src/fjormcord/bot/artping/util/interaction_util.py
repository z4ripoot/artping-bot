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
    # A click that only gets a private answer: call's reply, a CommandError's message, or failure when anything else
    # goes wrong. defer for a call that may take longer than the 3 seconds Discord waits for an answer
    if defer:
        await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        reply = await await_reply(call())
    except CommandError as e:
        logging.warning(str(e))
        reply = str(e)
    except Exception:
        # Answered here, since after a defer the view's on_error would only log and leave the clicker waiting
        logging.exception("The click on %s failed", item.custom_id)
        reply = failure
    await answer_privately(interaction, reply)


async def answer_privately(interaction: discord.Interaction, text: str):
    # Logged when Discord no longer takes an answer, e.g. when the defer itself failed for an expired click
    try:
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)
    except discord.HTTPException as e:
        logging.warning("Could not answer the click on %s. %s", getattr(interaction.message, "id", None), e)


def walk_components(components: Iterable) -> Iterator:
    # A message's components at any depth of its layout, in the order they are shown
    for component in components:
        yield component
        yield from walk_components(getattr(component, "children", []))
