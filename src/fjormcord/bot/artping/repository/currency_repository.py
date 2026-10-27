import logging

from fjormcord.bot.artping.database import execute, exists, get_database_connection
from fjormcord.bot.artping.model.currency import Currency, ScoreboardEntry, WalletEntry


def get_currency(currency_name: str) -> Currency | None:
    sql = """
        SELECT C.GACHA_CURRENCY_ID AS id, C.NAME AS name
        FROM GACHA_CURRENCY C
        WHERE C.NAME = ?
        """

    row = get_database_connection().execute(sql, (currency_name,)).fetchone()
    return Currency(**row) if row else None


def add_currency(currency_name: str):
    sql = """
        INSERT INTO GACHA_CURRENCY (NAME)
        VALUES (?)
        """

    execute(sql, (currency_name,))


def remove_currency(currency_id: int):
    sql = """
        DELETE FROM GACHA_CURRENCY
        WHERE GACHA_CURRENCY_ID = ?
        """

    execute(sql, (currency_id,))


def set_currency(user_id: str, currency_id: int, amount: int):
    sql = """
        INSERT INTO GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT)
        VALUES (?, ?, ?)
        ON CONFLICT (GACHA_CURRENCY_ID, USER) DO UPDATE SET AMOUNT = excluded.AMOUNT
        """

    logging.info("Setting user %s's currency %s to %s", user_id, currency_id, amount)
    execute(sql, (currency_id, user_id, amount))


def clear_currency(user_id: str, currency_id: int):
    sql = """
        DELETE FROM GACHA_CURRENCY_WALLET
        WHERE GACHA_CURRENCY_ID = ? AND USER = ?
        """

    logging.info("Clearing user %s's currency %s", user_id, currency_id)
    execute(sql, (currency_id, user_id))


def has_wallet_entry(user_id: str, currency_id: int) -> bool:
    sql = """
        SELECT 1
        FROM GACHA_CURRENCY_WALLET W
        WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
        """

    return exists(sql, (currency_id, user_id))


def get_wallet(user_id: str) -> list[WalletEntry]:
    sql = """
        SELECT C.NAME AS currency_name, W.AMOUNT AS amount
        FROM GACHA_CURRENCY_WALLET W
        JOIN GACHA_CURRENCY C ON W.GACHA_CURRENCY_ID = C.GACHA_CURRENCY_ID
        WHERE W.USER = ?
        ORDER BY C.NAME
        """

    return [WalletEntry(**row) for row in get_database_connection().execute(sql, (user_id,))]


def get_scoreboard(currency_id: int) -> list[ScoreboardEntry]:
    sql = """
        SELECT W.USER AS user_id, W.AMOUNT AS amount
        FROM GACHA_CURRENCY_WALLET W
        WHERE W.GACHA_CURRENCY_ID = ?
        ORDER BY W.AMOUNT DESC
        """

    return [ScoreboardEntry(**row) for row in get_database_connection().execute(sql, (currency_id,))]


def get_currency_names(prefix: str = "", limit: int = -1) -> list[str]:
    # The names starting with prefix, ignoring case; a limit of -1 means no limit
    sql = """
        SELECT C.NAME
        FROM GACHA_CURRENCY C
        WHERE SUBSTR(C.NAME, 1, LENGTH(?)) = ? COLLATE NOCASE
        ORDER BY C.NAME
        LIMIT ?
        """

    # Each row holds just the one selected column
    return [name for (name,) in get_database_connection().execute(sql, (prefix, prefix, limit))]
