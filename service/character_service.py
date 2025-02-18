import logging
import discord

from repository.art_ping_repository import ArtPingRepository
from repository.character_repository import CharacterRepository
from util.message_util import getFirst

class CharacterService():
    def addCharacterPing(message: discord.Message):
        character = getFirst(message.content)
        
        if character is None:
            logging.info("Failed to add character")
            return "Failed to add character"
        
        if CharacterRepository.getCharacter(character):
            logging.info("Character %s already exists", character)
            return f"Failed to add character {character}. Character {character} already exists"
        
        logging.info("Adding character %s", character)
        
        isAdded = CharacterRepository.addCharacter(character)
        
        if isAdded:
            return f"{character} has been added"
        else:
            return f"Failed to add character {character}"
        
    def removeCharacter(message: discord.Message):
        character = getFirst(message.content)
        
        if character is None:
            logging.info("Failed to remove character")
            return "Failed to remove character"
        
        entry = CharacterRepository.getCharacter(character)
        
        if entry is None:
            logging.info("Character %s doesn't exist", character)
            return f"Character {character} doesn't exist"
        
        logging.info("Removing character %s", character)
        
        isRemoved = CharacterRepository.removeCharacter(character)
        
        if isRemoved:
            return f"{entry} has been removed"
        else:
            return f"Failed to remove character {entry}"
        
    async def checkCharacter(self : discord.Client, message: discord.Message):
        character = getFirst(message.content)
        
        if character is None:
            logging.info("Failed to check character")
            return "Failed to check character"
        
        logging.info("Checking for character %s", character)

        characterRow = CharacterRepository.getCharacterRow(character)
        
        if characterRow is None:
            logging.info("Failed to check character %s", character)
            return f"Failed to check character {character}"
        
        characterId = characterRow[0]
        characterName = characterRow[1]
        
        logging.info("Character %s has been found", characterName)
        
        userIds = ArtPingRepository.getArtPings((characterId,))
        usernames = []
        
        for userId in userIds:
            user : discord.User = await self.fetch_user(userId) 
            usernames.append(user.global_name)
        
        if characterId:
            userList = ", ".join(usernames)
            return f"Character entry found for {characterName}\n" \
            + f"Users: {userList}"
        else:
            return f"Failed to check character {character}"