import logging

from fjormcord.bot.artping.database import get_database_connection
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


def add_character(character_name: str):
    sql = """
        INSERT INTO CHARACTERS (NAME)
        VALUES (?)
        """

    logging.info("Adding character %s", character_name)
    with get_database_connection() as conn:
        conn.execute(sql, (character_name,))


def remove_character(character_id: int):
    sql = """
        DELETE FROM CHARACTERS
        WHERE CHARACTER_ID = ?
        """

    logging.info("Removing character %s", character_id)
    with get_database_connection() as conn:
        conn.execute(sql, (character_id,))
