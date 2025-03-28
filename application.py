import client.art_ping_client
import discord
import logging

from config import art_ping_config

CONFIG = art_ping_config.read_config()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s %(funcName)s %(message)s",
    handlers=[logging.StreamHandler()]
)

INTENTS = discord.Intents.default()
INTENTS.message_content = True

CLIENT = client.art_ping_client.ArtPingClient(intents=INTENTS)
logging.info("Bot is running")
CLIENT.run(CONFIG.get('discord', 'token'))
