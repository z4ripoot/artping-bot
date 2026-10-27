import logging
from collections.abc import Iterable

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.character_vote import CharacterVote, VoteChannel
from fjormcord.bot.artping.repository import character_vote_repository
# Imported as modules, since character_service and vote_view import this one too
from fjormcord.bot.artping import vote_view
from fjormcord.bot.artping.service import character_service
from fjormcord.bot.artping.util.user_util import is_administrator


def is_voting_enabled() -> bool:
    # With fewer than 2 votes needed a vote decides nothing, so non-admins add characters directly
    return config.read_settings().character_votes_needed >= 2


async def start_vote(vote_channel: VoteChannel, proposer_id: str, name: str) -> str:
    # The vote message is sent here instead of being the reply, since the vote is stored by its ID
    if not vote_channel.in_guild:
        raise CommandError("Votes can only be started in a server")

    vote_message = await vote_channel.send(_vote_text(name), vote_view.VoteView(0))
    character_vote_repository.add_vote(
        CharacterVote(str(vote_message.id), vote_channel.channel_id, name, proposer_id, uses_button=True))

    # An empty reply sends nothing more
    return ""


async def toggle_vote(client: discord.Client, vote_message: discord.Message, user: discord.abc.User) -> str:
    # A click on the vote button adds the user's vote or takes it back; an admin's click passes the vote.
    # Returns the reply only the clicker sees.
    message_id = str(vote_message.id)
    vote = character_vote_repository.get_vote(message_id)
    if vote is None:
        # Closed while its message kept the button, e.g. when editing the message failed
        await _edit(vote_message, view=None)
        return "This vote has already been closed"

    dropped = await _drop_if_name_taken(vote_message, vote)
    if dropped is not None:
        return dropped

    # Nothing awaits from reading the vote to the commit, so other clicks and events can't interleave
    name = vote.character_name
    user_id = str(user.id)
    # The click comes from a server member, so the permissions are there without fetching the member
    administrator = is_administrator(user)
    if not administrator and character_vote_repository.has_voter(message_id, user_id):
        character_vote_repository.remove_voter(message_id, user_id)
        out = f"Your vote for {name} has been taken back"
    else:
        # An admin is subscribed along with the other voters
        character_vote_repository.add_voter(message_id, user_id)
        out = f"Your vote for {name} has been added"

    await _pass_or_show_count(client, vote_message, vote, administrator)
    return out


async def check_open_votes(client: discord.Client):
    # Run at startup: votes_needed or the names may have changed while the bot was offline, votes still counted by
    # their reactions get the button, and the messages of the votes that stay open are re-rendered
    for vote in character_vote_repository.get_votes():
        try:
            await _check_open_vote(client, vote)
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


def _vote_text(name: str) -> str:
    return f"Vote to add {name}. Votes needed: {config.read_settings().character_votes_needed}"


async def _check_open_vote(client: discord.Client, vote: CharacterVote):
    # Adds the character once enough users voted, or an admin reacted before the conversion; drops the vote when its
    # message is gone or its name got taken; otherwise re-renders its message with the current text and count
    message_id = vote.message_id
    try:
        vote_message = await _fetch_vote_message(client, vote)
    except discord.NotFound:
        logging.info("The message of vote %s is gone, dropping the vote", message_id)
        character_vote_repository.remove_vote(message_id)
        return
    except discord.Forbidden as e:
        # Kept, so the vote is checked, or converted, again once the bot may read the channel
        logging.warning("Can't read the message of vote %s, check the bot's permissions. %s", message_id, e)
        return

    settings = config.read_settings()
    voters = []
    has_administrator = False
    if not vote.uses_button:
        voters = await _get_voters(vote_message, settings.character_vote_emoji)
        has_administrator = (len(voters) < settings.character_votes_needed
                             and await _has_administrator(vote_message.guild, voters))

    # Another event may have closed the vote while the reactions and members were fetched, or another check
    # converted it; nothing awaits from here to the commit
    current = character_vote_repository.get_vote(message_id)
    if current is None:
        return
    if await _drop_if_name_taken(vote_message, vote) is not None:
        return

    converting = not current.uses_button
    if converting:
        character_vote_repository.convert_vote(message_id, [str(voter.id) for voter in voters])

    # Re-rendered at every start, so the text and label follow a changed votes_needed, and a conversion whose edit
    # failed gets its button on the next start
    await _pass_or_show_count(client, vote_message, vote, converting and has_administrator)


async def _drop_if_name_taken(vote_message: discord.Message, vote: CharacterVote) -> str | None:
    # A name taken another way, e.g. as an alias, leaves the vote nothing to decide: it is dropped and its message
    # says why. Returns that reason, or None when the vote stays open; then it awaits nothing, so the caller's
    # vote can't change underneath it
    try:
        character_service.require_unused_name(vote.character_name)
    except CommandError as e:
        logging.info("Dropping vote %s: %s", vote.message_id, e)
        character_vote_repository.remove_vote(vote.message_id)
        await _edit(vote_message, content=str(e), view=None)
        return str(e)
    return None


async def _pass_or_show_count(client: discord.Client, vote_message: discord.Message, vote: CharacterVote,
                              by_administrator: bool):
    # Adds the character when an admin voted or enough users did; otherwise renders the message with the current count
    count = character_vote_repository.count_voters(vote.message_id)
    if by_administrator or count >= config.read_settings().character_votes_needed:
        await _pass(client, vote_message, vote)
    else:
        await _edit(vote_message, content=_vote_text(vote.character_name), view=vote_view.VoteView(count))


async def _pass(client: discord.Client, vote_message: discord.Message, vote: CharacterVote):
    # The caller has awaited nothing since it read the vote, so it is still open
    other_votes = [other for other in character_vote_repository.get_votes_for(vote.character_name)
                   if other.message_id != vote.message_id]
    character_vote_repository.pass_vote(vote.message_id, vote.character_name)
    await _edit(vote_message, content=f"Character {vote.character_name} has been added", view=None)
    await _close(client, other_votes, vote.character_name)


async def _fetch_vote_message(client: discord.Client, vote: CharacterVote) -> discord.Message:
    channel_id = int(vote.channel_id)
    # The cache costs no request to Discord
    channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
    return await channel.fetch_message(int(vote.message_id))


async def _get_voters(vote_message: discord.Message, emoji: str) -> list[discord.abc.User]:
    # Users who reacted with the vote emoji, without bots such as this one; only read to convert a vote that was
    # counted by its reactions
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
    # The votes are already gone from the database; this only tells their messages, and removes their buttons
    for vote in votes:
        try:
            vote_message = await _fetch_vote_message(client, vote)
        except discord.HTTPException as e:
            logging.warning("Failed to fetch the message of closed vote %s. %s", vote.message_id, e)
            continue
        await _edit(vote_message, content=f"Character {name} has already been added", view=None)


async def _edit(vote_message: discord.Message, **changes):
    # changes: the content and view as Message.edit takes them, view=None removing the button
    try:
        await vote_message.edit(**changes)
    except discord.HTTPException as e:
        logging.warning("Failed to edit vote message %s. %s", vote_message.id, e)
