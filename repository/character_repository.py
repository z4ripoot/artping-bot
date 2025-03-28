import logging
from sqlite3 import OperationalError

from util.repository_util import get_database_connection

CONN = get_database_connection()
CURSOR = CONN.cursor()


def get_character_row(character_name):
    try:
        logging.info("Getting character %s", character_name)

        CURSOR.execute(f"""
            SELECT C.CHARACTER_ID, C.NAME
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) = ?
            """, (str(character_name).lower(),))
        result = CURSOR.fetchone()

        if result is None:
            raise Exception

        logging.info("Got character %s", character_name)

        return result
    except (OperationalError, Exception,) as e:
        logging.error("Failed to get character %s. %s", character_name, e)
        return None


def get_character_rows(character_names):
    try:
        logging.info("Getting characters %s", character_names)

        sql = """
            SELECT *
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) IN ({})
            """.format(','.join("?" * len(character_names)))

        parameters = (list(map(str.lower, character_names)))
        CURSOR.execute(sql, parameters)
        result = CURSOR.fetchall()

        if result is None:
            raise Exception

        logging.info("Got characters %s", character_names)

        return result
    except (OperationalError, Exception,) as e:
        logging.info("Failed to get characters %s. %s", character_names, e)
        return None


def get_missing_character_rows(character_names):
    try:
        logging.info("Getting missing characters %s", character_names)

        sql = """
            WITH INPUT(NAME) AS (
                VALUES {}
            )
            SELECT I.NAME
            FROM INPUT I
            WHERE I.NAME NOT IN (
                SELECT LOWER(C.NAME)
                FROM CHARACTERS C
            )
            """.format(','.join(("(?)",) * len(character_names)))

        parameters = (list(map(str.lower, character_names)))
        CURSOR.execute(sql, parameters)
        result = CURSOR.fetchall()

        if result is None:
            raise Exception

        logging.info("Got missing characters %s", character_names)

        return result
    except (OperationalError, Exception,) as e:
        logging.error("Failed to get missing characters %s. %s", character_names, e)
        return None


def get_character_name(character_name):
    try:
        logging.info("Getting character %s", character_name)

        CURSOR.execute(f"""
            SELECT C.NAME 
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) IS ?
            """, (str(character_name).lower(),))
        result = CURSOR.fetchone()[0]

        if result is None:
            raise Exception

        logging.info("Got character %s", character_name)

        return result
    except (OperationalError, Exception,) as e:
        logging.error("Failed to get character %s. %s", character_name, e)
        return None


def add_character(character_name):
    try:
        logging.info("Adding character %s", character_name)

        CURSOR.execute("""
            INSERT INTO CHARACTERS (NAME)
            VALUES (?)
            """, (character_name,))
        CONN.commit()

        logging.info("Added character %s", character_name)

        return True
    except (OperationalError, Exception,) as e:
        logging.error("Failed to add character %s. %s", character_name, e)
        return False


def remove_character(character_name):
    try:
        logging.info("Removing character %s", character_name)

        CURSOR.execute("""
            DELETE FROM CHARACTERS AS C
            WHERE LOWER(C.NAME) = ?
            """, (str(character_name).lower(),))
        CONN.commit()

        logging.info("Removed character %s", character_name)

        return True
    except (OperationalError, Exception,) as e:
        logging.error("Failed to remove character %s. %s", character_name, e)
        return False
