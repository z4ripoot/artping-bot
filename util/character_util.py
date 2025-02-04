import logging

from repository.character_repository import CharacterRepository

def getCharacters(content):
    splitCharacters = content.split(" ")
    characterList = []
    
    logging.info("Getting characters")
    
    # Get all character entries
    for character in splitCharacters[1:]:
        characterList.append(character)
    
    logging.info("Found %d characters", len(characterList))
    
    return characterList

def getFirstCharacter(content):
    return content.split(" ")[1]

def getCharacterIds(characterRows):
    characterIds = []
    for row in characterRows:
        characterIds.append(row[0])
    return characterIds

def getCharacterNames(characterRows):
    characterNames = []
    for row in characterRows:
        characterNames.append(row[1])
    return characterNames