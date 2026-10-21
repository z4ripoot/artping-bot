import logging

from fjormcord.bot.artping.database import get_database_connection


def get_character_row(character_name):
    return get_database_connection().execute("""
        SELECT C.CHARACTER_ID, C.NAME
        FROM CHARACTERS C
        WHERE C.NAME = ?
        """, (character_name,)).fetchone()


def get_character_rows(character_names):
    sql = """
        SELECT C.CHARACTER_ID, C.NAME
        FROM CHARACTERS C
        WHERE C.NAME IN ({})
        """.format(','.join("?" * len(character_names)))

    return get_database_connection().execute(sql, list(character_names)).fetchall()


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
