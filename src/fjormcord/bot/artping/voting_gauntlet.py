import asyncio
import html
import logging
import re
from datetime import datetime, time, timedelta, timezone

import aiohttp
import discord
from discord.ext import tasks

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.model.voting_gauntlet import Entrant, Round
from fjormcord.bot.artping.service import voting_gauntlet_service
from fjormcord.bot.artping.util.task_util import get_task_channel, start_channel_task
from fjormcord.bot.artping.util.user_util import mentions
from fjormcord.bot.artping.view.layout import message_options
from fjormcord.bot.artping.view.voting_gauntlet_view import track_buttons

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
# A character's picture, then its name and score, which is empty before the first count. The picture's class ends in
# its status: normal or behind
ENTRANT_PATTERN = re.compile(
    r'<div class="tournaments-art-(?:left|right) art-\d+-\d+-(\w+)">'
    r'.*?<p class="name">([^<]*)</p><p>([\d,]*)</p>',
    re.DOTALL,
)
STATUSES = {"normal": False, "behind": True}
# The most users Discord lets a message's allowed mentions name, so the most trackers a matchup message mentions
MAX_MENTIONS = 100
# One end of a round's window, e.g. "10/5 at 7:00 a.m."
TIME_PATTERN = re.compile(r"(\d{1,2})/(\d{1,2}) at (\d{1,2}):(\d{2}) ([ap])\.m\.")


def start_voting_gauntlet_notification(client: discord.Client):
    start_channel_task(
        task_voting_gauntlet_scores, client, config.read_settings().voting_gauntlet_channel_id, "Voting Gauntlet scores"
    )


@tasks.loop(time=POSTING_TIMES)
async def task_voting_gauntlet_scores(client: discord.Client):
    # The loop only survives network errors: any other exception, e.g. a database error, would stop it for good. The
    # next hour tries again
    try:
        await post_scores(client)
    except Exception:
        logging.exception("Posting the Voting Gauntlet scores failed. Task will be skipped")


async def post_scores(client: discord.Client) -> str:
    # Posts the scores of the running round; returns what it did, which ~sendvotinggauntlet replies with
    try:
        current_time = now()
        tournament_id, page = await fetch_page()
        rounds = parse_rounds(page, current_time)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        logging.exception("Voting Gauntlet scores could not be read. Task will be skipped")
        return "The Voting Gauntlet scores could not be read; the log has the error"

    running = next((round_ for round_ in rounds if round_.start <= current_time < round_.end), None)
    if running is None:
        # The gauntlet has ended once the latest round is over and it is the final one, with a single matchup
        latest = rounds[0]
        if len(latest.matchups) == 1 and current_time >= latest.end:
            voting_gauntlet_service.end_gauntlet()
        return f"No round of Voting Gauntlet {tournament_id} is running, so nothing was posted"

    voting_gauntlet_service.start_gauntlet(tournament_id)
    channel_id = config.read_settings().voting_gauntlet_channel_id
    channel = get_task_channel(client, channel_id)
    if channel is None:
        return f"Channel {channel_id} not found"
    failed = 0
    for matchup in running.matchups:
        trackers = tuple(voting_gauntlet_service.get_trackers(tournament_id, entrant.name) for entrant in matchup)
        # Every tracker is shown, but only those of the Weaker character are pinged
        pinged = [user_id for entrant, users in zip(matchup, trackers) if entrant.behind for user_id in users]
        try:
            # Many trackers are split over several messages, the buttons on the last
            for part in format_matchup(matchup, trackers, tournament_id):
                [options] = message_options(part)
                await channel.send(**options, allowed_mentions=_pings(part, pinged))
        except discord.DiscordException:
            # The other matchups are still posted
            logging.exception("Posting the Voting Gauntlet matchup of %s failed", matchup[0].name)
            failed += 1

    total = len(running.matchups)
    report = f"Posted {total - failed} of the {total} matchups of Voting Gauntlet {tournament_id} to <#{channel_id}>"
    return f"{report}; the log has the errors" if failed else report


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
    # The rounds on the page, latest first; raises ValueError when the page doesn't look as expected. The page's order
    # varies: before a gauntlet starts it lists every round earliest first, with the first round's matchups but no
    # scores; during round 3 and after the end it listed them latest first
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
    return sorted(rounds, key=lambda round_: round_.start, reverse=True)


def _parse_matchup(battle: str) -> tuple[Entrant, Entrant]:
    entrants = []
    for status, name, score in ENTRANT_PATTERN.findall(battle):
        if status not in STATUSES:
            raise ValueError(f"Unknown status {status} of {name}")
        entrants.append(Entrant(html.unescape(name), int(score.replace(",", "")) if score else None, STATUSES[status]))
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


def format_matchup(
    matchup: tuple[Entrant, Entrant], trackers: tuple[list[str], list[str]], tournament_id: int
) -> list[Layout]:
    # The messages of a matchup. In the site's order, labelled as in the game; after a separator the trackers of each
    # character (trackers holds them in the matchup's order) as mentions, which show their names, then the Track
    # buttons. A message can only ping MAX_MENTIONS users, so more trackers than that go in messages of their own
    # after the scores: per character, MAX_MENTIONS at a time
    lines = []
    for entrant, opponent in (matchup, matchup[::-1]):
        # In the first hour of a gauntlet the votes haven't been counted yet; the matchup is still posted, so its
        # characters can be tracked
        score = "No score yet" if entrant.score is None else f"{entrant.score:,}"
        lines += [f"**{entrant.name}** | {_status(entrant, opponent)}", score]
    scores = "\n".join(lines)
    buttons = (track_buttons(tournament_id, matchup),)
    tracked = [(entrant.name, users) for entrant, users in zip(matchup, trackers) if users]
    if sum(len(users) for _, users in tracked) <= MAX_MENTIONS:
        tracking = "\n".join(f"**{name}**: {mentions(users)}" for name, users in tracked)
        return [Layout((scores, tracking) if tracking else (scores,), buttons)]

    texts = [scores] + [
        f"**{name}**: {mentions(users[start : start + MAX_MENTIONS])}"
        for name, users in tracked
        for start in range(0, len(users), MAX_MENTIONS)
    ]
    return [Layout((text,)) for text in texts[:-1]] + [Layout((texts[-1],), buttons)]


def _pings(part: Layout, pinged: list[str]) -> discord.AllowedMentions:
    # Only the users in pinged that this message mentions are pinged; format_matchup keeps them to MAX_MENTIONS
    text = "\n".join(part.texts)
    users = [discord.Object(int(user_id)) for user_id in pinged if f"<@{user_id}>" in text]
    return discord.AllowedMentions(everyone=False, roles=False, users=users, replied_user=False)


def _status(entrant: Entrant, opponent: Entrant) -> str:
    if entrant.behind:
        return "🔴 Weaker 🔴"
    return "🔵 Stronger 🔵" if opponent.behind else "Same"
