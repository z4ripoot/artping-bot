import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import aiohttp
import discord
import pytest

from fjormcord.bot.artping import voting_gauntlet
from fjormcord.bot.artping.model.voting_gauntlet import Entrant
from fjormcord.bot.artping.repository import voting_gauntlet_repository
from fjormcord.bot.artping.service import voting_gauntlet_service
from fjormcord.bot.artping.view.layout import to_view
from fjormcord.bot.artping.view.voting_gauntlet_view import TrackButton
from tests.fakes import FakeChannel, button_labels, buttons, http_error, items_of_type, text_length, use_settings

# English, UTC pages of tournament 112 (scripts removed): as the site served it after the gauntlet ended, and an
# archived copy taken during round 3, whose Pacific times were rewritten to the UTC the bot requests
ENDED_PAGE = (Path(__file__).parent / "voting_gauntlet_112.html").read_text(encoding="utf-8")
ROUND_3_PAGE = (Path(__file__).parent / "voting_gauntlet_112_round_3.html").read_text(encoding="utf-8")
# Tournament 113 the day before it started: every round listed, earliest first, round 1's matchups without scores
UPCOMING_PAGE = (Path(__file__).parent / "voting_gauntlet_113_upcoming.html").read_text(encoding="utf-8")

TOURNAMENT_ID = 112
CHANNEL_ID = 123


def utc(month, day, hour, minute=0, year=2026):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_rounds_are_read_from_the_page():
    rounds = voting_gauntlet.parse_rounds(ENDED_PAGE, utc(10, 6, 12))

    # Latest round first, as on the page
    assert [(r.start, r.end) for r in rounds] == [
        (utc(10, 5, 7), utc(10, 7, 4)),
        (utc(10, 3, 7), utc(10, 5, 4)),
        (utc(10, 1, 7), utc(10, 3, 4)),
    ]
    assert rounds[0].matchups == [
        (Entrant("Edelgard", 24_743_944_266, behind=False), Entrant("Dimitri", 21_907_126_652, behind=True))
    ]
    assert len(rounds[2].matchups) == 4
    assert rounds[2].matchups[1] == (
        Entrant("Cai", 1_958_844_520, behind=True),
        Entrant("Claude", 2_072_857_153, behind=False),
    )


def test_running_round_is_read_from_the_page():
    [final, *_] = voting_gauntlet.parse_rounds(ROUND_3_PAGE, utc(10, 6, 1, 44))

    assert final.matchups == [
        (Entrant("Edelgard", 4_397_904_760, behind=False), Entrant("Dimitri", 3_872_872_478, behind=True))
    ]


def test_upcoming_gauntlet_is_read_from_the_page():
    rounds = voting_gauntlet.parse_rounds(UPCOMING_PAGE, utc(10, 30, 9, 37))

    # Latest round first, although the page lists them earliest first
    assert [(r.start, r.end) for r in rounds] == [
        (utc(11, 4, 7), utc(11, 6, 4)),
        (utc(11, 2, 7), utc(11, 4, 4)),
        (utc(10, 31, 7), utc(11, 2, 4)),
    ]
    assert [len(r.matchups) for r in rounds] == [0, 0, 4]
    # Not counted yet
    assert rounds[2].matchups[0] == (Entrant("Reginn", None, behind=False), Entrant("Dagr", None, behind=False))


def test_page_without_rounds_fails():
    with pytest.raises(ValueError, match="No rounds"):
        voting_gauntlet.parse_rounds("<html><body>Maintenance</body></html>", utc(10, 6, 12))


def test_unknown_status_fails():
    with pytest.raises(ValueError, match="status"):
        voting_gauntlet.parse_rounds(ROUND_3_PAGE.replace("art-112-8-behind", "art-112-8-winning"), utc(10, 6, 2))


def test_both_sides_behind_fails():
    with pytest.raises(ValueError, match="Both"):
        voting_gauntlet.parse_rounds(ROUND_3_PAGE.replace("art-112-2-normal", "art-112-2-behind"), utc(10, 6, 2))


def test_round_window_is_given_the_year_closest_to_now():
    # The page leaves out the year; a round over New Year is read correctly from either side of it
    window = "12/31 at 7:00 a.m.~1/2 at 3:59 a.m. UTC"

    assert voting_gauntlet.parse_window(window, utc(12, 31, 8)) == (utc(12, 31, 7), utc(1, 2, 4, year=2027))
    assert voting_gauntlet.parse_window(window, utc(1, 1, 8, year=2027)) == (utc(12, 31, 7), utc(1, 2, 4, year=2027))


def test_round_window_reads_afternoon_times():
    assert voting_gauntlet.parse_window("3/1 at 12:00 p.m.~3/3 at 11:59 p.m. UTC", utc(3, 2, 0)) == (
        utc(3, 1, 12),
        utc(3, 4, 0),
    )


def test_matchup_message_keeps_the_site_order():
    message = voting_gauntlet.format_matchup(
        (Entrant("Cai", 1_958_844_520, behind=True), Entrant("Claude", 2_072_857_153, behind=False)), [], 112
    )

    assert message.texts == ("Cai (Weaker)\n1,958,844,520\nClaude (Stronger)\n2,072,857,153",)
    assert button_labels(to_view(message)) == ["Track Cai", "Track Claude"]


def test_matchup_without_a_side_behind_is_same():
    message = voting_gauntlet.format_matchup(
        (Entrant("Cai", 2_072_857_153, behind=False), Entrant("Claude", 2_072_857_150, behind=False)), [], 112
    )

    assert message.texts == ("Cai (Same)\n2,072,857,153\nClaude (Same)\n2,072,857,150",)


def test_matchup_message_mentions_the_trackers():
    message = voting_gauntlet.format_matchup(
        (Entrant("Cai", 1, behind=True), Entrant("Claude", 2, behind=False)), ["11", "22"], 112
    )

    # The mentions after a separator
    assert message.texts == ("Cai (Weaker)\n1\nClaude (Stronger)\n2", "<@11> <@22>")


def set_up_site(monkeypatch, now, page=ENDED_PAGE, tournament_id=TOURNAMENT_ID, channel_id=CHANNEL_ID):
    # The site shows page at now; returns a client that sees the channel CHANNEL_ID, and that channel
    channel = FakeChannel()
    client = SimpleNamespace(get_channel=lambda channel_id: channel if channel_id == CHANNEL_ID else None)

    async def fetch_page():
        if isinstance(page, Exception):
            raise page
        return tournament_id, page

    use_settings(monkeypatch, voting_gauntlet_channel_id=channel_id)
    monkeypatch.setattr(voting_gauntlet, "fetch_page", fetch_page)
    monkeypatch.setattr(voting_gauntlet, "now", lambda: now)
    return client, channel


def run_task(monkeypatch, now, **site):
    client, channel = set_up_site(monkeypatch, now, **site)
    asyncio.run(voting_gauntlet.task_voting_gauntlet_scores.coro(client))
    return channel


def send_scores(monkeypatch, now, **site):
    # The debug command ~sendvotinggauntlet: its reply, and the channel
    client, channel = set_up_site(monkeypatch, now, **site)
    return asyncio.run(voting_gauntlet_service.send_scores(client)), channel


def track(name, opponent, user_id, tournament_id=TOURNAMENT_ID):
    return voting_gauntlet_service.toggle_tracking(tournament_id, str(user_id), name, opponent)


def custom_ids(message):
    return [button.custom_id for button in buttons(message.view)]


def test_every_matchup_of_the_running_round_is_posted(monkeypatch):
    sent = run_task(monkeypatch, utc(10, 2, 15, 5)).sent

    assert len(sent) == 4
    assert sent[0] == "Theodora (Weaker)\n4,629,570,726\nEdelgard (Stronger)\n4,712,198,958"


def test_matchup_message_has_a_track_button_per_character(monkeypatch):
    message = run_task(monkeypatch, utc(10, 6, 1, 5), page=ROUND_3_PAGE).last_message()

    assert button_labels(message.view) == ["Track Edelgard", "Track Dimitri"]
    assert isinstance(message.view, discord.ui.LayoutView)
    assert len(items_of_type(message.view, TrackButton)) == 2
    assert custom_ids(message) == ["voting_gauntlet:112:Edelgard:Dimitri", "voting_gauntlet:112:Dimitri:Edelgard"]
    # Persistent, so the buttons keep working after a restart
    assert message.view.timeout is None


def test_trackers_of_the_weaker_character_are_pinged(monkeypatch):
    run_task(monkeypatch, utc(10, 6, 1, 5), page=ROUND_3_PAGE)
    track("Dimitri", "Edelgard", 11)
    track("Dimitri", "Edelgard", 22)
    track("Edelgard", "Dimitri", 33)

    [message] = run_task(monkeypatch, utc(10, 6, 2, 5), page=ROUND_3_PAGE).sent

    assert message.endswith("Dimitri (Weaker)\n3,872,872,478\n<@11> <@22>")


def test_nobody_is_pinged_when_neither_side_is_behind(monkeypatch):
    run_task(monkeypatch, utc(10, 6, 1, 5), page=ROUND_3_PAGE)
    track("Dimitri", "Edelgard", 11)

    [message] = run_task(
        monkeypatch, utc(10, 6, 2, 5), page=ROUND_3_PAGE.replace("art-112-8-behind", "art-112-8-normal")
    ).sent

    assert "<@" not in message


def test_many_trackers_are_split_over_messages_with_the_buttons_on_the_last(monkeypatch):
    run_task(monkeypatch, utc(10, 6, 1, 5), page=ROUND_3_PAGE)
    for user_id in range(10**17, 10**17 + 200):
        track("Dimitri", "Edelgard", user_id)

    channel = run_task(monkeypatch, utc(10, 6, 2, 5), page=ROUND_3_PAGE)

    assert len(channel.sent) > 1
    assert " ".join(channel.sent).count("<@") == 200
    messages = list(channel.messages.values())
    assert all(text_length(message.view) <= 4000 for message in messages)
    assert [bool(button_labels(message.view)) for message in messages] == [False] * (len(messages) - 1) + [True]


def test_tracking_lasts_across_rounds(monkeypatch):
    run_task(monkeypatch, utc(10, 4, 1, 5), page=ROUND_3_PAGE)
    track("Dimitri", "Yuri", 11)

    # Between rounds 2 and 3, then in round 3
    run_task(monkeypatch, utc(10, 5, 5, 5), page=ROUND_3_PAGE)
    [message] = run_task(monkeypatch, utc(10, 6, 2, 5), page=ROUND_3_PAGE).sent

    assert message.endswith("<@11>")


def test_trackers_are_removed_when_the_final_round_has_ended(monkeypatch):
    run_task(monkeypatch, utc(10, 6, 1, 5), page=ROUND_3_PAGE)
    track("Dimitri", "Edelgard", 11)

    assert run_task(monkeypatch, utc(10, 7, 4, 5)).sent == []

    assert voting_gauntlet_service.get_trackers(TOURNAMENT_ID, "Dimitri") == []
    assert track("Dimitri", "Edelgard", 11) == voting_gauntlet_service.MESSAGE_ENDED


def test_trackers_of_an_older_gauntlet_are_removed_when_a_new_one_runs(monkeypatch):
    run_task(monkeypatch, utc(10, 6, 1, 5), page=ROUND_3_PAGE, tournament_id=111)
    track("Dimitri", "Edelgard", 11, tournament_id=111)

    [message] = run_task(monkeypatch, utc(10, 6, 2, 5), page=ROUND_3_PAGE).sent

    assert "<@" not in message
    assert track("Dimitri", "Edelgard", 11, tournament_id=111) == voting_gauntlet_service.MESSAGE_ENDED


def test_last_hour_of_a_round_is_posted(monkeypatch):
    assert len(run_task(monkeypatch, utc(10, 7, 3, 5)).sent) == 1


@pytest.mark.parametrize("now", [utc(10, 7, 4, 5), utc(10, 5, 5, 5), utc(9, 30, 12)])
def test_nothing_is_posted_outside_a_round(monkeypatch, now):
    # After the gauntlet, between two rounds, and before the gauntlet
    assert run_task(monkeypatch, now).sent == []


@pytest.mark.parametrize("page", [aiohttp.ClientError("down"), asyncio.TimeoutError(), "<html>changed</html>"])
def test_failure_is_logged_and_skipped(monkeypatch, caplog, page):
    assert run_task(monkeypatch, utc(10, 2, 15, 5), page=page).sent == []
    assert "Voting Gauntlet scores could not be read" in caplog.text


def test_any_other_failure_is_logged_and_skipped(monkeypatch, caplog):
    # discord.py's loop only survives network errors; anything else, e.g. a database error, must not stop it
    def fail(tournament_id):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(voting_gauntlet_service, "start_gauntlet", fail)

    assert run_task(monkeypatch, utc(10, 2, 15, 5)).sent == []
    assert "Posting the Voting Gauntlet scores failed" in caplog.text


def test_unknown_channel_is_logged(monkeypatch, caplog):
    assert run_task(monkeypatch, utc(10, 2, 15, 5), channel_id=456).sent == []
    assert "456" in caplog.text


def test_not_started_without_channel_id(monkeypatch, caplog):
    use_settings(monkeypatch, voting_gauntlet_channel_id=None)

    voting_gauntlet.start_voting_gauntlet_notification(SimpleNamespace())

    assert "No channel ID is configured for the Voting Gauntlet scores task" in caplog.text
    assert not voting_gauntlet.task_voting_gauntlet_scores.is_running()


def test_send_scores_posts_the_running_round_now(monkeypatch):
    reply, channel = send_scores(monkeypatch, utc(10, 2, 15, 30))

    assert reply == "Posted 4 of the 4 matchups of Voting Gauntlet 112 to <#123>"
    assert len(channel.sent) == 4


def test_send_scores_posts_nothing_outside_a_round(monkeypatch):
    # Between two rounds
    reply, channel = send_scores(monkeypatch, utc(10, 5, 5, 5))

    assert reply == "No round of Voting Gauntlet 112 is running, so nothing was posted"
    assert channel.sent == []


def test_nothing_is_posted_or_logged_before_the_gauntlet_starts(monkeypatch, caplog):
    sent = run_task(monkeypatch, utc(10, 30, 10, 5), page=UPCOMING_PAGE, tournament_id=113).sent

    assert sent == []
    assert "could not be read" not in caplog.text
    reply, _ = send_scores(monkeypatch, utc(10, 30, 10, 5), page=UPCOMING_PAGE, tournament_id=113)
    assert reply == "No round of Voting Gauntlet 113 is running, so nothing was posted"


def test_nothing_is_posted_while_the_running_round_has_no_scores(monkeypatch, caplog):
    # Round 1 has started, but the page still shows no scores
    sent = run_task(monkeypatch, utc(10, 31, 7, 5), page=UPCOMING_PAGE, tournament_id=113).sent

    assert sent == []
    assert "could not be read" not in caplog.text
    reply, _ = send_scores(monkeypatch, utc(10, 31, 7, 5), page=UPCOMING_PAGE, tournament_id=113)
    assert reply == "The running round of Voting Gauntlet 113 has no scores yet, so nothing was posted"


def test_upcoming_gauntlet_does_not_end_the_running_one(monkeypatch):
    # The last round listed has no matchups yet, so it isn't taken for a final round that is over
    voting_gauntlet_service.start_gauntlet(112)

    run_task(monkeypatch, utc(11, 7, 12), page=UPCOMING_PAGE, tournament_id=113)

    assert voting_gauntlet_repository.get_running_tournament() == 112


def test_send_scores_reports_a_page_it_cannot_read(monkeypatch):
    reply, _ = send_scores(monkeypatch, utc(10, 2, 15, 5), page=aiohttp.ClientError("down"))

    assert reply == "The Voting Gauntlet scores could not be read; the log has the error"


def test_send_scores_reports_a_missing_or_unknown_channel(monkeypatch):
    assert send_scores(monkeypatch, utc(10, 2, 15, 5), channel_id=None)[0] == (
        "No channel is configured for the Voting Gauntlet scores"
    )
    assert send_scores(monkeypatch, utc(10, 2, 15, 5), channel_id=456)[0] == "Channel 456 not found"


def test_send_scores_reports_matchups_that_failed(monkeypatch):
    client, channel = set_up_site(monkeypatch, utc(10, 2, 15, 5))
    send = channel.send
    calls = []

    async def send_all_but_the_first(**options):
        calls.append(options)
        if len(calls) == 1:
            raise http_error(discord.Forbidden, 403)
        return await send(**options)

    channel.send = send_all_but_the_first

    reply = asyncio.run(voting_gauntlet_service.send_scores(client))

    assert reply == "Posted 3 of the 4 matchups of Voting Gauntlet 112 to <#123>; the log has the errors"
    assert len(channel.sent) == 3
