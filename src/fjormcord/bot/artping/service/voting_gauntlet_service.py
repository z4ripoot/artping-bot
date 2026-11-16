import logging

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.voting_gauntlet import Entrant
from fjormcord.bot.artping.repository import voting_gauntlet_repository
from fjormcord.bot.artping.util.message_util import log_and_reply

MESSAGE_ENDED = "This Voting Gauntlet has ended"


async def send_scores(client: discord.Client) -> str:
    # Imported here: voting_gauntlet imports this module
    from fjormcord.bot.artping import voting_gauntlet

    if config.read_settings().voting_gauntlet_channel_id is None:
        return "No channel is configured for the Voting Gauntlet scores"
    return log_and_reply(await voting_gauntlet.post_scores(client))


def start_gauntlet(tournament_id: int, entrants: list[Entrant]):
    voting_gauntlet_repository.set_running_tournament(tournament_id, entrants)


def end_gauntlet():
    # Called every hour after the final round, so only an ended gauntlet that is still stored is removed and logged
    tournament_id = voting_gauntlet_repository.get_running_tournament()
    if tournament_id is None:
        return
    logging.info("Voting Gauntlet %s has ended; removing it and its trackers", tournament_id)
    voting_gauntlet_repository.remove_running_tournament()


def get_trackers(tournament_id: int, slot: int) -> list[str]:
    return voting_gauntlet_repository.get_trackers(tournament_id, slot)


def toggle_tracking(tournament_id: int, user_id: str, slot: int, opponent_slot: int) -> str:
    if voting_gauntlet_repository.get_running_tournament() != tournament_id:
        return MESSAGE_ENDED

    name = voting_gauntlet_repository.get_entrant_name(tournament_id, slot)
    opponent = voting_gauntlet_repository.get_entrant_name(tournament_id, opponent_slot)
    if name is None or opponent is None:
        return MESSAGE_ENDED

    if voting_gauntlet_repository.has_tracker(tournament_id, user_id, slot):
        voting_gauntlet_repository.remove_tracker(tournament_id, user_id, slot)
        return log_and_reply(f"You no longer track {name}")

    switched = voting_gauntlet_repository.has_tracker(tournament_id, user_id, opponent_slot)
    voting_gauntlet_repository.add_tracker(tournament_id, user_id, slot, opponent_slot)
    instead = f" instead of {opponent}" if switched else ""
    return log_and_reply(f"You now track {name}{instead}. You'll be pinged every hour when {name} is Weaker")
