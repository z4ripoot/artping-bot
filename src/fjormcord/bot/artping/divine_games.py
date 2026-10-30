import logging
from datetime import datetime, time, timezone

import discord
from discord.ext import tasks

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.util.task_util import get_task_channel, start_channel_task
from fjormcord.bot.artping.view.layout import to_view

# Divine Games ends on Saturday at 23:59 GMT+1, which is 22:59 UTC; all scheduling is done in UTC, independent of the
# host's timezone
CLOSING_TIME = time(hour=22, minute=59, second=0, tzinfo=timezone.utc)
ONE_HOUR_BEFORE_CLOSING_TIME = time(hour=21, minute=59, second=0, tzinfo=timezone.utc)
FIVE_HOUR_BEFORE_CLOSING_TIME = time(hour=17, minute=59, second=0, tzinfo=timezone.utc)
SATURDAY = 5


def start_divine_games_notification(client: discord.Client):
    start_channel_task(
        task_divine_games_before_closing_notification,
        client,
        config.read_settings().divine_games_channel_id,
        "Divine Games notification",
    )


@tasks.loop(time=[ONE_HOUR_BEFORE_CLOSING_TIME, FIVE_HOUR_BEFORE_CLOSING_TIME])
async def task_divine_games_before_closing_notification(client: discord.Client):
    # The loop only survives network errors: any other exception, e.g. a missing permission, would stop it for good
    try:
        await _send_notification(client)
    except Exception:
        logging.exception("Sending the Divine Games notification failed. Task will be skipped")


async def _send_notification(client: discord.Client):
    now = datetime.now(timezone.utc)
    if now.weekday() == SATURDAY:
        channel = get_task_channel(client, config.read_settings().divine_games_channel_id)
        if channel is not None:
            closing_time = int(datetime.combine(now.date(), CLOSING_TIME).timestamp())
            message = f"Divine Games ends <t:{closing_time}:R> at <t:{closing_time}:f>"

            logging.info(message)
            await channel.send(view=to_view(Layout((message,))))
