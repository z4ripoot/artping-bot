import configparser
import datetime
import logging
import discord
import pytz

from datetime import time
from datetime import datetime
from discord.ext import tasks
from service.alias_service import AliasService
from service.art_ping_service import ArtPingService
from service.character_service import CharacterService

ART_PING = "~artping"
ADD_PING = "~addping"
REMOVE_PING = "~removeping"
CHECK_PING = "~checkping"

ADD_CHARACTER = "~addcharacter"
REMOVE_CHARACTER = "~removecharacter"
CHECK_CHARACTER = "~checkcharacter"

ADD_ALIAS = "~addalias"
REMOVE_ALIAS = "~removealias"

HELP = "~help"

JST = pytz.timezone("Asia/Tokyo")

COLISEUM_ONE_HOUR_BEFORE_CLOSING_TIME = time(hour=7, minute=0, second=0, tzinfo=JST)
COLISEUM_FIVE_HOUR_BEFORE_CLOSING_TIME = time(hour=2, minute=0, second=0, tzinfo=JST)

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

class ArtPingClient(discord.Client):
    async def on_ready(self):
        logging.info("Initiating tasks")
        self.taskColiseumBeforeClosingNotification.start()
    
    async def on_message(self, message):
        discordMessage : discord.Message = message
        
        if (discordMessage.content[0] != '~'):
            return
        
        logging.info(f"Received message from {discordMessage.author}: {discordMessage.content}")
        
        content = discordMessage.content.lower()
        if content.startswith(ART_PING):
            # Ping all users for corresponding characters
            out = await ArtPingService.doArtPing(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(ADD_PING):
            # Add ping from user
            out = ArtPingService.addPing(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(REMOVE_PING):
            # Remove ping from user
            out = ArtPingService.removePing(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(CHECK_PING):
            # Check user's pings 
            out = ArtPingService.checkPing(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(ADD_CHARACTER):
            # Add character entry 
            out = CharacterService.addCharacterPing(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(REMOVE_CHARACTER):
            # Remove character entry
            out = CharacterService.removeCharacter(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(CHECK_CHARACTER):
            # Check character entry for aliases
            out = CharacterService.checkCharacter(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(ADD_ALIAS):
            # Add alias to character entry
            out = AliasService.addAlias(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(REMOVE_ALIAS):
            # Remove alias of character entry
            out = AliasService.removeAlias(discordMessage)
            await discordMessage.channel.send(out)
        elif content.startswith(HELP):
            # Help function to detail all the commands
            await ArtPingClient.showHelp(discordMessage)
        
    async def showHelp(message : discord.Message):
        out = 'Commands (content in brackets is what to add when using command):\n' \
            + '~addcharacter (character name): Add a character to the list of pingable characters \n'\
            + '~addping (character name): Call to add yourself to the ping list when this character is pinged \n'\
            + '~removeping (character name): Remove yourself from the ping list of this character \n'\
            + '~artping (character name): Ping users for art of this character \n'\
            + '~checkping: See which characters you are being pinged for \n'
        await message.channel.send(out)
        
    @tasks.loop(time=[COLISEUM_ONE_HOUR_BEFORE_CLOSING_TIME, COLISEUM_FIVE_HOUR_BEFORE_CLOSING_TIME])
    async def taskColiseumBeforeClosingNotification(self):
        datetimeJst = datetime.now(tz=JST)
        if (datetimeJst.weekday() == 1):
            channel_name =CONFIG.get('tasks', 'coliseum_notification_channel_name')
            channel = discord.utils.get(self.get_all_channels(), name=channel_name)
            if channel is None:
                logging.error("Invalid channel. Task will be skipped")
            else:
                closingTime = datetimeJst.replace(hour=8, minute=0, second=0, microsecond=0).timestamp().__floor__()
                message = f"Coliseum/Aether Raids closes <t:{closingTime}:R> at <t:{closingTime}:f>"
                
                logging.info(message)
                await channel.send(message)