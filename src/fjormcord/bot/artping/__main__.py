import logging
import sys

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.bot import ArtPingClient


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(filename)s %(funcName)s %(message)s",
        handlers=[logging.StreamHandler()]
    )

    token = config.read_config().get('discord', 'token', fallback='')
    if not token:
        sys.exit("No Discord token configured. Create config.ini with your bot's token, see README.md")

    intents = discord.Intents.default()
    intents.message_content = True

    client = ArtPingClient(intents=intents)
    logging.info("Bot is running")
    client.run(token)


if __name__ == "__main__":
    main()
