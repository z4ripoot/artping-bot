import configparser
import logging
import sys

import discord

from fjormcord.bot.artping import config, database
from fjormcord.bot.artping.bot import ArtPingClient


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(filename)s %(funcName)s %(message)s",
        handlers=[logging.StreamHandler()]
    )

    # A missing config.ini or setting stops the bot with what is wrong, see config.example.ini
    try:
        token = config.read_settings().discord_token
    except (OSError, configparser.Error, ValueError) as e:
        sys.exit(f"Invalid configuration: {e}")
    if not token:
        sys.exit("No Discord token configured. Create config.ini with your bot's token, see README.md")

    # Opening the database applies pending migrations; a failing one stops the bot here instead of failing every command
    database.get_database_connection()

    intents = discord.Intents.default()
    intents.message_content = True

    client = ArtPingClient(intents=intents)
    logging.info("Bot is running")
    client.run(token)


if __name__ == "__main__":
    main()
