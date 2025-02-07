import logging
import discord

from repository.character_repository import CharacterRepository
from util.character_util import getFirstCharacter

class CharacterService():
    def addCharacterPing(message: discord.Message):
        character = getFirstCharacter(message.content)
        
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
        character = getFirstCharacter(message.content)
        
        if not CharacterRepository.getCharacter(character):
            logging.info("Character %s doesn't exist", character)
            return f"Character {character} doesn't exist"
        
        logging.info("Removing character %s", character)
        
        entry = CharacterRepository.getCharacter(character)
        isRemoved = CharacterRepository.removeCharacter(character)
        
        if isRemoved:
            return f"{entry} has been removed"
        else:
            return f"Failed to remove character {entry}"
        
    def checkCharacter(message: discord.Message):
        character = getFirstCharacter(message.content)
        
        if not CharacterRepository.getCharacter(character):
            logging.info("Character %s doesn't exist", character)
            return f"Character {character} doesn't exist"
        
        logging.info("Checking for character %s", character)
        
        entry = CharacterRepository.getCharacter(character)
        
        if entry:
            return f"Character entry found for {entry}"
        else:
            return f"Failed to check character {character}"