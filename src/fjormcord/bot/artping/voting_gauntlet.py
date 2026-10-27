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

# Redirects to the page of the latest gauntlet, e.g. /voting_gauntlet/tournaments/112. There is no API, so the page's
# HTML is read; the redirect drops a query, so the language and timezone are added to the page it redirects to
CURRENT_URL = "https://support.fire-emblem-heroes.com/voting_gauntlet/current"
PAGE_QUERY = {"locale": "en-US", "timezone": "Etc/UTC"}
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

# The site counts the votes at the top of every hour; a few minutes later the new scores are on the page
POSTING_TIMES = [time(hour=hour, minute=5, tzinfo=timezone.utc) for hour in range(24)]

ROUND_PATTERN = re.compile(r'<article class="body-section-tournament">(.*?)</article>', re.DOTALL)
WINDOW_PATTERN = re.compile(r'<div class="tournaments-date">([^<]*)</div>')
ENTRANT_PATTERN = re.compile(r'<p class="name">([^<]*)</p><p>([\d,]+)</p>')
# One end of a round's window, e.g. "10/5 at 7:00 a.m."
TIME_PATTERN = re.compile(r'(\d{1,2})/(\d{1,2}) at (\d{1,2}):(\d{2}) ([ap])\.m\.')

NOTIFICATION_CHANNEL_ID = config.read_settings().voting_gauntlet_channel_id


def start_voting_gauntlet_notification(client: discord.Client):
    if not NOTIFICATION_CHANNEL_ID:
        logging.warning("No channel ID is configured for Voting Gauntlet scores. Voting Gauntlet task will not be "
                        "initiated")
    elif not task_voting_gauntlet_scores.is_running():
        # on_ready fires again after reconnects; starting a running loop raises
        logging.info("Initiating Voting Gauntlet task")
        task_voting_gauntlet_scores.start(client)


@tasks.loop(time=POSTING_TIMES)
async def task_voting_gauntlet_scores(client: discord.Client):
    try:
        current_time = now()
        rounds = parse_rounds(await fetch_page(), current_time)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        # An exception would stop the loop; the next hour tries again
        logging.exception("Voting Gauntlet scores could not be read. Task will be skipped")
        return

    running = next((r for r in rounds if r.start <= current_time < r.end), None)
    if running is None:
        return
    channel = client.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        logging.error("Channel %s not found. Task will be skipped", NOTIFICATION_CHANNEL_ID)
        return
    for matchup in running.matchups:
        await channel.send(format_matchup(matchup))


def now() -> datetime:
    return datetime.now(timezone.utc)


async def fetch_page() -> str:
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        async with session.get(CURRENT_URL) as response:
            response.raise_for_status()
            page_url = response.url
        async with session.get(page_url.with_query(PAGE_QUERY)) as response:
            response.raise_for_status()
            return await response.text()


def parse_rounds(page: str, current_time: datetime) -> list[Round]:
    # The rounds that have started, latest first; raises ValueError when the page doesn't look as expected
    rounds = []
    for section in ROUND_PATTERN.findall(page):
        window = WINDOW_PATTERN.search(section)
        if window is None:
            raise ValueError("Round without a date")
        start, end = parse_window(window.group(1), current_time)
        matchups = []
        for battle in section.split('<li class="tournaments-battle">')[1:]:
            entrants = [Entrant(html.unescape(name), int(score.replace(",", "")))
                        for name, score in ENTRANT_PATTERN.findall(battle)]
            if len(entrants) != 2:
                raise ValueError(f"Matchup with {len(entrants)} entrants")
            matchups.append((entrants[0], entrants[1]))
        rounds.append(Round(start, end, matchups))
    if not rounds:
        raise ValueError("No rounds on the page")
    return rounds


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


def format_matchup(matchup: tuple[Entrant, Entrant]) -> str:
    stronger, weaker = sorted(matchup, key=lambda entrant: entrant.score, reverse=True)
    return f"{stronger.name} (Stronger)\n{stronger.score:,}\n{weaker.name} (Weaker)\n{weaker.score:,}"
