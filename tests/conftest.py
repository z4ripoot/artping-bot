import sqlite3

import pytest

from fjormcord.bot.artping.config import PROJECT_ROOT
from fjormcord.bot.artping.database import set_database_connection
from tests.fakes import FakeClient


@pytest.fixture(autouse=True)
def database():
    connection = sqlite3.connect(":memory:")
    connection.executescript((PROJECT_ROOT / "db" / "schema.sql").read_text())
    set_database_connection(connection)
    yield connection
    connection.close()


@pytest.fixture
def client():
    return FakeClient({1: "Alice", 2: "Bob"})
