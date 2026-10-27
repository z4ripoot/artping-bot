import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import aiohttp
import pytest

from fjormcord.bot.artping import voting_gauntlet
from fjormcord.bot.artping.model.voting_gauntlet import Entrant
from tests.fakes import FakeChannel

# The English, UTC page of tournament 112, as the site served it after the gauntlet ended (scripts removed)
PAGE = (Path(__file__).parent / "voting_gauntlet_112.html").read_text(encoding="utf-8")

CHANNEL_ID = 123


def utc(month, day, hour, minute=0, year=2026):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_rounds_are_read_from_the_page():
    rounds = voting_gauntlet.parse_rounds(PAGE, utc(10, 6, 12))

    # Latest round first, as on the page
    assert [(r.start, r.end) for r in rounds] == [(utc(10, 5, 7), utc(10, 7, 4)),
                                                  (utc(10, 3, 7), utc(10, 5, 4)),
                                                  (utc(10, 1, 7), utc(10, 3, 4))]
    assert rounds[0].matchups == [(Entrant("Edelgard", 24_743_944_266), Entrant("Dimitri", 21_907_126_652))]
    assert len(rounds[2].matchups) == 4
    assert rounds[2].matchups[1] == (Entrant("Cai", 1_958_844_520), Entrant("Claude", 2_072_857_153))


def test_page_without_rounds_fails():
    with pytest.raises(ValueError, match="No rounds"):
        voting_gauntlet.parse_rounds("<html><body>Maintenance</body></html>", utc(10, 6, 12))


def test_round_window_is_given_the_year_closest_to_now():
    # The page leaves out the year; a round over New Year is read correctly from either side of it
    window = "12/31 at 7:00 a.m.~1/2 at 3:59 a.m. UTC"

    assert voting_gauntlet.parse_window(window, utc(12, 31, 8)) == (utc(12, 31, 7), utc(1, 2, 4, year=2027))
    assert voting_gauntlet.parse_window(window, utc(1, 1, 8, year=2027)) == (utc(12, 31, 7), utc(1, 2, 4, year=2027))


def test_round_window_reads_afternoon_times():
    assert voting_gauntlet.parse_window("3/1 at 12:00 p.m.~3/3 at 11:59 p.m. UTC", utc(3, 2, 0)) == (
        utc(3, 1, 12), utc(3, 4, 0))


def test_matchup_message_puts_the_leader_first():
    message = voting_gauntlet.format_matchup((Entrant("Cai", 1_958_844_520), Entrant("Claude", 2_072_857_153)))

    assert message == "Claude (Stronger)\n2,072,857,153\nCai (Weaker)\n1,958,844,520"


def run_task(monkeypatch, now, page=PAGE, channel_id=CHANNEL_ID):
    channel = FakeChannel()
    client = SimpleNamespace(get_channel=lambda channel_id: channel if channel_id == CHANNEL_ID else None)

    async def fetch_page():
        if isinstance(page, Exception):
            raise page
        return page

    monkeypatch.setattr(voting_gauntlet, "NOTIFICATION_CHANNEL_ID", channel_id)
    monkeypatch.setattr(voting_gauntlet, "fetch_page", fetch_page)
    monkeypatch.setattr(voting_gauntlet, "now", lambda: now)

    asyncio.run(voting_gauntlet.task_voting_gauntlet_scores.coro(client))
    return channel.sent


def test_every_matchup_of_the_running_round_is_posted(monkeypatch):
    sent = run_task(monkeypatch, utc(10, 2, 15, 5))

    assert len(sent) == 4
    assert sent[0] == "Edelgard (Stronger)\n4,712,198,958\nTheodora (Weaker)\n4,629,570,726"


def test_last_hour_of_a_round_is_posted(monkeypatch):
    assert len(run_task(monkeypatch, utc(10, 7, 3, 5))) == 1


@pytest.mark.parametrize("now", [utc(10, 7, 4, 5), utc(10, 5, 5, 5), utc(9, 30, 12)])
def test_nothing_is_posted_outside_a_round(monkeypatch, now):
    # After the gauntlet, between two rounds, and before the gauntlet
    assert run_task(monkeypatch, now) == []


@pytest.mark.parametrize("page", [aiohttp.ClientError("down"), asyncio.TimeoutError(), "<html>changed</html>"])
def test_failure_is_logged_and_skipped(monkeypatch, caplog, page):
    assert run_task(monkeypatch, utc(10, 2, 15, 5), page=page) == []
    assert "Voting Gauntlet scores could not be read" in caplog.text


def test_unknown_channel_is_logged(monkeypatch, caplog):
    assert run_task(monkeypatch, utc(10, 2, 15, 5), channel_id=456) == []
    assert "456" in caplog.text


def test_not_started_without_channel_id(monkeypatch, caplog):
    monkeypatch.setattr(voting_gauntlet, "NOTIFICATION_CHANNEL_ID", None)

    voting_gauntlet.start_voting_gauntlet_notification(SimpleNamespace())

    assert "No channel ID is configured for Voting Gauntlet" in caplog.text
    assert not voting_gauntlet.task_voting_gauntlet_scores.is_running()
