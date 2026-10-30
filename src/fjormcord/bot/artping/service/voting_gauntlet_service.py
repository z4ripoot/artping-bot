import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.repository import voting_gauntlet_repository
from fjormcord.bot.artping.util.message_util import log_info

MESSAGE_ENDED = "This Voting Gauntlet has ended"


async def send_scores(client: discord.Client) -> str:
    # A debug command: posts the scores now, as the hourly task does, so only while a round runs
    # Imported here: voting_gauntlet imports this module for the tracking
    from fjormcord.bot.artping import voting_gauntlet

    if config.read_settings().voting_gauntlet_channel_id is None:
        return "No channel is configured for the Voting Gauntlet scores"
    return log_info(await voting_gauntlet.post_scores(client))


def start_gauntlet(tournament_id: int):
    # Called while a round runs; the trackers of an older gauntlet are removed
    voting_gauntlet_repository.set_running_tournament(tournament_id)


def end_gauntlet():
    voting_gauntlet_repository.remove_running_tournament()


def get_trackers(tournament_id: int, name: str) -> list[str]:
    return voting_gauntlet_repository.get_trackers(tournament_id, name)


def toggle_tracking(tournament_id: int, user_id: str, name: str, opponent: str) -> str:
    # A click on "Track <name>" in the matchup of name and opponent
    if voting_gauntlet_repository.get_running_tournament() != tournament_id:
        return MESSAGE_ENDED
    if voting_gauntlet_repository.has_tracker(tournament_id, user_id, name):
        voting_gauntlet_repository.remove_tracker(tournament_id, user_id, name)
        return log_info(f"You no longer track {name}")

    switched = voting_gauntlet_repository.has_tracker(tournament_id, user_id, opponent)
    voting_gauntlet_repository.add_tracker(tournament_id, user_id, name, opponent)
    instead = f" instead of {opponent}" if switched else ""
    return log_info(f"You now track {name}{instead}. You'll be pinged every hour {name} is Weaker")
