import datetime
import logging
import discord

from datetime import time
from datetime import datetime
from discord.ext import tasks
from config import art_ping_config
from service.alias_service import AliasService
from service.art_ping_service import ArtPingService
from service.character_service import CharacterService
from service.currency_service import CurrencyService

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

CONFIG = art_ping_config.readConfig()

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

    async def on_message(self, message):
        discord_message: discord.Message = message

        content = discord_message.content
        if content is None or len(content) < 1:
            return

        content = discord_message.content.lower()
        if content == "thank you lorenz" or content == "thanks lorenz":
            await discord_message.channel.send(LORENZ_SMILE)

        if content == "chromk":
            await discord_message.channel.send(CHROMK)

        if discord_message.content[0] != '~':
            return

        logging.info(f"Received message from {discord_message.author.global_name}: {discord_message.content}")

        is_administrator = discord_message.author.guild_permissions.administrator
        if content.startswith(ART_PING):
            # Ping all users for corresponding characters
            out = await ArtPingService.doArtPing(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(ADD_PING):
            # Add ping from user
            out = ArtPingService.addPing(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(REMOVE_PING):
            # Remove ping from user
            out = ArtPingService.removePing(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(CHECK_PING):
            # Check user's pings 
            out = await ArtPingService.checkPing(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(ADD_CHARACTER):
            # Add character entry 
            out = MESSAGE_DENIED
            if is_administrator:
                out = CharacterService.addCharacterPing(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(REMOVE_CHARACTER):
            # Remove character entry
            out = MESSAGE_DENIED
            if is_administrator:
                out = CharacterService.removeCharacter(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(CHECK_CHARACTER):
            # Check character entry for aliases
            out = await CharacterService.checkCharacter(self, discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(ADD_ALIAS):
            # Add alias to character entry
            out = MESSAGE_DENIED
            if is_administrator:
                out = AliasService.addAlias(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(REMOVE_ALIAS):
            # Remove alias of character entry
            out = MESSAGE_DENIED
            if is_administrator:
                out = AliasService.removeAlias(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(ADD_CURRENCY):
            # Add new gacha currency
            out = MESSAGE_DENIED
            if is_administrator:
                out = CurrencyService.addCurrency(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(REMOVE_CURRENCY):
            # Remove currency
            out = MESSAGE_DENIED
            if is_administrator:
                out = CurrencyService.removeCurrency(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(SET_CURRENCY):
            # Set amount of given gacha currency for user 
            out = CurrencyService.setCurrency(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(CLEAR_CURRENCY):
            # Clear user's gacha currency from their wallet 
            out = CurrencyService.clearCurrency(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(CHECK_WALLET):
            # Check user's wallet of gacha currencies
            out = CurrencyService.checkWallet(discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(SCOREBOARD):
            # Show scoreboard of given gacha currency
            out = await CurrencyService.getScoreboard(self, discord_message)
            await discord_message.channel.send(out)
        elif content.startswith(HELP):
            # Help function to detail all the commands
            await ArtPingClient.show_help(discord_message)

    async def show_help(self: discord.Message):
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

        await self.channel.send(out)

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
