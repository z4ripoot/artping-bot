import logging
from collections.abc import Iterable

from fjormcord.bot.artping.database import get_database_connection
from fjormcord.bot.artping.model.character_vote import CharacterVote

_SELECT_VOTE = """
    SELECT V.MESSAGE_ID AS message_id, V.CHANNEL_ID AS channel_id, V.CHARACTER_NAME AS character_name,
           V.PROPOSER AS proposer
    FROM CHARACTER_VOTE V
    """


def add_vote(vote: CharacterVote):
    sql = """
        INSERT INTO CHARACTER_VOTE (MESSAGE_ID, CHANNEL_ID, CHARACTER_NAME, PROPOSER)
        VALUES (?, ?, ?, ?)
        """

    logging.info("Adding vote %s for character %s", vote.message_id, vote.character_name)
    with get_database_connection() as conn:
        conn.execute(sql, (vote.message_id, vote.channel_id, vote.character_name, vote.proposer))


def get_vote(message_id: str) -> CharacterVote | None:
    row = get_database_connection().execute(_SELECT_VOTE + "WHERE V.MESSAGE_ID = ?", (message_id,)).fetchone()
    return CharacterVote(**row) if row else None


def get_votes() -> list[CharacterVote]:
    return [CharacterVote(**row) for row in get_database_connection().execute(_SELECT_VOTE)]


def get_votes_for(character_name: str) -> list[CharacterVote]:
    rows = get_database_connection().execute(_SELECT_VOTE + "WHERE V.CHARACTER_NAME = ?", (character_name,))
    return [CharacterVote(**row) for row in rows]


def remove_vote(message_id: str):
    sql = """
        DELETE FROM CHARACTER_VOTE
        WHERE MESSAGE_ID = ?
        """

    logging.info("Removing vote %s", message_id)
    with get_database_connection() as conn:
        conn.execute(sql, (message_id,))


def remove_votes_for(character_name: str):
    sql = """
        DELETE FROM CHARACTER_VOTE
        WHERE CHARACTER_NAME = ?
        """

    logging.info("Removing votes for character %s", character_name)
    with get_database_connection() as conn:
        conn.execute(sql, (character_name,))


def pass_vote(character_name: str, user_ids: Iterable[str]):
    # Adds the character, subscribes the voters and closes every vote for the name, all or nothing
    add_character = """
        INSERT INTO CHARACTERS (NAME)
        VALUES (?)
        """
    add_ping = """
        INSERT INTO PINGS (CHARACTER_ID, USER)
        VALUES (?, ?)
        """
    remove_votes = """
        DELETE FROM CHARACTER_VOTE
        WHERE CHARACTER_NAME = ?
        """

    logging.info("Adding character %s by vote", character_name)
    with get_database_connection() as conn:
        character_id = conn.execute(add_character, (character_name,)).lastrowid
        conn.executemany(add_ping, [(character_id, user_id) for user_id in user_ids])
        conn.execute(remove_votes, (character_name,))
