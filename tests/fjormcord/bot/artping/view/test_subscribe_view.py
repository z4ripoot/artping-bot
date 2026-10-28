import asyncio

from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.repository import alias_repository, art_ping_repository, character_repository
from fjormcord.bot.artping.service import art_ping_service
from fjormcord.bot.artping.view.subscribe_view import SubscribeButton, SubscribeView
from tests.fakes import FakeInteraction


def add_character(name):
    return Character(character_repository.add_character(name), name)


def button_after_restart(view):
    # Rebuilt from its custom_id, as discord.py does for a click on a message sent before a restart
    [button] = view.children
    match = SubscribeButton.__discord_ui_compiled_template__.fullmatch(button.custom_id)
    return asyncio.run(SubscribeButton.from_custom_id(FakeInteraction(), button.item, match))


def click(view, user_id=7):
    interaction = FakeInteraction(user_id)
    asyncio.run(button_after_restart(view).callback(interaction))
    return interaction.sent


def test_view_is_persistent():
    view = SubscribeView(Character(3, "Lucina"))

    assert view.is_persistent()
    [button] = view.children
    assert (button.item.label, button.item.custom_id) == ("Subscribe to Lucina", "subscribe:3")


def test_click_subscribes_and_answers_privately():
    lucina = add_character("Lucina")

    assert click(SubscribeView(lucina)) == [("Ping for Lucina has been added", True, None)]
    assert art_ping_repository.get_art_ping_users([lucina.id]) == ["7"]


def test_click_only_subscribes():
    view = SubscribeView(add_character("Lucina"))
    click(view)

    assert click(view) == [("Ping for Lucina already exists", True, None)]


def test_click_names_a_renamed_character_by_its_new_name():
    lucina = add_character("Lucina")
    view = SubscribeView(lucina)
    alias_repository.add_alias(lucina.id, "Masked_Marth")
    alias_repository.set_primary_name(lucina.id, "Masked_Marth")

    assert click(view) == [("Ping for Masked_Marth has been added", True, None)]


def test_click_on_a_removed_character_is_answered_privately():
    lucina = add_character("Lucina")
    character_repository.remove_character(lucina.id)

    assert click(SubscribeView(lucina)) == [("This character doesn't exist anymore", True, None)]


def test_click_has_no_cooldown():
    view = SubscribeView(add_character("Lucina"))
    click(view)

    assert click(SubscribeView(add_character("Marth"))) == [("Ping for Marth has been added", True, None)]


def test_long_names_fit_the_label():
    view = SubscribeView(Character(3, "A" * 100))

    assert len(view.children[0].item.label) == 80


def test_failed_click_is_answered_privately(monkeypatch, caplog):
    def failing_subscribe(user_id, character_id):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(art_ping_service, "subscribe", failing_subscribe)

    assert click(SubscribeView(Character(3, "Lucina"))) == [("Something went wrong while subscribing", True, None)]
    assert "database is locked" in caplog.text
