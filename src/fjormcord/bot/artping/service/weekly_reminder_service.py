import logging
from datetime import datetime, timezone

import discord

from fjormcord.bot.artping import config, weekly_reminder
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.model.weekly_reminder import WeeklyReminder
from fjormcord.bot.artping.util.message_util import log_info


def get_closing_times() -> Layout:
    # The next closing time of every reminder, the soonest first, in the reminders' own words
    now = datetime.now(timezone.utc)
    closings = sorted(
        ((weekly_reminder.next_closing(reminder, now), reminder) for reminder in weekly_reminder.REMINDERS),
        key=lambda closing_and_reminder: closing_and_reminder[0],
    )
    lines = [weekly_reminder.reminder_text(reminder, closing) for closing, reminder in closings]
    return Layout(("### Closing times", "\n".join(lines)))


async def send_reminders(client: discord.Client) -> str:
    # A debug command: posts every reminder to its channel now, whatever the day, with its next closing time
    now = datetime.now(timezone.utc)
    lines = [await _send_reminder(client, reminder, now) for reminder in weekly_reminder.REMINDERS]
    return log_info("\n".join(lines))


async def _send_reminder(client: discord.Client, reminder: WeeklyReminder, now: datetime) -> str:
    channel_id = reminder.channel_id(config.read_settings())
    if channel_id is None:
        return f"{reminder.name}: no channel is configured"
    try:
        sent = await weekly_reminder.send_reminder(client, reminder, weekly_reminder.next_closing(reminder, now))
    except discord.HTTPException as e:
        # Reported per reminder, so the others are still sent
        logging.warning("Sending the %s failed. %s", reminder.name, e)
        return f"{reminder.name}: sending to <#{channel_id}> failed"
    if not sent:
        return f"{reminder.name}: channel {channel_id} not found"
    return f"{reminder.name}: sent to <#{channel_id}>"
