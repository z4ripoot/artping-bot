import logging
from collections.abc import Iterable

from fjormcord.bot.artping.database import execute, exists, fetch_all, fetch_one, fetch_value, get_database_connection
from fjormcord.bot.artping.model.character_vote import CharacterVote

_SELECT_VOTE = """
    SELECT V.MESSAGE_ID AS message_id, V.CHANNEL_ID AS channel_id, V.CHARACTER_NAME AS character_name,
           V.PROPOSER AS proposer, V.USES_BUTTON AS uses_button
    FROM CHARACTER_VOTE V
    """
_REMOVE_VOTES_FOR = """
    DELETE FROM CHARACTER_VOTE
    WHERE CHARACTER_NAME = ?
    """
_ADD_VOTER = """
    INSERT OR IGNORE INTO CHARACTER_VOTE_VOTER (MESSAGE_ID, USER)
    VALUES (?, ?)
    """


def add_vote(vote: CharacterVote, voter_ids: Iterable[str] = ()):
    # Stores the vote with its first voters, all or nothing
    sql = """
        INSERT INTO CHARACTER_VOTE (MESSAGE_ID, CHANNEL_ID, CHARACTER_NAME, PROPOSER, USES_BUTTON)
        VALUES (?, ?, ?, ?, ?)
        """

    logging.info("Adding vote %s for character %s", vote.message_id, vote.character_name)
    with get_database_connection() as conn:
        conn.execute(sql, (vote.message_id, vote.channel_id, vote.character_name, vote.proposer, vote.uses_button))
        conn.executemany(_ADD_VOTER, [(vote.message_id, voter_id) for voter_id in voter_ids])


def get_vote(message_id: str) -> CharacterVote | None:
    return fetch_one(CharacterVote, _SELECT_VOTE + "WHERE V.MESSAGE_ID = ?", (message_id,))


def get_votes() -> list[CharacterVote]:
    return fetch_all(CharacterVote, _SELECT_VOTE)


def get_votes_for(character_name: str) -> list[CharacterVote]:
    return fetch_all(CharacterVote, _SELECT_VOTE + "WHERE V.CHARACTER_NAME = ?", (character_name,))


def remove_vote(message_id: str):
    sql = """
        DELETE FROM CHARACTER_VOTE
        WHERE MESSAGE_ID = ?
        """

    logging.info("Removing vote %s", message_id)
    execute(sql, (message_id,))


def remove_votes_for(character_name: str):
    logging.info("Removing votes for character %s", character_name)
    execute(_REMOVE_VOTES_FOR, (character_name,))


def add_voter(message_id: str, user_id: str):
    execute(_ADD_VOTER, (message_id, user_id))


def remove_voter(message_id: str, user_id: str):
    sql = """
        DELETE FROM CHARACTER_VOTE_VOTER
        WHERE MESSAGE_ID = ? AND USER = ?
        """

    execute(sql, (message_id, user_id))


def has_voter(message_id: str, user_id: str) -> bool:
    sql = """
        SELECT 1
        FROM CHARACTER_VOTE_VOTER
        WHERE MESSAGE_ID = ? AND USER = ?
        """

    return exists(sql, (message_id, user_id))


def count_voters(message_id: str) -> int:
    sql = """
        SELECT COUNT(*)
        FROM CHARACTER_VOTE_VOTER
        WHERE MESSAGE_ID = ?
        """

    return fetch_value(sql, (message_id,))


def convert_vote(message_id: str, user_ids: Iterable[str]):
    # Stores the voters counted from the reactions and marks the vote as counting stored voters, all or nothing
    mark_vote = """
        UPDATE CHARACTER_VOTE
        SET USES_BUTTON = 1
        WHERE MESSAGE_ID = ?
        """

    logging.info("Converting vote %s to a button vote", message_id)
    with get_database_connection() as conn:
        conn.executemany(_ADD_VOTER, [(message_id, user_id) for user_id in user_ids])
        conn.execute(mark_vote, (message_id,))


def pass_vote(message_id: str, character_name: str):
    # Adds the character, subscribes the voters and closes every vote for the name, all or nothing
    add_character = """
        INSERT INTO CHARACTERS (NAME)
        VALUES (?)
        """
    add_pings = """
        INSERT INTO PINGS (CHARACTER_ID, USER)
        SELECT ?, USER
        FROM CHARACTER_VOTE_VOTER
        WHERE MESSAGE_ID = ?
        """

    logging.info("Adding character %s by vote", character_name)
    with get_database_connection() as conn:
        character_id = conn.execute(add_character, (character_name,)).lastrowid
        conn.execute(add_pings, (character_id, message_id))
        conn.execute(_REMOVE_VOTES_FOR, (character_name,))
