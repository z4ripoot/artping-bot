import pytest

from fjormcord.bot.artping.database import connect, set_database_connection
from fjormcord.bot.artping.service import art_ping_service
from tests.fakes import FakeClient


@pytest.fixture(autouse=True)
def database():
    connection = connect(":memory:")
    set_database_connection(connection)
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def art_ping_cooldowns(monkeypatch):
    # Cooldowns are kept per character ID, and every test's database starts again at ID 1
    monkeypatch.setattr(art_ping_service, "_last_pinged", {})


@pytest.fixture
def client():
    return FakeClient({1: "Alice", 2: "Bob"})
