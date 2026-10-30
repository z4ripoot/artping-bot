import logging
from datetime import date, datetime, time, timedelta, timezone

import discord
from discord.ext import tasks

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.model.weekly_reminder import WeeklyReminder
from fjormcord.bot.artping.util.task_util import get_task_channel, start_channel_task
from fjormcord.bot.artping.view.layout import to_view

# Every reminder is sent this many hours before closing
HOURS_BEFORE_CLOSING = (5, 1)

# All scheduling is done in UTC, independent of the host's timezone
COLISEUM = WeeklyReminder(
    name="Coliseum notification",
    weekday=0,
    closing_time=time(hour=23, minute=0, tzinfo=timezone.utc),
    text="Coliseum/Aether Raids closes",
    channel_id=lambda settings: settings.coliseum_channel_id,
)
# Divine Games ends on Saturday at 23:59 GMT+1, which is 22:59 UTC
DIVINE_GAMES = WeeklyReminder(
    name="Divine Games notification",
    weekday=5,
    closing_time=time(hour=22, minute=59, tzinfo=timezone.utc),
    text="Divine Games ends",
    channel_id=lambda settings: settings.divine_games_channel_id,
)
REMINDERS = (COLISEUM, DIVINE_GAMES)


def start_weekly_reminders(client: discord.Client):
    for reminder in REMINDERS:
        start_channel_task(TASKS[reminder], client, reminder.channel_id(config.read_settings()), reminder.name)


def reminder_times(reminder: WeeklyReminder) -> list[time]:
    # Any date will do, only the time of day is kept; a reminder may fall on the day before closing
    closing = datetime.combine(date(2000, 1, 1), reminder.closing_time)
    return [(closing - timedelta(hours=hours)).timetz() for hours in HOURS_BEFORE_CLOSING]


def _make_task(reminder: WeeklyReminder) -> tasks.Loop:
    @tasks.loop(time=reminder_times(reminder))
    async def task(client: discord.Client):
        # The loop only survives network errors: any other exception, e.g. a missing permission, would stop it for good
        try:
            await send_notification(client, reminder)
        except Exception:
            logging.exception("Sending the %s failed. Task will be skipped", reminder.name)

    return task


TASKS = {reminder: _make_task(reminder) for reminder in REMINDERS}


async def send_notification(client: discord.Client, reminder: WeeklyReminder):
    # Only within a day of closing, so a reminder may fall on the day before closing but not on other days
    now = datetime.now(timezone.utc)
    closing = next_closing(reminder, now)
    if closing - now < timedelta(days=1):
        await send_reminder(client, reminder, closing)


def next_closing(reminder: WeeklyReminder, now: datetime) -> datetime:
    # The first closing after now, this week or the next
    days_ahead = (reminder.weekday - now.weekday()) % 7
    closing = datetime.combine(now.date() + timedelta(days=days_ahead), reminder.closing_time)
    if closing <= now:
        closing += timedelta(weeks=1)
    return closing


def reminder_text(reminder: WeeklyReminder, closing: datetime) -> str:
    # Discord shows the timestamps in each reader's own timezone
    closing_time = int(closing.timestamp())
    return f"{reminder.text} <t:{closing_time}:R> at <t:{closing_time}:f>"


async def send_reminder(client: discord.Client, reminder: WeeklyReminder, closing: datetime) -> bool:
    # Posts the reminder to its channel; False, and logged, when the bot can't see the channel
    channel = get_task_channel(client, reminder.channel_id(config.read_settings()))
    if channel is None:
        return False

    message = reminder_text(reminder, closing)
    logging.info(message)
    await channel.send(view=to_view(Layout((message,))))
    return True
