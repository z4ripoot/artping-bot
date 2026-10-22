from fjormcord.bot.artping import config

CONFIG = config.read_config()

LORENZ_SMILE = CONFIG.get('emoji', 'lorenz_smile')

CHROMK_1 = CONFIG.get('emoji', 'chromk_1')
CHROMK_2 = CONFIG.get('emoji', 'chromk_2')
CHROMK_3 = CONFIG.get('emoji', 'chromk_3')
CHROMK_4 = CONFIG.get('emoji', 'chromk_4')
CHROMK_5 = CONFIG.get('emoji', 'chromk_5')
CHROMK_6 = CONFIG.get('emoji', 'chromk_6')
CHROMK_7 = CONFIG.get('emoji', 'chromk_7')
CHROMK_8 = CONFIG.get('emoji', 'chromk_8')
CHROMK_9 = CONFIG.get('emoji', 'chromk_9')
CHROMK_10 = CONFIG.get('emoji', 'chromk_10')
CHROMK_11 = CONFIG.get('emoji', 'chromk_11')
CHROMK_12 = CONFIG.get('emoji', 'chromk_12')
CHROMK = f'{CHROMK_1}{CHROMK_2}{CHROMK_3}{CHROMK_4}\n{CHROMK_5}{CHROMK_6}{CHROMK_7}{CHROMK_8}\n{CHROMK_9}{CHROMK_10}{CHROMK_11}{CHROMK_12}'

# Whole messages (case-insensitive) that the bot answers with emoji
EASTER_EGG_REPLIES = {
    "thank you lorenz": LORENZ_SMILE,
    "thanks lorenz": LORENZ_SMILE,
    "chromk": CHROMK,
}


def get_easter_egg_reply(content):
    # Returns None when the message isn't an easter egg
    return EASTER_EGG_REPLIES.get(content.lower())
