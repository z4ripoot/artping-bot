from fjormcord.bot.artping.database import execute, get_database_connection
from fjormcord.bot.artping.model.character import Character


def get_character(name: str) -> Character | None:
    # Finds the character by its name or one of its aliases; a name and an alias never collide
    sql = """
        SELECT C.CHARACTER_ID AS id, C.NAME AS name
        FROM CHARACTERS C
        WHERE C.NAME = ?
           OR C.CHARACTER_ID IN (SELECT A.CHARACTER_ID FROM ALIAS A WHERE A.ALIAS = ?)
        """

    row = get_database_connection().execute(sql, (name, name)).fetchone()
    return Character(**row) if row else None


def get_all_names(prefix: str = "", limit: int = -1) -> list[str]:
    # The names of all characters and all aliases starting with prefix, ignoring case, for autocompletion; a limit
    # of -1 means no limit
    sql = """
        SELECT N.NAME
        FROM (SELECT C.NAME FROM CHARACTERS C UNION SELECT A.ALIAS FROM ALIAS A) N
        WHERE SUBSTR(N.NAME, 1, LENGTH(?)) = ? COLLATE NOCASE
        ORDER BY N.NAME COLLATE NOCASE
        LIMIT ?
        """

    # Each row holds just the one selected column
    return [name for (name,) in get_database_connection().execute(sql, (prefix, prefix, limit))]


def add_character(character_name: str):
    sql = """
        INSERT INTO CHARACTERS (NAME)
        VALUES (?)
        """

    execute(sql, (character_name,))


def remove_character(character_id: int):
    sql = """
        DELETE FROM CHARACTERS
        WHERE CHARACTER_ID = ?
        """

    execute(sql, (character_id,))
