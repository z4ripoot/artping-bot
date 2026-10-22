import logging
import sqlite3
from collections.abc import Sequence

from fjormcord.bot.artping.database import get_database_connection
from fjormcord.bot.artping.model.character import Character


def _to_character(row: sqlite3.Row) -> Character:
    return Character(id=row['CHARACTER_ID'], name=row['NAME'])


def get_character(character_name: str) -> Character | None:
    row = get_database_connection().execute("""
        SELECT C.CHARACTER_ID, C.NAME
        FROM CHARACTERS C
        WHERE C.NAME = ?
        """, (character_name,)).fetchone()

    return _to_character(row) if row else None


def get_characters(character_names: Sequence[str]) -> list[Character]:
    sql = """
        SELECT C.CHARACTER_ID, C.NAME
        FROM CHARACTERS C
        WHERE C.NAME IN ({})
        """.format(','.join("?" * len(character_names)))

    return [_to_character(row) for row in get_database_connection().execute(sql, list(character_names))]


def add_character(character_name: str):
    logging.info("Adding character %s", character_name)

    with get_database_connection() as conn:
        conn.execute("""
            INSERT INTO CHARACTERS (NAME)
            VALUES (?)
            """, (character_name,))


def remove_character(character_id: int):
    logging.info("Removing character %s", character_id)

    with get_database_connection() as conn:
        conn.execute("""
            DELETE FROM CHARACTERS
            WHERE CHARACTER_ID = ?
            """, (character_id,))
