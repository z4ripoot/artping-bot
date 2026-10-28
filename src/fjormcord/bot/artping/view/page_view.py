import logging
import re
from collections.abc import Awaitable, Callable

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.service import art_ping_service, character_service, currency_service  # Modules: cycle
from fjormcord.bot.artping.view.layout import to_view


class PageButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"page:(?P<kind>scoreboard|pings|character):(?P<subject_id>\d+):(?P<page>\d+)",
):
    # Previous or Next under a paged list: turns the clicked message to the page in its custom_id. kind names the list
    # and subject_id whose it is: the currency of a scoreboard, the user of a ping list, the character of its list of
    # subscribers. IDs, not names, keep the custom_id short and survive a rename. Registered with
    # Client.add_dynamic_items, so a click is handled after a restart too
    def __init__(self, kind: str, subject_id: int, page: int, label: str, disabled: bool = False):
        super().__init__(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"page:{kind}:{subject_id}:{page}",
                disabled=disabled,
            )
        )
        self.kind = kind
        self.subject_id = subject_id
        self.page = page

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls(match["kind"], int(match["subject_id"]), int(match["page"]), item.label, item.disabled)

    async def callback(self, interaction: discord.Interaction):
        await show_page(
            interaction,
            lambda: _render(self.kind, interaction.client, self.subject_id, self.page),
            "Something went wrong while turning the page",
        )


def page_buttons(kind: str, subject_id: int, page: int, page_count: int) -> tuple[PageButton, ...]:
    # None for a single page; otherwise Previous and Next, disabled on the first and the last page
    if page_count == 1:
        return ()
    return (
        PageButton(kind, subject_id, page - 1, "◀ Previous", disabled=page == 1),
        PageButton(kind, subject_id, page + 1, "Next ▶", disabled=page == page_count),
    )


async def show_page(
    interaction: discord.Interaction,
    render: Callable[[], Awaitable[Layout]],
    failure: str,
    redraw: Callable[[], Awaitable[Layout]] | None = None,
):
    # Edits the clicked message to what render lays out. A click on a page is a command, so it has the cooldown; anyone
    # who sees the message may click. Errors are answered privately and leave the message as it was, drawn again by
    # redraw when given: a dropdown keeps showing a refused pick until its message is edited
    try:
        with interaction.client.cooldowns.command(interaction.user):
            # Looking up the users may take longer than the 3 seconds Discord waits for an answer
            await interaction.response.defer()
            layout = await render()
    except CommandError as e:
        logging.warning(str(e))
        await _answer_privately(interaction, str(e))
        await _redraw(interaction, redraw)
        return
    except Exception:
        logging.exception("Showing a page of message %s failed", interaction.message.id)
        await _answer_privately(interaction, failure)
        await _redraw(interaction, redraw)
        return

    await interaction.edit_original_response(content=None, view=to_view(layout))


def shown_page(message: discord.Message) -> int:
    # The page a message shows, read from its Previous button, which leads to the page before; 1 without page buttons
    components = list(message.components)
    while components:
        component = components.pop(0)
        match = PageButton.__discord_ui_compiled_template__.fullmatch(getattr(component, "custom_id", None) or "")
        if match:
            return int(match["page"]) + 1
        components += getattr(component, "children", [])
    return 1


async def _render(kind: str, client: discord.Client, subject_id: int, page: int) -> Layout:
    # The service is looked up when clicked, as it imports this module too
    match kind:
        case "scoreboard":
            return await currency_service.get_scoreboard_page(client, subject_id, page)
        case "pings":
            return await art_ping_service.check_ping_page(client, subject_id, page)
        case "character":
            return await character_service.check_character_page(client, subject_id, page)
    raise ValueError(f"Unknown page kind {kind}")


async def _answer_privately(interaction: discord.Interaction, text: str):
    # Logged when Discord no longer takes an answer, e.g. when the defer itself failed for an expired click
    try:
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)
    except discord.HTTPException as e:
        logging.warning("Could not answer the click on message %s. %s", interaction.message.id, e)


async def _redraw(interaction: discord.Interaction, redraw: Callable[[], Awaitable[Layout]] | None):
    # Edited as the bot's own message, since the answer to the click may have been a new, private message
    if redraw is None:
        return
    try:
        await interaction.message.edit(content=None, view=to_view(await redraw()))
    except Exception:
        logging.exception("Redrawing message %s failed", interaction.message.id)
