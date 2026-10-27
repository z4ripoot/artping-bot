from collections.abc import Callable

from fjormcord.bot.artping import config


def lorenz_smile() -> str:
    return config.read_settings().emoji["lorenz_smile"]


def chromk() -> str:
    # chromk_1 to chromk_12 are the pieces of one picture, laid out in 3 rows of 4
    emoji = config.read_settings().emoji
    pieces = [emoji[f"chromk_{number}"] for number in range(1, 13)]
    return "\n".join("".join(pieces[start : start + 4]) for start in range(0, 12, 4))


# Whole messages (case-insensitive) that the bot answers with emoji
EASTER_EGG_REPLIES: dict[str, Callable[[], str]] = {
    "thank you lorenz": lorenz_smile,
    "thanks lorenz": lorenz_smile,
    "chromk": chromk,
}


def get_easter_egg_reply(content: str) -> str | None:
    # Returns None when the message isn't an easter egg
    reply = EASTER_EGG_REPLIES.get(content.lower())
    return reply() if reply else None
