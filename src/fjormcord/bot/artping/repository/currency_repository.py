import logging
from dataclasses import dataclass

from fjormcord.bot.artping.database import get_database_connection


@dataclass(frozen=True)
class Currency:
    id: int
    name: str


@dataclass(frozen=True)
class WalletEntry:
    currency_name: str
    amount: int


@dataclass(frozen=True)
class ScoreboardEntry:
    user_id: str
    amount: int


def get_currency(currency_name):
    row = get_database_connection().execute("""
        SELECT C.GACHA_CURRENCY_ID, C.NAME
        FROM GACHA_CURRENCY C
        WHERE C.NAME = ?
        """, (currency_name,)).fetchone()

    return Currency(id=row['GACHA_CURRENCY_ID'], name=row['NAME']) if row else None


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
            INSERT INTO GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT)
            VALUES (?, ?, ?)
            ON CONFLICT (GACHA_CURRENCY_ID, USER) DO UPDATE SET AMOUNT = excluded.AMOUNT
            """, (currency_id, user_id, amount,))


def clear_currency(user_id, currency_id):
    logging.info("Clearing user %s's currency %s", user_id, currency_id)

    with get_database_connection() as conn:
        conn.execute("""
            DELETE FROM GACHA_CURRENCY_WALLET
            WHERE GACHA_CURRENCY_ID = ? AND USER = ?
            """, (currency_id, user_id,))


def has_wallet_entry(user_id, currency_id):
    return get_database_connection().execute("""
        SELECT 1
        FROM GACHA_CURRENCY_WALLET W
        WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
        """, (currency_id, user_id,)).fetchone() is not None


def get_wallet(user_id):
    rows = get_database_connection().execute("""
        SELECT C.NAME, W.AMOUNT
        FROM GACHA_CURRENCY_WALLET W
        JOIN GACHA_CURRENCY C ON W.GACHA_CURRENCY_ID = C.GACHA_CURRENCY_ID
        WHERE W.USER = ?
        ORDER BY C.NAME
        """, (user_id,))

    return [WalletEntry(currency_name=row['NAME'], amount=row['AMOUNT']) for row in rows]


def get_scoreboard(currency_id):
    rows = get_database_connection().execute("""
        SELECT W.USER, W.AMOUNT
        FROM GACHA_CURRENCY_WALLET W
        WHERE W.GACHA_CURRENCY_ID = ?
        ORDER BY W.AMOUNT DESC
        """, (currency_id,))

    return [ScoreboardEntry(user_id=row['USER'], amount=row['AMOUNT']) for row in rows]
