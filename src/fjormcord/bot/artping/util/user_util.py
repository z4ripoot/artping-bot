import logging

import discord


async def get_username(client: discord.Client, user_id):
    try:
        user = await client.fetch_user(int(user_id))
    except (discord.NotFound, discord.HTTPException) as e:
        logging.warning("Failed to fetch user %s. %s", user_id, e)
        return f"Unknown user ({user_id})"

    # global_name is None for users who never set a display name
    return user.global_name or user.name
