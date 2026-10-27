import pytest

from fjormcord.bot.artping import config
from fjormcord.bot.artping.database import connect, set_database_connection
from tests.fakes import FakeClient

# Tests run with the example's settings, never with a developer's own config.ini; set before the test modules are
# imported, as some read the settings at import
config._settings = config.load_settings(config.EXAMPLE_CONFIG_FILE)


@pytest.fixture(autouse=True)
def database():
    connection = connect(":memory:")
    set_database_connection(connection)
    yield connection
    connection.close()


@pytest.fixture
def client():
    return FakeClient({1: "Alice", 2: "Bob"})
