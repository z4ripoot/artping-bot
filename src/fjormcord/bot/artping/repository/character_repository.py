from fjormcord.bot.artping.database import execute, fetch_names, fetch_one, get_database_connection
from fjormcord.bot.artping.model.character import Character

_SELECT_CHARACTER = """
    SELECT C.CHARACTER_ID AS id, C.NAME AS name
    FROM CHARACTERS C
    """


def get_character(name: str) -> Character | None:
    where = """
        WHERE C.NAME = ?
           OR C.CHARACTER_ID IN (SELECT A.CHARACTER_ID FROM ALIAS A WHERE A.ALIAS = ?)
        """

    return fetch_one(Character, _SELECT_CHARACTER + where, (name, name))


def get_character_by_id(character_id: int) -> Character | None:
    return fetch_one(Character, _SELECT_CHARACTER + "WHERE C.CHARACTER_ID = ?", (character_id,))


def get_all_names(prefix: str = "", limit: int = -1) -> list[str]:
    return fetch_names("SELECT C.NAME FROM CHARACTERS C UNION SELECT A.ALIAS FROM ALIAS A", prefix, limit)


def add_character(character_name: str) -> int:
    sql = """
        INSERT INTO CHARACTERS (NAME)
        VALUES (?)
        """

    with get_database_connection() as conn:
        return conn.execute(sql, (character_name,)).lastrowid


def remove_character(character_id: int):
    sql = """
        DELETE FROM CHARACTERS
        WHERE CHARACTER_ID = ?
        """

    execute(sql, (character_id,))
