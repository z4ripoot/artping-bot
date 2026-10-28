import logging
import re

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.reply import Reply
from fjormcord.bot.artping.service import currency_service  # A module: it imports this one too


class PageButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"scoreboard:(?P<currency_id>\d+):(?P<page>\d+)",
):
    # Previous or Next under a scoreboard: turns the clicked message to the page in its custom_id. The currency's ID,
    # not its name, is in it, so the custom_id stays short. Registered with Client.add_dynamic_items, so a click is
    # handled after a restart too
    def __init__(self, currency_id: int, page: int, label: str, disabled: bool = False):
        super().__init__(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"scoreboard:{currency_id}:{page}",
                disabled=disabled,
            )
        )
        self.currency_id = currency_id
        self.page = page

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls(int(match["currency_id"]), int(match["page"]), item.label, item.disabled)

    async def callback(self, interaction: discord.Interaction):
        # Turning the page is a command, so it has the cooldown; anyone who sees the scoreboard may turn it
        try:
            with interaction.client.cooldowns.command(interaction.user):
                # Looking up the users may take longer than the 3 seconds Discord waits for an answer
                await interaction.response.defer()
                reply = await currency_service.get_scoreboard_page(interaction.client, self.currency_id, self.page)
        except CommandError as e:
            logging.warning(str(e))
            await _answer_privately(interaction, str(e))
            return
        except Exception:
            logging.exception("Turning scoreboard %s to page %s failed", self.currency_id, self.page)
            await _answer_privately(interaction, "Something went wrong while turning the page")
            return

        # A scoreboard that shrank to one page loses its buttons
        if isinstance(reply, Reply):
            await interaction.edit_original_response(content=reply.content, view=reply.view)
        else:
            await interaction.edit_original_response(content=reply, view=None)


class ScoreboardView(discord.ui.View):
    # Previous and Next under a scoreboard of several pages, disabled on the first and last page; no timeout, so they
    # don't stop working
    def __init__(self, currency_id: int, page: int, page_count: int):
        super().__init__(timeout=None)
        self.add_item(PageButton(currency_id, page - 1, "◀ Previous", disabled=page == 1))
        self.add_item(PageButton(currency_id, page + 1, "Next ▶", disabled=page == page_count))


async def _answer_privately(interaction: discord.Interaction, text: str):
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True)
    else:
        await interaction.response.send_message(text, ephemeral=True)
