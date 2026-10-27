import logging

from fjormcord.bot.artping.database import execute, exists, fetch_column, fetch_value, get_database_connection

_REMOVE_TRACKER = """
    DELETE FROM VOTING_GAUNTLET_TRACKER
    WHERE TOURNAMENT_ID = ? AND USER = ? AND CHARACTER_NAME = ?
    """


def get_running_tournament() -> int | None:
    return fetch_value("SELECT TOURNAMENT_ID FROM VOTING_GAUNTLET")


def set_running_tournament(tournament_id: int):
    # Replaces another gauntlet, whose trackers go with it; the running one keeps its trackers
    with get_database_connection() as conn:
        conn.execute("DELETE FROM VOTING_GAUNTLET WHERE TOURNAMENT_ID != ?", (tournament_id,))
        conn.execute("INSERT OR IGNORE INTO VOTING_GAUNTLET (TOURNAMENT_ID) VALUES (?)", (tournament_id,))


def remove_running_tournament():
    logging.info("Removing the running Voting Gauntlet and its trackers")
    execute("DELETE FROM VOTING_GAUNTLET")


def has_tracker(tournament_id: int, user_id: str, character_name: str) -> bool:
    sql = """
        SELECT 1
        FROM VOTING_GAUNTLET_TRACKER
        WHERE TOURNAMENT_ID = ? AND USER = ? AND CHARACTER_NAME = ?
        """

    return exists(sql, (tournament_id, user_id, character_name))


def add_tracker(tournament_id: int, user_id: str, character_name: str, opponent_name: str):
    # A user tracks one side of a matchup, so tracking a character stops tracking its opponent
    with get_database_connection() as conn:
        conn.execute(_REMOVE_TRACKER, (tournament_id, user_id, opponent_name))
        conn.execute(
            """
            INSERT OR IGNORE INTO VOTING_GAUNTLET_TRACKER (TOURNAMENT_ID, USER, CHARACTER_NAME)
            VALUES (?, ?, ?)
            """,
            (tournament_id, user_id, character_name),
        )


def remove_tracker(tournament_id: int, user_id: str, character_name: str):
    execute(_REMOVE_TRACKER, (tournament_id, user_id, character_name))


def get_trackers(tournament_id: int, character_name: str) -> list[str]:
    sql = """
        SELECT USER
        FROM VOTING_GAUNTLET_TRACKER
        WHERE TOURNAMENT_ID = ? AND CHARACTER_NAME = ?
        ORDER BY USER
        """

    return fetch_column(sql, (tournament_id, character_name))
