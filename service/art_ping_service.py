import logging
import discord
from repository.art_ping_repository import ArtPingRepository
from repository.character_repository import CharacterRepository
from util.character_util import getCharacterIds, getCharacterNames
from util.message_util import getEntries, getFirst

class ArtPingService():
    async def doArtPing(message : discord.Message):
        entries = getEntries(message.content)
        
        if not entries:
            out = "Character is missing. Please add the character to your ping"
            logging.warning(out)
            return out
        
        missingCharacters = await ArtPingService.getMissingCharacters(message, entries)        
        characters = list(filter(lambda character: character not in missingCharacters, entries))
        
        logging.info("Pinging characters %s", characters)
        
        if not characters:
            out = "Character is missing. Please add the character to your ping"
            logging.warning(out)
            return out
        
        characterRows = CharacterRepository.getCharacterRows(characters)
        userRows = ArtPingRepository.getArtPingUsers(getCharacterIds(characterRows))
        
        out = ", ".join(getCharacterNames(characterRows))
        out += ": "
        
        users = []
        for row in userRows:
            users.append(f"<@{row}>")
            
        out += " ".join(users)
            
        logging.info("Pinged %s users for %s", len(users), characters)
        return out
    
    def addPing(message: discord.Message):
        entries = getEntries(message.content)
        
        if not entries:
            out = "Character is missing. Please add the character to be pinged for"
            logging.warning(out)
            return out
        elif len(entries) > 1:
            out = "More than one character detected. Please add the characters separately"
            logging.warning(out)
            return out
        
        entry = getFirst(message.content)
        
        if not CharacterRepository.getCharacterName(entry):
            out = f"Character {entry} doesn't exist"
            logging.warning(out)
            return out
        
        userId = str(message.author.id)
        character = CharacterRepository.getCharacterRow(entry)
        characterId = character[0]
        characterName = character[1]
        
        if ArtPingRepository.getArtPingRow(characterId, userId):
            out = f"Ping for {characterName} already exists"
            logging.info(out)
            return out
        
        logging.info("Adding ping for %s", characterName)
        isAdded = ArtPingRepository.addPing(characterId, userId)
        
        if isAdded:
            out = f"A ping for {characterName} has been added"
            logging.info(out)
            return out
        else: 
            out = f"Failed to add ping for {entry}"
            logging.warning(out)
            return out
    
    def removePing(message: discord.Message):
        entries = getEntries(message.content)
        
        if not entries:
            return "Character is missing. Please add the character you would like to remove"
        elif len(entries) > 1:
            return "More than one character detected. Please remove the characters separately"
        
        entry = getFirst(message.content)
        
        if not CharacterRepository.getCharacterName(entry):
            out = f"Character {entry} doesn't exist"
            logging.warning(out)
            return out
        
        userId = str(message.author.id)
        character = CharacterRepository.getCharacterRow(entry)
        characterId = character[0]
        characterName = character[1]
        
        if not ArtPingRepository.getArtPingRow(characterId, userId):
            out = f"Ping for {characterName} doesn't exist"
            logging.warning(out)
            return out
        
        logging.info("Removing ping for %s", characterName)
        isRemoved = ArtPingRepository.removePing(characterId, userId)
        
        if isRemoved:
            out = f"Ping for {characterName} has been removed"
            logging.info(out)
            return out
        else:
            out = f"Failed to remove ping for {characterName}"
            logging.warning(out)
            return out
        
    async def checkPing(message: discord.Message):
        userId = str(message.author.id)
        
        logging.info(f"Getting pings for user {userId}")
        
        pings = ArtPingRepository.getPingsFromUser(userId)
        
        logging.info(f"Got pings for user {userId}")
        
        return "\n".join(pings)
        
    async def getMissingCharacters(message: discord.Message, characters):
        logging.info("Checking for missing characters")
        
        missingCharacters = []
        missingCharacterRows = CharacterRepository.getMissingCharacterRows(characters)
        
        if missingCharacterRows:
            logging.info("Missing characters found")
            
            for row in missingCharacterRows:
                missingCharacters.append(row[0])
            await message.channel.send(f"No character entry for {', '.join(missingCharacters)}")
            
        return missingCharacters