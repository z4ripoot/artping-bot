import logging
from collections.abc import Iterable

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.character_vote import CharacterVote, VoteChannel
from fjormcord.bot.artping.repository import character_vote_repository
# Imported as a module, since character_service imports this one too
from fjormcord.bot.artping.service import character_service
from fjormcord.bot.artping.util.message_util import CommandError
from fjormcord.bot.artping.util.user_util import is_administrator


def is_voting_enabled() -> bool:
    # With fewer than 2 votes needed a vote decides nothing, so non-admins add characters directly
    return config.read_settings().character_votes_needed >= 2


async def start_vote(vote_channel: VoteChannel, proposer_id: str, name: str) -> str:
    # The vote message is sent here instead of being the reply, since the vote is stored by its ID
    if not vote_channel.in_guild:
        raise CommandError("Votes can only be started in a server")

    settings = config.read_settings()
    vote_message = await vote_channel.send(f"Vote to add {name}: react with {settings.character_vote_emoji}. "
                                           f"Votes needed: {settings.character_votes_needed}", None)
    character_vote_repository.add_vote(
        CharacterVote(str(vote_message.id), vote_channel.channel_id, name, proposer_id))

    try:
        await vote_message.add_reaction(settings.character_vote_emoji)
    except discord.HTTPException as e:
        # Users can still add the reaction themselves
        logging.warning("Failed to react to the vote for %s. %s", name, e)

    # An empty reply sends nothing more
    return ""


async def check_vote(client: discord.Client, message_id: str):
    # Adds the character once enough users, or an admin, reacted; drops the vote when its message is gone or its name got taken
    vote = character_vote_repository.get_vote(message_id)
    if vote is None:
        return

    try:
        vote_message = await _fetch_vote_message(client, vote)
    except discord.NotFound:
        logging.info("The message of vote %s is gone, dropping the vote", message_id)
        character_vote_repository.remove_vote(message_id)
        return
    except discord.Forbidden as e:
        # Kept, so the vote counts again once the bot may read the channel
        logging.warning("Can't read the message of vote %s, check the bot's permissions. %s", message_id, e)
        return

    settings = config.read_settings()
    voters = await _get_voters(vote_message, settings.character_vote_emoji)

    # Another event may have closed the vote while the reactions were fetched; nothing awaits from here to the commit
    if character_vote_repository.get_vote(message_id) is None:
        return

    try:
        character_service.require_unused_name(vote.character_name)
    except CommandError as e:
        logging.info("Dropping vote %s: %s", message_id, e)
        character_vote_repository.remove_vote(message_id)
        await _edit(vote_message, str(e))
        return

    if len(voters) < settings.character_votes_needed and not await _has_administrator(vote_message.guild, voters):
        return

    # Another event may have closed the vote while the members were fetched
    if character_vote_repository.get_vote(message_id) is None:
        return

    other_votes = [other for other in character_vote_repository.get_votes_for(vote.character_name)
                   if other.message_id != message_id]
    for voter in voters:
        character_vote_repository.add_voter(message_id, str(voter.id))
    character_vote_repository.pass_vote(message_id, vote.character_name)
    await _edit(vote_message, f"Character {vote.character_name} has been added")
    await _close(client, other_votes, vote.character_name)


async def check_open_votes(client: discord.Client):
    # Run at startup: reactions may have changed while the bot was offline
    for vote in character_vote_repository.get_votes():
        try:
            await check_vote(client, vote.message_id)
        except Exception:
            logging.exception("Checking vote %s failed", vote.message_id)


async def close_votes(client: discord.Client, name: str):
    # The character has been added without them, so the open votes for its name have nothing left to decide
    votes = character_vote_repository.get_votes_for(name)
    character_vote_repository.remove_votes_for(name)
    await _close(client, votes, name)


def drop_deleted_vote(message_id: str):
    # Called for every deleted message, most of which aren't votes
    if character_vote_repository.get_vote(message_id) is not None:
        character_vote_repository.remove_vote(message_id)


async def _fetch_vote_message(client: discord.Client, vote: CharacterVote) -> discord.Message:
    channel_id = int(vote.channel_id)
    # The cache costs no request to Discord
    channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
    return await channel.fetch_message(int(vote.message_id))


async def _get_voters(vote_message: discord.Message, emoji: str) -> list[discord.abc.User]:
    # Users who reacted with the vote emoji, without bots such as this one
    for reaction in vote_message.reactions:
        if str(reaction.emoji) == emoji:
            return [user async for user in reaction.users() if not user.bot]
    return []


async def _has_administrator(guild: discord.Guild, voters: list[discord.abc.User]) -> bool:
    # Only asked while a vote is short, so this costs fewer requests than the votes needed
    for voter in voters:
        # Reactions list a voter as a member, with permissions, only when the member is cached
        if getattr(voter, 'guild_permissions', None) is None:
            try:
                voter = await guild.fetch_member(voter.id)
            except discord.HTTPException as e:
                # E.g. a voter who left the server; their vote still counts, but not as an admin's
                logging.info("Failed to fetch member %s. %s", voter.id, e)
                continue
        if is_administrator(voter):
            return True
    return False


async def _close(client: discord.Client, votes: Iterable[CharacterVote], name: str):
    # The votes are already gone from the database; this only tells their messages
    for vote in votes:
        try:
            vote_message = await _fetch_vote_message(client, vote)
        except discord.HTTPException as e:
            logging.warning("Failed to fetch the message of closed vote %s. %s", vote.message_id, e)
            continue
        await _edit(vote_message, f"Character {name} has already been added")


async def _edit(vote_message: discord.Message, content: str):
    try:
        await vote_message.edit(content=content)
    except discord.HTTPException as e:
        logging.warning("Failed to edit vote message %s. %s", vote_message.id, e)
