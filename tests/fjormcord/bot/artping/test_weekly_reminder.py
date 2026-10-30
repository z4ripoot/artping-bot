import asyncio
from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
from types import SimpleNamespace

import discord
import pytest

from fjormcord.bot.artping import weekly_reminder
from fjormcord.bot.artping.weekly_reminder import COLISEUM, DIVINE_GAMES, TASKS
from tests.fakes import FakeChannel, fake_datetime, http_error, use_settings

CHANNEL_ID = 123
# The host runs on UTC+4, where the reminder times already fall on the next day
HOST_OFFSET = timedelta(hours=4)

# Each reminder with its channel setting, the time of its last reminder, and the closing time and text it announces
CASES = pytest.mark.parametrize(
    ("reminder", "setting", "utc_now", "closing", "text"),
    [
        pytest.param(
            COLISEUM,
            "coliseum_channel_id",
            datetime(2026, 10, 19, 22, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 19, 23, 0, tzinfo=timezone.utc),
            "Coliseum/Aether Raids closes",
            id="coliseum",
        ),
        pytest.param(
            DIVINE_GAMES,
            "divine_games_channel_id",
            datetime(2026, 10, 31, 21, 59, tzinfo=timezone.utc),
            # 23:59 GMT+1
            datetime(2026, 10, 31, 22, 59, tzinfo=timezone.utc),
            "Divine Games ends",
            id="divine_games",
        ),
    ],
)


def run_task(monkeypatch, reminder, setting, utc_now, channel_id=CHANNEL_ID, channel=None):
    channel = channel or FakeChannel()
    client = SimpleNamespace(get_channel=lambda channel_id: channel if channel_id == CHANNEL_ID else None)
    use_settings(monkeypatch, **{setting: channel_id})
    monkeypatch.setattr(weekly_reminder, "datetime", fake_datetime(utc_now, HOST_OFFSET))

    asyncio.run(TASKS[reminder].coro(client))
    return channel


@CASES
def test_reminder_uses_utc_regardless_of_host_timezone(monkeypatch, reminder, setting, utc_now, closing, text):
    channel = run_task(monkeypatch, reminder, setting, utc_now)

    closing_time = int(closing.timestamp())
    assert channel.sent == [f"{text} <t:{closing_time}:R> at <t:{closing_time}:f>"]
    # Laid out: the text in a container, no content
    assert isinstance(channel.last_message().view, discord.ui.LayoutView)


@CASES
def test_reminder_skipped_on_other_days(monkeypatch, reminder, setting, utc_now, closing, text):
    # A day earlier, which is already the closing day on the UTC+4 host
    assert run_task(monkeypatch, reminder, setting, utc_now - timedelta(days=1)).sent == []


@CASES
def test_reminder_skipped_for_unknown_channel(monkeypatch, caplog, reminder, setting, utc_now, closing, text):
    assert run_task(monkeypatch, reminder, setting, utc_now, channel_id=456).sent == []
    assert "456" in caplog.text


@CASES
def test_reminder_failure_is_logged_and_skipped(monkeypatch, caplog, reminder, setting, utc_now, closing, text):
    # discord.py's loop only survives network errors; a missing permission must not stop the weekly reminder
    class ForbiddenChannel(FakeChannel):
        async def send(self, content=None, allowed_mentions=None, view=None):
            raise http_error(discord.Forbidden, 403)

    run_task(monkeypatch, reminder, setting, utc_now, channel=ForbiddenChannel())

    assert f"Sending the {reminder.name} failed" in caplog.text


@CASES
def test_reminder_not_started_without_channel_id(monkeypatch, caplog, reminder, setting, utc_now, closing, text):
    use_settings(monkeypatch, **{setting: None})

    weekly_reminder.start_weekly_reminders(SimpleNamespace())

    assert f"No channel ID is configured for the {reminder.name} task" in caplog.text
    assert not TASKS[reminder].is_running()


def test_reminders_are_sent_five_and_one_hour_before_closing():
    assert weekly_reminder.reminder_times(DIVINE_GAMES) == [
        time(17, 59, tzinfo=timezone.utc),
        time(21, 59, tzinfo=timezone.utc),
    ]


def test_reminder_on_the_day_before_closing(monkeypatch):
    # Closing on Tuesday at 01:00 UTC, so the 5 hours reminder is sent on Monday at 20:00
    reminder = replace(COLISEUM, weekday=1, closing_time=time(1, 0, tzinfo=timezone.utc))
    channel = FakeChannel()
    use_settings(monkeypatch, coliseum_channel_id=CHANNEL_ID)
    utc_now = datetime(2026, 10, 19, 20, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(weekly_reminder, "datetime", fake_datetime(utc_now, timedelta()))

    asyncio.run(weekly_reminder.send_notification(SimpleNamespace(get_channel=lambda channel_id: channel), reminder))

    closing_time = int(datetime(2026, 10, 20, 1, 0, tzinfo=timezone.utc).timestamp())
    assert channel.sent == [f"Coliseum/Aether Raids closes <t:{closing_time}:R> at <t:{closing_time}:f>"]
