import logging
from datetime import datetime, time, timezone

import discord
from discord.ext import tasks

from fjormcord.bot.artping import config

# Coliseum closes on Monday at 23:00 UTC; all scheduling is done in UTC, independent of the host's timezone
CLOSING_TIME = time(hour=23, minute=0, second=0, tzinfo=timezone.utc)
ONE_HOUR_BEFORE_CLOSING_TIME = time(hour=22, minute=0, second=0, tzinfo=timezone.utc)
FIVE_HOUR_BEFORE_CLOSING_TIME = time(hour=18, minute=0, second=0, tzinfo=timezone.utc)

NOTIFICATION_CHANNEL_ID = config.read_settings().coliseum_channel_id


def start_coliseum_notification(client: discord.Client):
    if not NOTIFICATION_CHANNEL_ID:
        logging.warning(
            "No channel ID is configured for Coliseum notifications. Coliseum notification task will not be initiated")
    elif not task_coliseum_before_closing_notification.is_running():
        # on_ready fires again after reconnects; starting a running loop raises
        logging.info("Initiating Coliseum notification task")
        task_coliseum_before_closing_notification.start(client)


@tasks.loop(time=[ONE_HOUR_BEFORE_CLOSING_TIME, FIVE_HOUR_BEFORE_CLOSING_TIME])
async def task_coliseum_before_closing_notification(client: discord.Client):
    now = datetime.now(timezone.utc)
    if now.weekday() == 0:
        channel = client.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            logging.error("Channel %s not found. Task will be skipped", NOTIFICATION_CHANNEL_ID)
        else:
            closing_time = int(datetime.combine(now.date(), CLOSING_TIME).timestamp())
            message = f"Coliseum/Aether Raids closes <t:{closing_time}:R> at <t:{closing_time}:f>"

            logging.info(message)
            await channel.send(message)
