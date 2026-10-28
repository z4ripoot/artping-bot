import asyncio

from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.repository import alias_repository, art_ping_repository, character_repository
from fjormcord.bot.artping.service import art_ping_service
from fjormcord.bot.artping.view.subscribe_view import SubscribeButton
from tests.fakes import FakeInteraction


def add_character(name):
    return Character(character_repository.add_character(name), name)


def button_after_restart(button):
    # Rebuilt from its custom_id, as discord.py does for a click on a message sent before a restart
    match = SubscribeButton.__discord_ui_compiled_template__.fullmatch(button.custom_id)
    return asyncio.run(SubscribeButton.from_custom_id(FakeInteraction(), button.item, match))


def click(button, user_id=7):
    interaction = FakeInteraction(user_id)
    asyncio.run(button_after_restart(button).callback(interaction))
    return interaction.sent


def test_button_names_the_character_and_holds_its_id():
    button = SubscribeButton.for_character(Character(3, "Lucina"))

    assert (button.item.label, button.item.custom_id) == ("Subscribe to Lucina", "subscribe:3")


def test_click_subscribes_and_answers_privately():
    lucina = add_character("Lucina")

    assert click(SubscribeButton.for_character(lucina)) == [("Ping for Lucina has been added", True, None)]
    assert art_ping_repository.get_art_ping_users([lucina.id]) == ["7"]


def test_click_only_subscribes():
    button = SubscribeButton.for_character(add_character("Lucina"))
    click(button)

    assert click(button) == [("Ping for Lucina already exists", True, None)]


def test_click_names_a_renamed_character_by_its_new_name():
    lucina = add_character("Lucina")
    button = SubscribeButton.for_character(lucina)
    alias_repository.add_alias(lucina.id, "Masked_Marth")
    alias_repository.set_primary_name(lucina.id, "Masked_Marth")

    assert click(button) == [("Ping for Masked_Marth has been added", True, None)]


def test_click_on_a_removed_character_is_answered_privately():
    lucina = add_character("Lucina")
    character_repository.remove_character(lucina.id)

    assert click(SubscribeButton.for_character(lucina)) == [("This character doesn't exist anymore", True, None)]


def test_click_has_no_cooldown():
    button = SubscribeButton.for_character(add_character("Lucina"))
    click(button)

    marth = SubscribeButton.for_character(add_character("Marth"))

    assert click(marth) == [("Ping for Marth has been added", True, None)]


def test_long_names_fit_the_label():
    button = SubscribeButton.for_character(Character(3, "A" * 100))

    assert len(button.item.label) == 80


def test_failed_click_is_answered_privately(monkeypatch, caplog):
    def failing_subscribe(user_id, character_id):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(art_ping_service, "subscribe", failing_subscribe)

    sent = click(SubscribeButton.for_character(Character(3, "Lucina")))

    assert sent == [("Something went wrong while subscribing", True, None)]
    assert "database is locked" in caplog.text
