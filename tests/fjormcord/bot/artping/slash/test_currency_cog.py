from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.slash.currency_cog import CurrencyCog
from tests.fakes import FakeClient, FakeInteraction, invoke


def test_set_currency():
    currency_repository.add_currency("Orbs")
    cog = CurrencyCog(None)
    interaction = FakeInteraction(user_id=4)

    invoke(cog.set_currency, interaction, cog, currency="orbs", amount=50)

    assert currency_repository.get_wallet("4")[0].amount == 50
    assert interaction.sent[0][1] is False


def test_amount_too_large_is_refused_by_the_service():
    currency_repository.add_currency("Orbs")
    cog = CurrencyCog(None)
    interaction = FakeInteraction()

    invoke(cog.set_currency, interaction, cog, currency="Orbs", amount=2 ** 63)

    assert interaction.sent[0][:2] == ("Failed to set currency. The amount is too large", True)


def test_clear_currency():
    currency_repository.add_currency("Orbs")
    cog = CurrencyCog(None)
    invoke(cog.set_currency, FakeInteraction(user_id=4), cog, currency="Orbs", amount=5)
    interaction = FakeInteraction(user_id=4)

    invoke(cog.clear_currency, interaction, cog, currency="Orbs")

    assert currency_repository.get_wallet("4") == []


def test_empty_wallet_names_slash_command():
    cog = CurrencyCog(None)
    interaction = FakeInteraction()

    invoke(cog.check_wallet, interaction, cog)

    assert interaction.sent[0][0] == "Your wallet is empty. Use /setcurrency to add a currency"


def test_wallet_names_the_member():
    currency_repository.add_currency("Orbs")
    cog = CurrencyCog(None)
    invoke(cog.set_currency, FakeInteraction(user_id=4), cog, currency="Orbs", amount=5)
    interaction = FakeInteraction(user_id=4)
    interaction.user.display_name = "Lissa"

    invoke(cog.check_wallet, interaction, cog)

    assert interaction.sent[0][0].startswith("User Lissa's wallet:")


def test_scoreboard_next_page_hint():
    currency_repository.add_currency("Orbs")
    cog = CurrencyCog(None)
    client = FakeClient(users={user_id: f"user{user_id}" for user_id in range(1, 13)})
    for user_id in range(1, 13):
        invoke(cog.set_currency, FakeInteraction(user_id=user_id), cog, currency="Orbs", amount=user_id)
    interaction = FakeInteraction(client=client)

    invoke(cog.scoreboard, interaction, cog, currency="Orbs", page=1)

    assert interaction.response.deferred == [{}]
    assert interaction.sent[0][0].endswith("Use /scoreboard currency:Orbs page:2 for the next page")


def test_admin_currency_commands_are_admin_only():
    cog = CurrencyCog(None)
    for command in (cog.add_currency, cog.remove_currency):
        assert command.default_permissions.administrator
        assert command.guild_only
    refused = FakeInteraction()
    added = FakeInteraction(administrator=True)

    invoke(cog.add_currency, refused, cog, currency="Orbs")
    invoke(cog.add_currency, added, cog, currency="Orbs")
    removed = FakeInteraction(administrator=True)
    invoke(cog.remove_currency, removed, cog, currency="orbs")

    assert refused.sent[0][:2] == ("This command is for admins only", True)
    assert added.sent[0][0] == "Currency Orbs has been added"
    assert removed.sent[0][0] == "Currency Orbs has been removed"
    assert currency_repository.get_currency_names() == []
