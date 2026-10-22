import logging
from collections.abc import Sequence

from fjormcord.bot.artping.database import get_database_connection


def has_ping(character_id: int, user_id: str) -> bool:
    return get_database_connection().execute("""
        SELECT 1
        FROM PINGS P
        WHERE P.CHARACTER_ID = ? AND P.USER = ?
        """, (character_id, user_id,)).fetchone() is not None


def get_art_ping_users(character_ids: Sequence[int]) -> list[str]:
    sql = """
        SELECT DISTINCT P.USER
        FROM PINGS P
        WHERE P.CHARACTER_ID IN ({})
        """.format(','.join("?" * len(character_ids)))

    # Each row holds just the one selected column
    return [user_id for (user_id,) in get_database_connection().execute(sql, list(character_ids))]


def add_ping(character_id: int, user_id: str):
    logging.info("Adding ping for character %s and user %s", character_id, user_id)

    with get_database_connection() as conn:
        conn.execute("""
            INSERT INTO PINGS (CHARACTER_ID, USER)
            VALUES (?, ?)
            """, (character_id, user_id,))


def remove_ping(character_id: int, user_id: str):
    logging.info("Removing ping for character %s and user %s", character_id, user_id)

    with get_database_connection() as conn:
        conn.execute("""
            DELETE FROM PINGS
            WHERE CHARACTER_ID = ? AND USER = ?
            """, (character_id, user_id,))


def get_pings_from_user(user_id: str) -> list[str]:
    rows = get_database_connection().execute("""
        SELECT C.NAME
        FROM PINGS P
        JOIN CHARACTERS C ON P.CHARACTER_ID = C.CHARACTER_ID
        WHERE P.USER = ?
        ORDER BY C.NAME
        """, (user_id,))

    return [name for (name,) in rows]
