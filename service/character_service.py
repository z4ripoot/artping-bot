import logging
from attr import Out
import discord

from repository.art_ping_repository import ArtPingRepository
from repository.character_repository import CharacterRepository
from util.message_util import getFirst

class CharacterService():
    def addCharacterPing(message: discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = "Failed to add character"
            logging.warning(out)
            return out
        
        if CharacterRepository.getCharacterName(entry):
            out = f"Failed to add character {entry}. Character {entry} already exists"
            logging.warning(out)
            return out
        
        logging.info("Adding character %s", entry)
        
        isAdded = CharacterRepository.addCharacter(entry)
        
        if isAdded:
            out = f"{entry} has been added"
            logging.warning(out)
            return out
        else:
            out = f"Failed to add character {entry}"
            logging.warning(out)
            return out
        
    def removeCharacter(message: discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = f"Failed to remove character"
            logging.warning(out)
            return out
        
        character = CharacterRepository.getCharacterName(entry)
        
        if character is None:
            out = f"Character {entry} doesn't exist"
            logging.warning(out)
            return out
        
        logging.info("Removing character %s", character)
        
        isRemoved = CharacterRepository.removeCharacter(character)
        
        if isRemoved:
            out = f"{character} has been removed"
            logging.info(out)
            return out
        else:
            out = f"Failed to remove character {character}"
            logging.warning(out)
            return out
        
    async def checkCharacter(self : discord.Client, message: discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = "Failed to check character"
            logging.warning(out)
            return out
        
        logging.info("Checking for character %s", entry)

        characters = CharacterRepository.getCharacterRow(entry)
        
        if characters is None:
            out = f"Failed to check character {entry}"
            logging.warning(out)
            return out
        
        characterId = characters[0]
        characterName = characters[1]
        
        logging.info("Character %s has been found", characterName)
        
        userIds = ArtPingRepository.getArtPingUsers((characterId,))
        usernames = []
        
        for userId in userIds:
            user : discord.User = await self.fetch_user(userId) 
            usernames.append(user.global_name)
        
        if characterId:
            userList = ", ".join(usernames)
            return f"Character entry found for {characterName}\n" \
            + f"Users: {userList}"
        else:
            return f"Failed to check character {entry}"