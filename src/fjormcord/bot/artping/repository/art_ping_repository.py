import logging

from fjormcord.bot.artping.database import get_database_connection


def get_art_ping_row(character_id, user_id):
    return get_database_connection().execute("""
        SELECT P.CHARACTER_ID, P.USER
        FROM PINGS P
        WHERE P.CHARACTER_ID = ? AND P.USER = ?
        """, (character_id, user_id,)).fetchone()


def get_art_ping_users(character_ids):
    sql = """
        SELECT DISTINCT P.USER
        FROM PINGS P
        WHERE P.CHARACTER_ID IN ({})
        """.format(','.join("?" * len(character_ids)))

    return [row['USER'] for row in get_database_connection().execute(sql, list(character_ids))]


def add_ping(character_id, user_id):
    logging.info("Adding ping for character %s and user %s", character_id, user_id)

    with get_database_connection() as conn:
        conn.execute("""
            INSERT INTO PINGS (CHARACTER_ID, USER)
            VALUES (?, ?)
            """, (character_id, user_id,))


def remove_ping(character_id, user_id):
    logging.info("Removing ping for character %s and user %s", character_id, user_id)

    with get_database_connection() as conn:
        conn.execute("""
            DELETE FROM PINGS
            WHERE CHARACTER_ID = ? AND USER = ?
            """, (character_id, user_id,))


def get_pings_from_user(user_id):
    rows = get_database_connection().execute("""
        SELECT C.NAME
        FROM PINGS P
        LEFT JOIN CHARACTERS C ON P.CHARACTER_ID = C.CHARACTER_ID
        WHERE P.USER = ?
        """, (user_id,))

    return [row['NAME'] for row in rows]
