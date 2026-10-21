import pytest

from fjormcord.bot.artping.database import connect, set_database_connection
from tests.fakes import FakeClient


@pytest.fixture(autouse=True)
def database():
    connection = connect(":memory:")
    set_database_connection(connection)
    yield connection
    connection.close()


@pytest.fixture
def client():
    return FakeClient({1: "Alice", 2: "Bob"})
