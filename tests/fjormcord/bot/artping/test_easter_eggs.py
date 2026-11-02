from fjormcord.bot.artping.easter_eggs import chromk, get_easter_egg_reply, lorenz_smile


def test_thanking_lorenz_is_answered_with_a_smile():
    assert get_easter_egg_reply("Thanks Lorenz") == lorenz_smile()
    assert get_easter_egg_reply("thank you lorenz") == lorenz_smile()


def test_chromk_is_answered_with_the_full_emoji_grid():
    assert get_easter_egg_reply("CHROMK") == chromk()
    assert chromk().count("\n") == 2


def test_only_whole_messages_trigger_a_reply():
    assert get_easter_egg_reply("thanks lorenz!") is None
    assert get_easter_egg_reply("chromk is great") is None
