import logging
from sqlite3 import OperationalError

from util.repository_util import get_database_connection

CONN = get_database_connection()
CURSOR = CONN.cursor()


def get_currency_row(currency_name):
    try:
        logging.info("Getting currency %s", currency_name)

        CURSOR.execute(f"""
            SELECT C.GACHA_CURRENCY_ID, C.NAME
            FROM GACHA_CURRENCY C
            WHERE LOWER(C.NAME) = ?
            """, (str(currency_name).lower(),))

        result = CURSOR.fetchone()
        if result is None:
            raise Exception

        logging.info("Got currency %s", currency_name)

        return result
    except (OperationalError, Exception) as e:
        logging.error("Failed to get currency %s. %s", currency_name, e)
        return None


def add_currency(currency_name):
    try:
        logging.info("Adding currency %s", currency_name)

        CURSOR.execute("""
            INSERT INTO GACHA_CURRENCY (NAME)
            VALUES (?)
            """, (currency_name,))
        CONN.commit()

        logging.info("Added currency %s", currency_name)

        return True
    except (OperationalError, Exception) as e:
        logging.error("Failed to add currency %s. %s", currency_name, e)
        return False


def remove_currency(currency_id):
    try:
        logging.info("Removing currency %s", currency_id)

        CURSOR.execute("""
            DELETE FROM GACHA_CURRENCY AS C
            WHERE C.GACHA_CURRENCY_ID = ?
            """, (currency_id,))
        CONN.commit()

        logging.info("Removed currency %s", currency_id)

        return True
    except (OperationalError, Exception) as e:
        logging.error("Failed to remove currency %s. %s", currency_id, e)
        return False


def set_currency(user_id, currency_id, amount):
    try:
        logging.info("Setting user %s's currency %s to %s", user_id, currency_id, amount)

        CURSOR.execute("""
            UPDATE GACHA_CURRENCY_WALLET AS W
            SET AMOUNT = ?
            WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
            """, (amount, currency_id, user_id,))
        CONN.commit()

        logging.info("Set user %s's currency %s to %s", user_id, currency_id, amount)

        return True
    except (OperationalError, Exception) as e:
        logging.error("Failed to set user %s's currency %s to %s. %s", user_id, currency_id, amount, e)
        return False


def clear_currency(user_id, currency_id):
    try:
        logging.info("Clearing user %s's currency %s", user_id, currency_id)

        CURSOR.execute("""
            DELETE FROM GACHA_CURRENCY_WALLET AS W
            WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
            """, (currency_id, str(user_id),))
        CONN.commit()

        logging.info("Cleared user %s's currency %s", user_id, currency_id)

        return True
    except (OperationalError, Exception) as e:
        logging.error("Failed to clear user %s's currency %s. %s", user_id, currency_id, e)
        return False


def get_wallet_row(user_id, currency_id):
    try:
        logging.info("Getting user %s's wallet for currency %s", user_id, currency_id)

        CURSOR.execute("""
            SELECT *
            FROM GACHA_CURRENCY_WALLET W
            WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
            """, (currency_id, user_id,))
        result = CURSOR.fetchone()

        if result is None:
            raise Exception

        logging.info("Got user %s's wallet for currency %s", user_id, currency_id)

        return result
    except (OperationalError, Exception) as e:
        logging.error("Failed to get user %s's wallet for currency %s. %s", user_id, currency_id, e)
        return None


def get_wallet_rows(user_id):
    try:
        logging.info("Getting user %s's wallet", user_id)

        CURSOR.execute("""
            SELECT C.NAME, W.AMOUNT
            FROM GACHA_CURRENCY_WALLET W
            LEFT JOIN GACHA_CURRENCY C ON
            W.GACHA_CURRENCY_ID = C.GACHA_CURRENCY_ID
            WHERE W.USER = ?
            """, (user_id,))
        result = CURSOR.fetchall()

        if result is None:
            raise Exception

        logging.info("Got user %s's wallet", user_id)

        return result
    except (OperationalError, Exception) as e:
        logging.error("Failed to get user %s's wallet. %s", user_id, e)
        return None


def create_wallet(user_id, currency_id, amount):
    try:
        logging.info("Creating user %s's wallet for currency %s with %s amount", user_id, currency_id, amount)

        CURSOR.execute("""
            INSERT INTO GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT)
            VALUES (?, ?, ?)
            """, (currency_id, str(user_id), amount))
        CONN.commit()

        logging.info("Created user %s's wallet for currency %s with %s amount", user_id, currency_id, amount)

        return True
    except (OperationalError, Exception) as e:
        logging.error("Failed to create user %s's wallet for currency %s with %s amount. %s", user_id, currency_id,
                      amount, e)
        return False


def get_scoreboard_rows(currency_id):
    try:
        logging.info("Getting scoreboard for %s", currency_id)

        CURSOR.execute("""
            SELECT W.USER, W.AMOUNT
            FROM GACHA_CURRENCY_WALLET W
            WHERE W.GACHA_CURRENCY_ID = ?
            ORDER BY W.AMOUNT DESC
            """, (currency_id,))
        result = CURSOR.fetchall()

        if result is None:
            raise Exception

        logging.info("Got scoreboard for %s", currency_id)

        return result
    except (OperationalError, Exception) as e:
        logging.error("Failed to get scoreboard for %s. %s", currency_id, e)
        return None
