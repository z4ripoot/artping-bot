from repository.character_repository import CharacterRepository

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