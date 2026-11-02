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
        handlers=[logging.StreamHandler()],
    )

    token = get_token()

    # Opening the database applies pending migrations; it will fail fast when database migration fails
    database.get_database_connection()

    intents = discord.Intents.default()
    intents.message_content = True

    client = ArtPingClient(intents=intents)
    logging.info("Bot is running")
    client.run(token)


def get_token() -> str:
    # A missing config.ini or setting stops the bot with what is wrong, see config.example.ini
    try:
        token = config.read_settings().discord_token
    except (OSError, configparser.Error, ValueError) as e:
        sys.exit(f"Invalid configuration: {e}")
    if not token:
        sys.exit("No Discord token configured. Create config.ini with your bot's token, see README.md")
    return token


if __name__ == "__main__":
    main()
