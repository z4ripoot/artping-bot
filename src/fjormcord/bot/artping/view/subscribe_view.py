import logging
import re

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.service import art_ping_service  # A module: it imports this one too, via character_service


class SubscribeButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"subscribe:(?P<character_id>\d+)",
):
    # "Subscribe to <name>" under the message that announces a new character. The character's ID is in the
    # custom_id, so the button keeps working after a restart (registered with Client.add_dynamic_items) and after the
    # character is renamed. It only subscribes; a click is not a command, so it has no cooldown
    def __init__(self, character_id: int, label: str):
        super().__init__(
            discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=f"subscribe:{character_id}")
        )
        self.character_id = character_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls(int(match["character_id"]), item.label)

    async def callback(self, interaction: discord.Interaction):
        try:
            reply = art_ping_service.subscribe(str(interaction.user.id), self.character_id)
        except CommandError as e:
            logging.warning(str(e))
            reply = str(e)
        except Exception:
            logging.exception("Subscribing to character %s failed", self.character_id)
            reply = "Something went wrong while subscribing"
        await interaction.response.send_message(reply, ephemeral=True)

    @classmethod
    def for_character(cls, character: Character) -> "SubscribeButton":
        # Discord allows labels of 80 characters at most
        return cls(character.id, f"Subscribe to {character.name}"[:80])
