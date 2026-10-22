import logging
from dataclasses import dataclass

from fjormcord.bot.artping.database import get_database_connection


@dataclass(frozen=True)
class Character:
    id: int
    name: str


def _to_character(row):
    return Character(id=row['CHARACTER_ID'], name=row['NAME'])


def get_character(character_name):
    row = get_database_connection().execute("""
        SELECT C.CHARACTER_ID, C.NAME
        FROM CHARACTERS C
        WHERE C.NAME = ?
        """, (character_name,)).fetchone()

    return _to_character(row) if row else None


def get_characters(character_names):
    sql = """
        SELECT C.CHARACTER_ID, C.NAME
        FROM CHARACTERS C
        WHERE C.NAME IN ({})
        """.format(','.join("?" * len(character_names)))

    return [_to_character(row) for row in get_database_connection().execute(sql, list(character_names))]


def add_character(character_name):
    logging.info("Adding character %s", character_name)

    with get_database_connection() as conn:
        conn.execute("""
            INSERT INTO CHARACTERS (NAME)
            VALUES (?)
            """, (character_name,))


def remove_character(character_id):
    logging.info("Removing character %s", character_id)

    with get_database_connection() as conn:
        conn.execute("""
            DELETE FROM CHARACTERS
            WHERE CHARACTER_ID = ?
            """, (character_id,))
