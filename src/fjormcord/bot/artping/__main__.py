import logging

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.bot import ArtPingClient


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(filename)s %(funcName)s %(message)s",
        handlers=[logging.StreamHandler()]
    )

    intents = discord.Intents.default()
    intents.message_content = True

    client = ArtPingClient(intents=intents)
    logging.info("Bot is running")
    client.run(config.read_config().get('discord', 'token'))


if __name__ == "__main__":
    main()
