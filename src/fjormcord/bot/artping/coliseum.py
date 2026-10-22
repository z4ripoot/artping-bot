import logging
from datetime import datetime, time, timezone

import discord
from discord.ext import tasks

from fjormcord.bot.artping import config

# Coliseum closes on Monday at 23:00 UTC; all scheduling is done in UTC, independent of the host's timezone
COLISEUM_CLOSING_TIME = time(hour=23, minute=0, second=0, tzinfo=timezone.utc)
COLISEUM_ONE_HOUR_BEFORE_CLOSING_TIME = time(hour=22, minute=0, second=0, tzinfo=timezone.utc)
COLISEUM_FIVE_HOUR_BEFORE_CLOSING_TIME = time(hour=18, minute=0, second=0, tzinfo=timezone.utc)

_channel_id = config.read_config().get('tasks', 'coliseum_notification_channel_id', fallback='')
COLISEUM_NOTIFICATION_CHANNEL_ID = int(_channel_id) if _channel_id else None


def start_coliseum_notification(client: discord.Client):
    if not COLISEUM_NOTIFICATION_CHANNEL_ID:
        logging.warning(
            "No channel ID is configured for Coliseum notifications. Coliseum notification task will not be initiated")
    elif not task_coliseum_before_closing_notification.is_running():
        # on_ready fires again after reconnects; starting a running loop raises
        logging.info("Initiating Coliseum notification task")
        task_coliseum_before_closing_notification.start(client)


@tasks.loop(time=[COLISEUM_ONE_HOUR_BEFORE_CLOSING_TIME, COLISEUM_FIVE_HOUR_BEFORE_CLOSING_TIME])
async def task_coliseum_before_closing_notification(client: discord.Client):
    now = datetime.now(timezone.utc)
    if now.weekday() == 0:
        channel = client.get_channel(COLISEUM_NOTIFICATION_CHANNEL_ID)
        if channel is None:
            logging.error("Channel %s not found. Task will be skipped", COLISEUM_NOTIFICATION_CHANNEL_ID)
        else:
            closing_time = int(datetime.combine(now.date(), COLISEUM_CLOSING_TIME).timestamp())
            message = f"Coliseum/Aether Raids closes <t:{closing_time}:R> at <t:{closing_time}:f>"

            logging.info(message)
            await channel.send(message)
