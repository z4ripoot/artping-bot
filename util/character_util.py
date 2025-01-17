
def getCharacters(content):
    splitCharacters = content.split(" ")
    characterList = []
    # Get all character entries
    for character in splitCharacters[1:]:
        characterList.append(character)
    return characterList

def getFirstCharacter(content):
    return content.split(" ")[1]