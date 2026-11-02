import logging
from collections.abc import Iterable

import discord


def is_administrator(author: discord.abc.User) -> bool:
    permissions = getattr(author, "guild_permissions", None)
    return permissions is not None and permissions.administrator


def mentions(user_ids: Iterable[str]) -> str:
    return " ".join(f"<@{user_id}>" for user_id in user_ids)


async def get_username(client: discord.Client, user_id: str) -> str:
    user = client.get_user(int(user_id))
    if user is None:
        try:
            user = await client.fetch_user(int(user_id))
        except discord.HTTPException as e:
            logging.warning("Failed to fetch user %s. %s", user_id, e)
            return f"Unknown user ({user_id})"

    return user.global_name or user.name
