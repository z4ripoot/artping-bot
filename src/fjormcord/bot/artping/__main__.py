from fjormcord.bot.artping import bot
import discord
import logging

from fjormcord.bot.artping import config

CONFIG = config.read_config()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s %(funcName)s %(message)s",
    handlers=[logging.StreamHandler()]
)

INTENTS = discord.Intents.default()
INTENTS.message_content = True

CLIENT = bot.ArtPingClient(intents=INTENTS)
logging.info("Bot is running")
CLIENT.run(CONFIG.get('discord', 'token'))
