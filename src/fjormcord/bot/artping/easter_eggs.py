from fjormcord.bot.artping import config

EMOJI = config.read_settings().emoji

LORENZ_SMILE = EMOJI['lorenz_smile']

# chromk_1 to chromk_12 are the pieces of one picture, laid out in 3 rows of 4
_chromk_pieces = [EMOJI[f'chromk_{number}'] for number in range(1, 13)]
CHROMK = "\n".join("".join(_chromk_pieces[start:start + 4]) for start in range(0, 12, 4))

# Whole messages (case-insensitive) that the bot answers with emoji
EASTER_EGG_REPLIES = {
    "thank you lorenz": LORENZ_SMILE,
    "thanks lorenz": LORENZ_SMILE,
    "chromk": CHROMK,
}


def get_easter_egg_reply(content):
    # Returns None when the message isn't an easter egg
    return EASTER_EGG_REPLIES.get(content.lower())
