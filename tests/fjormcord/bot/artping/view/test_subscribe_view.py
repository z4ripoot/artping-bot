import asyncio

from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.repository import alias_repository, art_ping_repository, character_repository
from fjormcord.bot.artping.service import art_ping_service
from fjormcord.bot.artping.view.subscribe_view import SubscribeButton, SubscribeSelect
from tests.fakes import FakeInteraction, after_restart


def add_character(name):
    return Character(character_repository.add_character(name), name)


def click(button, user_id=7):
    interaction = FakeInteraction(user_id)
    asyncio.run(after_restart(button).callback(interaction))
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


def pick(select, character_ids, user_id=7):
    # Picks characters in the dropdown, rebuilt from its custom_id as after a restart; returns the answer
    rebuilt = after_restart(select)
    # discord.py has no public way to pick: it fills _values from the interaction's data
    rebuilt.item._values = [str(character_id) for character_id in character_ids]
    interaction = FakeInteraction(user_id)
    asyncio.run(rebuilt.callback(interaction))
    return interaction.sent


def test_select_lists_the_characters_and_allows_picking_all():
    select = SubscribeSelect.for_characters([Character(1, "Chrom"), Character(2, "Lucina")])

    assert [(option.label, option.value) for option in select.item.options] == [("Chrom", "1"), ("Lucina", "2")]
    assert (select.item.custom_id, select.item.min_values, select.item.max_values) == ("subscribe_select", 1, 2)


def test_select_holds_at_most_25_characters():
    select = SubscribeSelect.for_characters([Character(number, f"C{number:02}") for number in range(30)])

    assert len(select.item.options) == 25
    assert select.item.max_values == 25


def test_pick_after_restart_subscribes():
    chrom, lucina = add_character("Chrom"), add_character("Lucina")
    select = SubscribeSelect.for_characters([chrom, lucina])

    assert pick(select, [chrom.id, lucina.id]) == [("Pings for Chrom, Lucina have been added", True, None)]
    assert art_ping_repository.get_art_ping_users([lucina.id]) == ["7"]


def test_pick_reports_added_existing_and_removed():
    chrom, lucina, robin = add_character("Chrom"), add_character("Lucina"), add_character("Robin")
    art_ping_repository.add_ping(robin.id, "7")
    select = SubscribeSelect.for_characters([chrom, lucina, robin])
    character_repository.remove_character(lucina.id)

    assert pick(select, [chrom.id, lucina.id, robin.id]) == [
        (
            "Ping for Chrom has been added\nYou are already subscribed to Robin\n"
            "Some picked characters don't exist anymore",
            True,
            None,
        )
    ]
    assert art_ping_repository.get_art_ping_users([chrom.id]) == ["7"]


def test_pick_has_no_cooldown():
    chrom, lucina = add_character("Chrom"), add_character("Lucina")
    select = SubscribeSelect.for_characters([chrom, lucina])
    pick(select, [chrom.id])

    assert pick(select, [lucina.id]) == [("Ping for Lucina has been added", True, None)]


def test_pick_never_unsubscribes():
    # Leaving a character out of a later pick keeps its ping: unsubscribing is only done with removeping
    chrom, lucina = add_character("Chrom"), add_character("Lucina")
    select = SubscribeSelect.for_characters([chrom, lucina])
    pick(select, [chrom.id, lucina.id])

    assert pick(select, [chrom.id]) == [("You are already subscribed to Chrom", True, None)]
    assert art_ping_repository.get_art_ping_users([lucina.id]) == ["7"]


def test_button_click_never_unsubscribes():
    lucina = add_character("Lucina")
    button = SubscribeButton.for_character(lucina)
    click(button)
    click(button)

    assert art_ping_repository.get_art_ping_users([lucina.id]) == ["7"]
