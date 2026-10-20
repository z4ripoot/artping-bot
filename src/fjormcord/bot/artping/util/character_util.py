def get_character_ids(character_rows):
    character_ids = []
    for row in character_rows:
        character_ids.append(row[0])
    return character_ids


def get_character_names(character_rows):
    character_names = []
    for row in character_rows:
        character_names.append(row[1])
    return character_names
