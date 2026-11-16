from fjormcord.bot.artping.database import execute, exists, fetch_column, fetch_value, get_database_connection
from fjormcord.bot.artping.model.voting_gauntlet import Entrant

_REMOVE_TRACKER = """
    DELETE FROM VOTING_GAUNTLET_TRACKER
    WHERE TOURNAMENT_ID = ? AND USER = ? AND SLOT = ?
    """


def get_running_tournament() -> int | None:
    return fetch_value("SELECT TOURNAMENT_ID FROM VOTING_GAUNTLET")


def set_running_tournament(tournament_id: int, entrants: list[Entrant]):
    with get_database_connection() as conn:
        conn.execute("DELETE FROM VOTING_GAUNTLET WHERE TOURNAMENT_ID != ?", (tournament_id,))
        conn.execute("INSERT OR IGNORE INTO VOTING_GAUNTLET (TOURNAMENT_ID) VALUES (?)", (tournament_id,))

        # An update rather than a replace, which would delete the entrant's trackers
        conn.executemany(
            """
            INSERT INTO VOTING_GAUNTLET_ENTRANT (TOURNAMENT_ID, SLOT, NAME)
            VALUES (?, ?, ?)
            ON CONFLICT (TOURNAMENT_ID, SLOT) DO UPDATE SET NAME = excluded.NAME
            """,
            [(tournament_id, entrant.slot, entrant.name) for entrant in entrants],
        )

        # Trackers stored by name before migration 003: a name that belongs to one entrant moves to its slot, the rest
        # are dropped (a "Shez", since two entrants are called Shez and it can't tell which one was meant)
        conn.execute(
            """
            INSERT OR IGNORE INTO VOTING_GAUNTLET_TRACKER (TOURNAMENT_ID, USER, SLOT)
            SELECT N.TOURNAMENT_ID, N.USER, E.SLOT
            FROM VOTING_GAUNTLET_NAMED_TRACKER N
            JOIN VOTING_GAUNTLET_ENTRANT E ON E.TOURNAMENT_ID = N.TOURNAMENT_ID AND E.NAME = N.CHARACTER_NAME
            WHERE (
                SELECT COUNT(*)
                FROM VOTING_GAUNTLET_ENTRANT NAMESAKE
                WHERE NAMESAKE.TOURNAMENT_ID = E.TOURNAMENT_ID AND NAMESAKE.NAME = E.NAME
            ) = 1
            """
        )

        conn.execute("DELETE FROM VOTING_GAUNTLET_NAMED_TRACKER")


def remove_running_tournament():
    execute("DELETE FROM VOTING_GAUNTLET")


def get_entrant_name(tournament_id: int, slot: int) -> str | None:
    return fetch_value(
        "SELECT NAME FROM VOTING_GAUNTLET_ENTRANT WHERE TOURNAMENT_ID = ? AND SLOT = ?", (tournament_id, slot)
    )


def has_tracker(tournament_id: int, user_id: str, slot: int) -> bool:
    sql = """
        SELECT 1
        FROM VOTING_GAUNTLET_TRACKER
        WHERE TOURNAMENT_ID = ? AND USER = ? AND SLOT = ?
        """

    return exists(sql, (tournament_id, user_id, slot))


def add_tracker(tournament_id: int, user_id: str, slot: int, opponent_slot: int):
    with get_database_connection() as conn:
        conn.execute(_REMOVE_TRACKER, (tournament_id, user_id, opponent_slot))
        conn.execute(
            """
            INSERT OR IGNORE INTO VOTING_GAUNTLET_TRACKER (TOURNAMENT_ID, USER, SLOT)
            VALUES (?, ?, ?)
            """,
            (tournament_id, user_id, slot),
        )


def remove_tracker(tournament_id: int, user_id: str, slot: int):
    execute(_REMOVE_TRACKER, (tournament_id, user_id, slot))


def get_trackers(tournament_id: int, slot: int) -> list[str]:
    sql = """
        SELECT USER
        FROM VOTING_GAUNTLET_TRACKER
        WHERE TOURNAMENT_ID = ? AND SLOT = ?
        ORDER BY USER
        """

    return fetch_column(sql, (tournament_id, slot))
