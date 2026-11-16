import re

import discord

from fjormcord.bot.artping.model.voting_gauntlet import Entrant
from fjormcord.bot.artping.service import voting_gauntlet_service
from fjormcord.bot.artping.util.interaction_util import answer_click


class TrackButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"voting_gauntlet_track:(?P<tournament_id>\d+):(?P<slot>\d+):(?P<opponent_slot>\d+)",
):
    def __init__(self, tournament_id: int, slot: int, opponent_slot: int, label: str):
        super().__init__(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id=f"voting_gauntlet_track:{tournament_id}:{slot}:{opponent_slot}",
            )
        )
        self.tournament_id = tournament_id
        self.slot = slot
        self.opponent_slot = opponent_slot

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls(int(match["tournament_id"]), int(match["slot"]), int(match["opponent_slot"]), item.label)

    async def callback(self, interaction: discord.Interaction):
        await answer_click(
            self,
            interaction,
            lambda: voting_gauntlet_service.toggle_tracking(
                self.tournament_id, str(interaction.user.id), self.slot, self.opponent_slot
            ),
            "Something went wrong while tracking",
        )


def track_buttons(tournament_id: int, matchup: tuple[Entrant, Entrant]) -> tuple[TrackButton, TrackButton]:
    first, second = matchup
    return (
        TrackButton(tournament_id, first.slot, second.slot, f"Track {first.name}"),
        TrackButton(tournament_id, second.slot, first.slot, f"Track {second.name}"),
    )
