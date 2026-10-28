import asyncio
import html
import logging
import re
from datetime import datetime, time, timedelta, timezone

import aiohttp
import discord
from discord.ext import tasks

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.voting_gauntlet import Entrant, Round
from fjormcord.bot.artping.service import voting_gauntlet_service
from fjormcord.bot.artping.util.message_util import split_message
from fjormcord.bot.artping.util.task_util import get_task_channel, start_channel_task
from fjormcord.bot.artping.util.user_util import mentions
from fjormcord.bot.artping.view.voting_gauntlet_view import TrackView

# Redirects to the page of the latest gauntlet, e.g. /voting_gauntlet/tournaments/112. There is no API, so the page's
# HTML is read; the redirect drops a query, so the language and timezone are added to the page it redirects to
CURRENT_URL = "https://support.fire-emblem-heroes.com/voting_gauntlet/current"
PAGE_QUERY = {"locale": "en-US", "timezone": "Etc/UTC"}
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)
TOURNAMENT_PATTERN = re.compile(r"/tournaments/(\d+)$")

# The site counts the votes at the top of every hour; a few minutes later the new scores are on the page
POSTING_TIMES = [time(hour=hour, minute=5, tzinfo=timezone.utc) for hour in range(24)]

ROUND_PATTERN = re.compile(r'<article class="body-section-tournament">(.*?)</article>', re.DOTALL)
WINDOW_PATTERN = re.compile(r'<div class="tournaments-date">([^<]*)</div>')
# A character's picture, then its name and score. The picture's class ends in its status: normal or behind
ENTRANT_PATTERN = re.compile(
    r'<div class="tournaments-art-(?:left|right) art-\d+-\d+-(\w+)">'
    r'.*?<p class="name">([^<]*)</p><p>([\d,]+)</p>',
    re.DOTALL,
)
STATUSES = {"normal": False, "behind": True}
# One end of a round's window, e.g. "10/5 at 7:00 a.m."
TIME_PATTERN = re.compile(r"(\d{1,2})/(\d{1,2}) at (\d{1,2}):(\d{2}) ([ap])\.m\.")


def start_voting_gauntlet_notification(client: discord.Client):
    start_channel_task(
        task_voting_gauntlet_scores, client, config.read_settings().voting_gauntlet_channel_id, "Voting Gauntlet scores"
    )


@tasks.loop(time=POSTING_TIMES)
async def task_voting_gauntlet_scores(client: discord.Client):
    try:
        current_time = now()
        tournament_id, page = await fetch_page()
        rounds = parse_rounds(page, current_time)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        # An exception would stop the loop; the next hour tries again
        logging.exception("Voting Gauntlet scores could not be read. Task will be skipped")
        return

    running = next((round_ for round_ in rounds if round_.start <= current_time < round_.end), None)
    if running is None:
        # Rounds are listed once they start, latest first; the final one has a single matchup
        latest = rounds[0]
        if len(latest.matchups) == 1 and current_time >= latest.end:
            voting_gauntlet_service.end_gauntlet()
        return

    voting_gauntlet_service.start_gauntlet(tournament_id)
    channel = get_task_channel(client, config.read_settings().voting_gauntlet_channel_id)
    if channel is None:
        return
    for matchup in running.matchups:
        trackers = [
            user_id
            for entrant in matchup
            if entrant.behind
            for user_id in voting_gauntlet_service.get_trackers(tournament_id, entrant.name)
        ]
        try:
            *parts, last = split_message(format_matchup(matchup, trackers))
            for part in parts:
                await channel.send(part)
            await channel.send(last, view=TrackView(tournament_id, matchup))
        except discord.DiscordException:
            # The other matchups are still posted
            logging.exception("Posting the Voting Gauntlet matchup of %s failed", matchup[0].name)


def now() -> datetime:
    return datetime.now(timezone.utc)


async def fetch_page() -> tuple[int, str]:
    # The tournament number of the latest gauntlet, and its page
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        async with session.get(CURRENT_URL) as response:
            response.raise_for_status()
            page_url = response.url
        tournament = TOURNAMENT_PATTERN.search(page_url.path)
        if tournament is None:
            raise ValueError(f"Not a tournament page: {page_url}")
        async with session.get(page_url.with_query(PAGE_QUERY)) as response:
            response.raise_for_status()
            return int(tournament.group(1)), await response.text()


def parse_rounds(page: str, current_time: datetime) -> list[Round]:
    # The rounds that have started, latest first; raises ValueError when the page doesn't look as expected
    rounds = []
    for section in ROUND_PATTERN.findall(page):
        window = WINDOW_PATTERN.search(section)
        if window is None:
            raise ValueError("Round without a date")
        start, end = parse_window(window.group(1), current_time)
        matchups = [_parse_matchup(battle) for battle in section.split('<li class="tournaments-battle">')[1:]]
        rounds.append(Round(start, end, matchups))
    if not rounds:
        raise ValueError("No rounds on the page")
    return rounds


def _parse_matchup(battle: str) -> tuple[Entrant, Entrant]:
    entrants = []
    for status, name, score in ENTRANT_PATTERN.findall(battle):
        if status not in STATUSES:
            raise ValueError(f"Unknown status {status} of {name}")
        entrants.append(Entrant(html.unescape(name), int(score.replace(",", "")), STATUSES[status]))
    if len(entrants) != 2:
        raise ValueError(f"Matchup with {len(entrants)} entrants")
    if entrants[0].behind and entrants[1].behind:
        raise ValueError(f"Both {entrants[0].name} and {entrants[1].name} are behind")
    return entrants[0], entrants[1]


def parse_window(window: str, current_time: datetime) -> tuple[datetime, datetime]:
    # E.g. "10/5 at 7:00 a.m.~10/7 at 3:59 a.m. UTC"; the end returned is the minute after the last one
    if not window.endswith(" UTC"):
        raise ValueError(f"Round date not in UTC: {window}")
    times = TIME_PATTERN.findall(window)
    if len(times) != 2:
        raise ValueError(f"Unreadable round date: {window}")
    start, last_minute = (_to_datetime(*parts, current_time) for parts in times)
    return start, last_minute + timedelta(minutes=1)


def _to_datetime(month: str, day: str, hour: str, minute: str, half: str, current_time: datetime) -> datetime:
    hour_24 = int(hour) % 12 + (12 if half == "p" else 0)
    # The page leaves out the year: take the one closest to now, so a round over New Year is read right
    candidates = []
    for year in (current_time.year - 1, current_time.year, current_time.year + 1):
        try:
            candidates.append(datetime(year, int(month), int(day), hour_24, int(minute), tzinfo=timezone.utc))
        except ValueError:
            # 2/29 outside a leap year
            pass
    if not candidates:
        raise ValueError(f"Invalid round date: {month}/{day}")
    return min(candidates, key=lambda candidate: abs(candidate - current_time))


def format_matchup(matchup: tuple[Entrant, Entrant], trackers: list[str]) -> str:
    # In the site's order, labelled as in the game; the trackers of the Weaker character are mentioned below
    lines = []
    for entrant, opponent in (matchup, matchup[::-1]):
        lines += [f"{entrant.name} ({_status(entrant, opponent)})", f"{entrant.score:,}"]
    if trackers:
        lines.append(mentions(trackers))
    return "\n".join(lines)


def _status(entrant: Entrant, opponent: Entrant) -> str:
    if entrant.behind:
        return "Weaker"
    return "Stronger" if opponent.behind else "Same"
