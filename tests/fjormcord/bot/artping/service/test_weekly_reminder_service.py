import asyncio
from datetime import datetime, timedelta, timezone

import discord
import pytest

from fjormcord.bot.artping.service import weekly_reminder_service
from tests.fakes import FakeChannel, FakeClient, fake_datetime, http_error, use_settings

COLISEUM_CLOSING = int(datetime(2026, 11, 2, 23, 0, tzinfo=timezone.utc).timestamp())
DIVINE_GAMES_CLOSING = int(datetime(2026, 10, 31, 23, 0, tzinfo=timezone.utc).timestamp())


def at(monkeypatch, utc_now):
    monkeypatch.setattr(weekly_reminder_service, "datetime", fake_datetime(utc_now, timedelta()))


def test_closing_times_lists_the_soonest_first(monkeypatch):
    # Saturday noon: Divine Games closes tonight, Coliseum on Monday
    at(monkeypatch, datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc))

    assert weekly_reminder_service.get_closing_times().texts == (
        "### Closing times",
        f"Divine Games closes <t:{DIVINE_GAMES_CLOSING}:R> at <t:{DIVINE_GAMES_CLOSING}:f>\n"
        f"Coliseum/Aether Raids closes <t:{COLISEUM_CLOSING}:R> at <t:{COLISEUM_CLOSING}:f>",
    )


def test_closing_times_after_closing_give_next_week(monkeypatch):
    # Saturday 23:30 UTC, after Divine Games closed
    at(monkeypatch, datetime(2026, 10, 31, 23, 30, tzinfo=timezone.utc))

    next_week = int(datetime(2026, 11, 7, 23, 0, tzinfo=timezone.utc).timestamp())
    assert weekly_reminder_service.get_closing_times().texts[1].splitlines() == [
        f"Coliseum/Aether Raids closes <t:{COLISEUM_CLOSING}:R> at <t:{COLISEUM_CLOSING}:f>",
        f"Divine Games closes <t:{next_week}:R> at <t:{next_week}:f>",
    ]


@pytest.fixture
def channels(monkeypatch):
    coliseum, divine_games = FakeChannel(channel_id=20), FakeChannel(channel_id=30)
    use_settings(monkeypatch, coliseum_channel_id=20, divine_games_channel_id=30)
    # A Wednesday, when no reminder is due
    at(monkeypatch, datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc))
    return coliseum, divine_games


def send_reminders(*channels):
    return asyncio.run(weekly_reminder_service.send_reminders(FakeClient(channels=channels)))


def test_send_reminders_posts_every_reminder_now(channels):
    coliseum, divine_games = channels

    assert send_reminders(coliseum, divine_games) == (
        "Coliseum notification: sent to <#20>\nDivine Games notification: sent to <#30>"
    )
    assert coliseum.sent == [f"Coliseum/Aether Raids closes <t:{COLISEUM_CLOSING}:R> at <t:{COLISEUM_CLOSING}:f>"]
    assert divine_games.sent == [f"Divine Games closes <t:{DIVINE_GAMES_CLOSING}:R> at <t:{DIVINE_GAMES_CLOSING}:f>"]


def test_send_reminders_reports_a_missing_or_unknown_channel(monkeypatch, channels):
    coliseum, _ = channels
    use_settings(monkeypatch, coliseum_channel_id=None, divine_games_channel_id=456)

    assert send_reminders(coliseum) == (
        "Coliseum notification: no channel is configured\nDivine Games notification: channel 456 not found"
    )
    assert coliseum.sent == []


def test_send_reminders_continues_after_a_failure(channels):
    _, divine_games = channels

    class ForbiddenChannel(FakeChannel):
        async def send(self, content=None, allowed_mentions=None, view=None):
            raise http_error(discord.Forbidden, 403)

    assert send_reminders(ForbiddenChannel(channel_id=20), divine_games) == (
        "Coliseum notification: sending to <#20> failed\nDivine Games notification: sent to <#30>"
    )
    assert len(divine_games.sent) == 1
