import logging

from fjormcord.bot.artping.database import execute, exists, get_database_connection


def has_alias(character_id: int, alias: str) -> bool:
    sql = """
        SELECT 1
        FROM ALIAS A
        WHERE A.CHARACTER_ID = ?
          AND A.ALIAS = ?
        """

    return exists(sql, (character_id, alias))


def get_aliases(character_id: int) -> list[str]:
    sql = """
        SELECT A.ALIAS
        FROM ALIAS A
        WHERE A.CHARACTER_ID = ?
        ORDER BY A.ALIAS
        """

    # Each row holds just the one selected column
    return [alias for (alias,) in get_database_connection().execute(sql, (character_id,))]


def add_alias(character_id: int, alias: str):
    sql = """
        INSERT INTO ALIAS (CHARACTER_ID, ALIAS)
        VALUES (?, ?)
        """

    logging.info("Adding alias %s for character %s", alias, character_id)
    execute(sql, (character_id, alias))


def remove_alias(character_id: int, alias: str):
    sql = """
        DELETE FROM ALIAS
        WHERE CHARACTER_ID = ?
          AND ALIAS = ?
        """

    logging.info("Removing alias %s for character %s", alias, character_id)
    execute(sql, (character_id, alias))


def set_primary_name(character_id: int, alias: str):
    # Swaps the name and the alias: the name becomes an alias, and the alias (as stored) the name
    add_name_as_alias = """
        INSERT INTO ALIAS (CHARACTER_ID, ALIAS)
        SELECT C.CHARACTER_ID, C.NAME
        FROM CHARACTERS C
        WHERE C.CHARACTER_ID = ?
        """
    rename = """
        UPDATE CHARACTERS
        SET NAME = (SELECT A.ALIAS FROM ALIAS A WHERE A.CHARACTER_ID = ? AND A.ALIAS = ?)
        WHERE CHARACTER_ID = ?
        """
    remove = """
        DELETE FROM ALIAS
        WHERE CHARACTER_ID = ?
          AND ALIAS = ?
        """

    logging.info("Making alias %s the name of character %s", alias, character_id)
    with get_database_connection() as conn:
        conn.execute(add_name_as_alias, (character_id,))
        conn.execute(rename, (character_id, alias, character_id))
        conn.execute(remove, (character_id, alias))
