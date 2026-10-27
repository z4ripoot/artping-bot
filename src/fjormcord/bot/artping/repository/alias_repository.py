from fjormcord.bot.artping.database import execute, exists, fetch_column, get_database_connection

_REMOVE_ALIAS = """
    DELETE FROM ALIAS
    WHERE CHARACTER_ID = ?
      AND ALIAS = ?
    """


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

    return fetch_column(sql, (character_id,))


def add_alias(character_id: int, alias: str):
    sql = """
        INSERT INTO ALIAS (CHARACTER_ID, ALIAS)
        VALUES (?, ?)
        """

    execute(sql, (character_id, alias))


def remove_alias(character_id: int, alias: str):
    execute(_REMOVE_ALIAS, (character_id, alias))


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

    with get_database_connection() as conn:
        conn.execute(add_name_as_alias, (character_id,))
        conn.execute(rename, (character_id, alias, character_id))
        conn.execute(_REMOVE_ALIAS, (character_id, alias))
