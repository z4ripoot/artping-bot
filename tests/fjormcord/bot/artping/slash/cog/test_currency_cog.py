import pytest

from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.slash.cog.currency_cog import CurrencyCog
from tests.fakes import FakeClient, FakeInteraction, button_labels, invoke


@pytest.fixture
def cog():
    return CurrencyCog()


def test_set_currency(cog):
    currency_repository.add_currency("Orbs")
    interaction = FakeInteraction(user_id=4)

    invoke(cog.set_currency, interaction, cog, currency="orbs", amount=50)

    assert currency_repository.get_wallet("4")[0].amount == 50
    assert interaction.sent[0].ephemeral is False


def test_amount_too_large_is_refused_by_the_service(cog):
    currency_repository.add_currency("Orbs")
    interaction = FakeInteraction()

    invoke(cog.set_currency, interaction, cog, currency="Orbs", amount=2**63)

    assert interaction.sent[0].content == "Failed to set currency. The amount is too large"
    assert interaction.sent[0].ephemeral is True


def test_clear_currency(cog):
    currency_repository.add_currency("Orbs")
    invoke(cog.set_currency, FakeInteraction(user_id=4), cog, currency="Orbs", amount=5)
    interaction = FakeInteraction(user_id=4)

    invoke(cog.clear_currency, interaction, cog, currency="Orbs")

    assert currency_repository.get_wallet("4") == []


def test_empty_wallet_names_slash_command(cog):
    interaction = FakeInteraction()

    invoke(cog.check_wallet, interaction, cog)

    assert interaction.sent[0].content == "Your wallet is empty. Use /setcurrency to add a currency"


def test_wallet_names_the_member(cog):
    currency_repository.add_currency("Orbs")
    invoke(cog.set_currency, FakeInteraction(user_id=4), cog, currency="Orbs", amount=5)
    interaction = FakeInteraction(user_id=4)
    interaction.user.display_name = "Lissa"

    invoke(cog.check_wallet, interaction, cog)

    assert interaction.sent[0].content == "### Lissa's wallet\nOrbs: 5"


def test_scoreboard_is_sent_with_its_buttons(cog):
    currency_repository.add_currency("Orbs")
    client = FakeClient(users={user_id: f"user{user_id}" for user_id in range(1, 13)})
    for user_id in range(1, 13):
        invoke(cog.set_currency, FakeInteraction(user_id=user_id), cog, currency="Orbs", amount=user_id)
    interaction = FakeInteraction(client=client)

    invoke(cog.scoreboard, interaction, cog, currency="Orbs", page=1)

    assert interaction.response.deferred == [{}]
    assert interaction.sent[0].content.splitlines()[-1] == "10. user3 (3)"
    assert button_labels(interaction.channel.last_message().view) == ["◀ Previous", "Next ▶"]


def test_admin_currency_commands_are_admin_only(cog):
    for command in (cog.add_currency, cog.remove_currency):
        assert command.default_permissions.administrator
        assert command.guild_only
    refused = FakeInteraction()
    added = FakeInteraction(administrator=True)

    invoke(cog.add_currency, refused, cog, currency="Orbs")
    invoke(cog.add_currency, added, cog, currency="Orbs")
    removed = FakeInteraction(administrator=True)
    invoke(cog.remove_currency, removed, cog, currency="orbs")

    assert refused.sent[0].content == "This command is for admins only"
    assert refused.sent[0].ephemeral is True
    assert added.sent[0].content == "Currency Orbs has been added"
    assert removed.sent[0].content == "Currency Orbs has been removed"
    assert currency_repository.get_currency_names() == []
