import logging

import discord
from discord.ext import tasks


def start_channel_task(task: tasks.Loop, client: discord.Client, channel_id: int | None, name: str):
    # Starts a task that posts to a channel, unless no channel is configured for it; on_ready fires again after
    # reconnects, and starting a running loop raises, so it is started once
    if not channel_id:
        logging.warning("No channel ID is configured for the %s task, so it will not be initiated", name)
    elif not task.is_running():
        logging.info("Initiating the %s task", name)
        task.start(client)


def get_task_channel(client: discord.Client, channel_id: int):
    # The channel a task posts to; None, and logged, when the bot can't see it, and the task skips this time
    channel = client.get_channel(channel_id)
    if channel is None:
        logging.error("Channel %s not found. Task will be skipped", channel_id)
    return channel
