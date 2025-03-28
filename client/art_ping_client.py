import datetime
import logging
import discord

from datetime import time
from datetime import datetime
from discord.ext import tasks
from config import art_ping_config
from service.alias_service import add_alias, remove_alias
from service.art_ping_service import do_art_ping, add_ping, remove_ping, check_ping
from service.character_service import add_character_ping, remove_character, check_character
from service.currency_service import add_currency, remove_currency, set_currency, clear_currency, check_wallet, \
    get_scoreboard

MESSAGE_DENIED = "You do not have the permissions for this command"

ART_PING = "~artping"
ADD_PING = "~addping"
REMOVE_PING = "~removeping"
CHECK_PING = "~checkping"

ADD_CHARACTER = "~addcharacter"
REMOVE_CHARACTER = "~removecharacter"
CHECK_CHARACTER = "~checkcharacter"

ADD_ALIAS = "~addalias"
REMOVE_ALIAS = "~removealias"

ADD_CURRENCY = "~addcurrency"
REMOVE_CURRENCY = "~removecurrency"
SET_CURRENCY = "~setcurrency"
CLEAR_CURRENCY = "~clearcurrency"
CHECK_WALLET = "~checkwallet"
SCOREBOARD = "~scoreboard"

HELP = "~help"

COLISEUM_ONE_HOUR_BEFORE_CLOSING_TIME = time(hour=22, minute=0, second=0)
COLISEUM_FIVE_HOUR_BEFORE_CLOSING_TIME = time(hour=18, minute=0, second=0)

CONFIG = art_ping_config.read_config()

COLISEUM_NOTIFICATION_CHANNEL_NAME = CONFIG.get('tasks', 'coliseum_notification_channel_name')
LORENZ_SMILE = CONFIG.get('emoji', 'lorenz_smile')

CHROMK_1 = CONFIG.get('emoji', 'chromk_1')
CHROMK_2 = CONFIG.get('emoji', 'chromk_2')
CHROMK_3 = CONFIG.get('emoji', 'chromk_3')
CHROMK_4 = CONFIG.get('emoji', 'chromk_4')
CHROMK_5 = CONFIG.get('emoji', 'chromk_5')
CHROMK_6 = CONFIG.get('emoji', 'chromk_6')
CHROMK_7 = CONFIG.get('emoji', 'chromk_7')
CHROMK_8 = CONFIG.get('emoji', 'chromk_8')
CHROMK_9 = CONFIG.get('emoji', 'chromk_9')
CHROMK_10 = CONFIG.get('emoji', 'chromk_10')
CHROMK_11 = CONFIG.get('emoji', 'chromk_11')
CHROMK_12 = CONFIG.get('emoji', 'chromk_12')
CHROMK = f'{CHROMK_1}{CHROMK_2}{CHROMK_3}{CHROMK_4}\n{CHROMK_5}{CHROMK_6}{CHROMK_7}{CHROMK_8}\n{CHROMK_9}{CHROMK_10}{CHROMK_11}{CHROMK_12}'


async def show_help(message: discord.Message):
    out = 'Commands (content in brackets is what to add when using command):\n' \
          + '~artping (character name): Ping users for art of this character \n' \
          + '~addping (character name): Call to add yourself to the ping list when this character is pinged \n' \
          + '~removeping (character name): Remove yourself from the ping list of this character \n' \
          + '~checkping: See which characters you are being pinged for \n' \
          + '~checkcharacter (character name): See which users are pinged for this character \n' \
          + '\n' \
          + 'Gacha Currency Commands:\n' \
          + '~setcurrency (currency name) (amount): Set the number of orbs, primos or any other currency that you have\n' \
          + '~clearcurrency (currency name): Clears the number you have saved for that particular currency\n' \
          + '~checkwallet: Shows a list of all currencies you have and their count\n' \
          + '~scoreboard (currency name): Shows a leaderboard of the specified currency\n'

    await message.channel.send(out)


class ArtPingClient(discord.Client):
    async def on_ready(self):
        logging.info("Initiating tasks")

        if COLISEUM_NOTIFICATION_CHANNEL_NAME is None:
            logging.warning(
                "No channel name is configured for Coliseum notifications. Coliseum notification task will not be initiated")
        else:
            logging.info("Initiating Coliseum notification task")
            self.task_coliseum_before_closing_notification.start()

        logging.info("Tasks are initiated")

    async def on_message(self, message: discord.Message):
        content = message.content
        if content is None or len(content) < 1:
            return

        content = message.content.lower()
        if content == "thank you lorenz" or content == "thanks lorenz":
            await message.channel.send(LORENZ_SMILE)

        if content == "chromk":
            await message.channel.send(CHROMK)

        if message.content[0] != '~':
            return

        logging.info(f"Received message from {message.author.global_name}: {message.content}")

        is_administrator = message.author.guild_permissions.administrator
        if content.startswith(ART_PING):
            # Ping all users for corresponding characters
            out = await do_art_ping(message)
            await message.channel.send(out)
        elif content.startswith(ADD_PING):
            # Add ping from user
            out = add_ping(message)
            await message.channel.send(out)
        elif content.startswith(REMOVE_PING):
            # Remove ping from user
            out = remove_ping(message)
            await message.channel.send(out)
        elif content.startswith(CHECK_PING):
            # Check user's pings 
            out = await check_ping(message)
            await message.channel.send(out)
        elif content.startswith(ADD_CHARACTER):
            # Add character entry 
            out = MESSAGE_DENIED
            if is_administrator:
                out = add_character_ping(message)
            await message.channel.send(out)
        elif content.startswith(REMOVE_CHARACTER):
            # Remove character entry
            out = MESSAGE_DENIED
            if is_administrator:
                out = remove_character(message)
            await message.channel.send(out)
        elif content.startswith(CHECK_CHARACTER):
            # Check character entry for aliases
            out = await check_character(self, message)
            await message.channel.send(out)
        elif content.startswith(ADD_ALIAS):
            # Add alias to character entry
            out = MESSAGE_DENIED
            if is_administrator:
                out = add_alias(message)
            await message.channel.send(out)
        elif content.startswith(REMOVE_ALIAS):
            # Remove alias of character entry
            out = MESSAGE_DENIED
            if is_administrator:
                out = remove_alias(message)
            await message.channel.send(out)
        elif content.startswith(ADD_CURRENCY):
            # Add new gacha currency
            out = MESSAGE_DENIED
            if is_administrator:
                out = add_currency(message)
            await message.channel.send(out)
        elif content.startswith(REMOVE_CURRENCY):
            # Remove currency
            out = MESSAGE_DENIED
            if is_administrator:
                out = remove_currency(message)
            await message.channel.send(out)
        elif content.startswith(SET_CURRENCY):
            # Set amount of given gacha currency for user 
            out = set_currency(message)
            await message.channel.send(out)
        elif content.startswith(CLEAR_CURRENCY):
            # Clear user's gacha currency from their wallet 
            out = clear_currency(message)
            await message.channel.send(out)
        elif content.startswith(CHECK_WALLET):
            # Check user's wallet of gacha currencies
            out = check_wallet(message)
            await message.channel.send(out)
        elif content.startswith(SCOREBOARD):
            # Show scoreboard of given gacha currency
            out = await get_scoreboard(self, message)
            await message.channel.send(out)
        elif content.startswith(HELP):
            # Help function to detail all the commands
            await show_help(message)

    @tasks.loop(time=[COLISEUM_ONE_HOUR_BEFORE_CLOSING_TIME, COLISEUM_FIVE_HOUR_BEFORE_CLOSING_TIME])
    async def task_coliseum_before_closing_notification(self):
        now = datetime.now()
        if now.weekday() == 0:
            channel = discord.utils.get(self.get_all_channels(), name=COLISEUM_NOTIFICATION_CHANNEL_NAME)
            if channel is None:
                logging.error("Invalid channel. Task will be skipped")
            else:
                closing_time = now.replace(hour=23, minute=0, second=0, microsecond=0).timestamp().__floor__()
                message = f"Coliseum/Aether Raids closes <t:{closing_time}:R> at <t:{closing_time}:f>"

                logging.info(message)
                await channel.send(message)
