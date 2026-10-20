import logging

from fjormcord.bot.artping.database import get_database_connection


def get_currency_row(currency_name):
    return get_database_connection().execute("""
        SELECT C.GACHA_CURRENCY_ID, C.NAME
        FROM GACHA_CURRENCY C
        WHERE LOWER(C.NAME) = ?
        """, (currency_name.lower(),)).fetchone()


def add_currency(currency_name):
    logging.info("Adding currency %s", currency_name)

    with get_database_connection() as conn:
        conn.execute("""
            INSERT INTO GACHA_CURRENCY (NAME)
            VALUES (?)
            """, (currency_name,))


def remove_currency(currency_id):
    logging.info("Removing currency %s", currency_id)

    with get_database_connection() as conn:
        conn.execute("""
            DELETE FROM GACHA_CURRENCY
            WHERE GACHA_CURRENCY_ID = ?
            """, (currency_id,))


def set_currency(user_id, currency_id, amount):
    logging.info("Setting user %s's currency %s to %s", user_id, currency_id, amount)

    with get_database_connection() as conn:
        conn.execute("""
            UPDATE GACHA_CURRENCY_WALLET
            SET AMOUNT = ?
            WHERE GACHA_CURRENCY_ID = ? AND USER = ?
            """, (amount, currency_id, user_id,))


def clear_currency(user_id, currency_id):
    logging.info("Clearing user %s's currency %s", user_id, currency_id)

    with get_database_connection() as conn:
        conn.execute("""
            DELETE FROM GACHA_CURRENCY_WALLET
            WHERE GACHA_CURRENCY_ID = ? AND USER = ?
            """, (currency_id, user_id,))


def get_wallet_row(user_id, currency_id):
    return get_database_connection().execute("""
        SELECT W.GACHA_CURRENCY_ID, W.USER, W.AMOUNT
        FROM GACHA_CURRENCY_WALLET W
        WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
        """, (currency_id, user_id,)).fetchone()


def get_wallet_rows(user_id):
    return get_database_connection().execute("""
        SELECT C.NAME, W.AMOUNT
        FROM GACHA_CURRENCY_WALLET W
        LEFT JOIN GACHA_CURRENCY C ON W.GACHA_CURRENCY_ID = C.GACHA_CURRENCY_ID
        WHERE W.USER = ?
        """, (user_id,)).fetchall()


def create_wallet(user_id, currency_id, amount):
    logging.info("Creating user %s's wallet for currency %s with %s amount", user_id, currency_id, amount)

    with get_database_connection() as conn:
        conn.execute("""
            INSERT INTO GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT)
            VALUES (?, ?, ?)
            """, (currency_id, user_id, amount,))


def get_scoreboard_rows(currency_id):
    return get_database_connection().execute("""
        SELECT W.USER, W.AMOUNT
        FROM GACHA_CURRENCY_WALLET W
        WHERE W.GACHA_CURRENCY_ID = ?
        ORDER BY W.AMOUNT DESC
        """, (currency_id,)).fetchall()
