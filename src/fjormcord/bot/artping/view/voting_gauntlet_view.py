import re

import discord

from fjormcord.bot.artping.model.voting_gauntlet import Entrant
from fjormcord.bot.artping.service import voting_gauntlet_service
from fjormcord.bot.artping.util.interaction_util import answer_click


class TrackButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"voting_gauntlet:(?P<tournament_id>\d+):(?P<name>[^:]+):(?P<opponent>[^:]+)",
):
    # "Track <name>" under a matchup message. The gauntlet and both names are in the custom_id, so a click is
    # handled after a restart too: the class is registered with Client.add_dynamic_items, and discord.py rebuilds
    # the button from the custom_id of whatever message was clicked.
    def __init__(self, tournament_id: int, name: str, opponent: str):
        super().__init__(
            discord.ui.Button(
                label=f"Track {name}",
                style=discord.ButtonStyle.primary,
                custom_id=f"voting_gauntlet:{tournament_id}:{name}:{opponent}",
            )
        )
        self.tournament_id = tournament_id
        self.name = name
        self.opponent = opponent

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls(int(match["tournament_id"]), match["name"], match["opponent"])

    async def callback(self, interaction: discord.Interaction):
        await answer_click(
            self,
            interaction,
            lambda: voting_gauntlet_service.toggle_tracking(
                self.tournament_id, str(interaction.user.id), self.name, self.opponent
            ),
            "Something went wrong while tracking",
        )


def track_buttons(tournament_id: int, matchup: tuple[Entrant, Entrant]) -> tuple[TrackButton, TrackButton]:
    # The two Track buttons of a matchup, in the site's order
    first, second = matchup
    return TrackButton(tournament_id, first.name, second.name), TrackButton(tournament_id, second.name, first.name)
