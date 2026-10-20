import logging
from sqlite3 import OperationalError

from fjormcord.bot.artping.database import get_database_connection, get_ids


def get_art_ping_row(character_id, user_id):
    cursor = get_database_connection().cursor()

    try:
        logging.info("Getting art ping")

        cursor.execute("""
            SELECT P.CHARACTER_ID, P.USER
            FROM PINGS P
            WHERE P.CHARACTER_ID = ? AND P.USER = ?
            """, (character_id, user_id,))
        user_ids = cursor.fetchone()[0]

        logging.info("Got art ping")

        return user_ids
    except (OperationalError, Exception,) as e:
        logging.error("Failed to get art ping. %s", e)
        return None


def get_art_ping_users(character_ids):
    cursor = get_database_connection().cursor()

    try:
        logging.info("Getting pings")

        sql = """
            SELECT DISTINCT P.USER
            FROM PINGS P
            WHERE P.CHARACTER_ID IN ({})
            """.format(','.join("?" * len(character_ids)))
        cursor.execute(sql, character_ids)
        user_ids = get_ids(cursor.fetchall())

        logging.info("Got pings")

        return user_ids
    except (OperationalError, Exception,) as e:
        logging.error("Failed to ping characters. %s", e)
        return None


def add_ping(character_id, user_id):
    cursor = get_database_connection().cursor()

    try:
        logging.info("Adding ping")

        cursor.execute("""
            INSERT INTO PINGS (CHARACTER_ID, USER)
            VALUES (?, ?)
            """, (character_id, user_id,))
        cursor.connection.commit()

        logging.info("Added ping")

        return True
    except (OperationalError, Exception,) as e:
        logging.error("Failed to add ping. %s", e)
        return False


def remove_ping(character_id, user_id):
    cursor = get_database_connection().cursor()

    try:
        logging.info("Removing ping")

        cursor.execute("""
            DELETE FROM PINGS AS P
            WHERE P.CHARACTER_ID = ?
            AND P.USER = ?
            """, (character_id, user_id,))
        cursor.connection.commit()

        logging.info("Removed ping")

        return True
    except (OperationalError, Exception,) as e:
        logging.error("Failed to remove ping. %s", e)
        return False


def get_pings_from_user(user_id):
    cursor = get_database_connection().cursor()

    try:
        logging.info(f"Getting user pings for {user_id}")

        cursor.execute("""
            SELECT C.NAME
            FROM PINGS P
            LEFT JOIN CHARACTERS C ON
            P.CHARACTER_ID = C.CHARACTER_ID
            WHERE P.USER = ?
            """, (user_id,))
        pings = get_ids(cursor.fetchall())

        logging.info(f"Got art pings for user {user_id}")

        return pings
    except (OperationalError, Exception,) as e:
        logging.error("Failed to get users ping. %s", e)
        return None
