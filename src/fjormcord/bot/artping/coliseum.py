import logging
from datetime import datetime, time, timezone

import discord
from discord.ext import tasks

from fjormcord.bot.artping import config
from fjormcord.bot.artping.util.task_util import get_task_channel, start_channel_task

# Coliseum closes on Monday at 23:00 UTC; all scheduling is done in UTC, independent of the host's timezone
CLOSING_TIME = time(hour=23, minute=0, second=0, tzinfo=timezone.utc)
ONE_HOUR_BEFORE_CLOSING_TIME = time(hour=22, minute=0, second=0, tzinfo=timezone.utc)
FIVE_HOUR_BEFORE_CLOSING_TIME = time(hour=18, minute=0, second=0, tzinfo=timezone.utc)

NOTIFICATION_CHANNEL_ID = config.read_settings().coliseum_channel_id


def start_coliseum_notification(client: discord.Client):
    start_channel_task(task_coliseum_before_closing_notification, client, NOTIFICATION_CHANNEL_ID,
                       "Coliseum notification")


@tasks.loop(time=[ONE_HOUR_BEFORE_CLOSING_TIME, FIVE_HOUR_BEFORE_CLOSING_TIME])
async def task_coliseum_before_closing_notification(client: discord.Client):
    now = datetime.now(timezone.utc)
    if now.weekday() == 0:
        channel = get_task_channel(client, NOTIFICATION_CHANNEL_ID)
        if channel is not None:
            closing_time = int(datetime.combine(now.date(), CLOSING_TIME).timestamp())
            message = f"Coliseum/Aether Raids closes <t:{closing_time}:R> at <t:{closing_time}:f>"

            logging.info(message)
            await channel.send(message)
