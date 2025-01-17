import logging
import discord
from repository.art_ping_repository import ArtPingRepository
from repository.character_repository import CharacterRepository
from service.character_service import CharacterService
from util.character_util import getCharacterIds, getCharacterNames, getCharacters, getFirstCharacter

class ArtPingService():
    def doArtPing(message : discord.Message):
        characters = getCharacters(message.content)
        
        logging.info("Pinging characters %s", characters)
        
        characterRows = CharacterRepository.getCharacterRows(characters)
        users = ArtPingRepository.getArtPings(getCharacterIds(characterRows))
        
        content = ", ".join(getCharacterNames(characterRows))
        content += ": "
        
        for user in users:
            content += "<@" + user + ">"
            
        return content
    
    def addPing(message: discord.Message):
        characters = getCharacters(message.content)
        
        if not characters:
            return "Character is missing. Please add the character to be pinged for"
        elif len(characters) > 1:
            return "More than one character detected. Please add the characters separately"
        
        character = getFirstCharacter(message.content)
        
        if not CharacterRepository.getCharacter(character):
            logging.info("Character %s doesn't exist", character)
            return f"Character {character} doesn't exist"
        
        userId = str(message.author.id)
        characterRow = CharacterRepository.getCharacterRow(character)
        characterId = characterRow[0]
        character = characterRow[1]
        
        if ArtPingRepository.getArtPing(characterId, userId):
            logging.info("Ping for %s already exists", character)
            return f"Ping for {character} already exists"
        
        logging.info("Adding ping for %s", character)
        isAdded = ArtPingRepository.addPing(characterId, userId)
        
        if isAdded:
            return f"A ping for {character} has been added"
        else: 
            return f"Failed to add ping for {character}"
    
    def removePing(message: discord.Message):
        characters = getCharacters(message.content)
        
        if not characters:
            return "Character is missing. Please add the character you would like to remove"
        elif len(characters) > 1:
            return "More than one character detected. Please remove the characters separately"
        
        character = getFirstCharacter(message.content)
        
        if not CharacterRepository.getCharacter(character):
            logging.info("Character %s doesn't exist", character)
            return f"Character {character} doesn't exist"
        
        userId = str(message.author.id)
        characterRow = CharacterRepository.getCharacterRow(character)
        characterId = characterRow[0]
        character = characterRow[1]
        
        if not ArtPingRepository.getArtPing(characterId, userId):
            logging.info("Ping for %s doesn't exist", character)
            return f"Ping for {character} doesn't exist"
        
        logging.info("Removing ping for %s", character)
        isRemoved = ArtPingRepository.removePing(characterId, userId)
        
        if isRemoved:
            return f"Ping for {character} has been removed"
        else:
            return f"Failed to remove ping for {character}"