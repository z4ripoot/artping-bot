import sqlite3

import pytest

from fjormcord.bot.artping.database import MIGRATIONS_PATH, connect


def table_names(connection):
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def user_version(connection):
    return connection.execute("PRAGMA user_version").fetchone()[0]


def latest_version():
    return max(int(path.name.split("_")[0]) for path in MIGRATIONS_PATH.glob("*.sql"))


def unversioned_database(path):
    # A database as it was created before versioning: the initial schema, user_version 0
    connection = sqlite3.connect(path)
    connection.executescript((MIGRATIONS_PATH / "001_initial_schema.sql").read_text())
    return connection


def test_new_database_gets_schema(tmp_path):
    connection = connect(tmp_path / "new.db")

    assert table_names(connection) == {
        "CHARACTERS",
        "ALIAS",
        "PINGS",
        "GACHA_CURRENCY",
        "GACHA_CURRENCY_WALLET",
        "CHARACTER_VOTE",
        "CHARACTER_VOTE_VOTER",
        "RESOURCE",
        "VOTING_GAUNTLET",
        "VOTING_GAUNTLET_TRACKER",
    }
    assert user_version(connection) == latest_version()
    connection.close()


def test_existing_database_keeps_its_data(tmp_path):
    path = tmp_path / "existing.db"
    connection = connect(path)
    with connection:
        connection.execute("INSERT INTO CHARACTERS (NAME) VALUES ('Lucina')")
    connection.close()

    connection = connect(path)

    assert connection.execute("SELECT NAME FROM CHARACTERS").fetchall() == [("Lucina",)]
    connection.close()


def test_names_are_unique_regardless_of_case(tmp_path):
    connection = connect(tmp_path / "new.db")
    connection.execute("INSERT INTO CHARACTERS (NAME) VALUES ('Lucina')")
    connection.execute("INSERT INTO GACHA_CURRENCY (NAME) VALUES ('Orbs')")

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO CHARACTERS (NAME) VALUES ('lucina')")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO GACHA_CURRENCY (NAME) VALUES ('ORBS')")
    connection.close()


def test_aliases_are_unique_regardless_of_case(tmp_path):
    connection = connect(tmp_path / "new.db")
    connection.execute("INSERT INTO CHARACTERS (CHARACTER_ID, NAME) VALUES (1, 'Furina')")
    connection.execute("INSERT INTO CHARACTERS (CHARACTER_ID, NAME) VALUES (2, 'Lucina')")
    connection.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (1, 'Focalors')")

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (2, 'FOCALORS')")
    connection.close()


def test_unversioned_database_is_migrated_without_losing_data(tmp_path):
    path = tmp_path / "live.db"
    old = unversioned_database(path)
    with old:
        old.execute("INSERT INTO CHARACTERS (CHARACTER_ID, NAME) VALUES (7, 'Lucina')")
        old.execute("INSERT INTO PINGS (CHARACTER_ID, USER) VALUES (7, '1')")
        old.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (7, 'Lucy')")
        old.execute("INSERT INTO GACHA_CURRENCY (GACHA_CURRENCY_ID, NAME) VALUES (3, 'Orbs')")
        old.execute("INSERT INTO GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT) VALUES (3, '1', 50)")
    old.close()

    connection = connect(path)

    assert user_version(connection) == latest_version()
    assert connection.execute("SELECT CHARACTER_ID, NAME FROM CHARACTERS").fetchall() == [(7, "Lucina")]
    assert connection.execute("SELECT CHARACTER_ID, USER FROM PINGS").fetchall() == [(7, "1")]
    assert connection.execute("SELECT CHARACTER_ID, ALIAS FROM ALIAS").fetchall() == [(7, "Lucy")]
    assert connection.execute("SELECT GACHA_CURRENCY_ID, USER, AMOUNT FROM GACHA_CURRENCY_WALLET").fetchall() == [
        (3, "1", 50)
    ]
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO CHARACTERS (NAME) VALUES ('LUCINA')")
    connection.close()


def test_migration_normalizes_existing_names_and_aliases(tmp_path):
    path = tmp_path / "live.db"
    old = unversioned_database(path)
    with old:
        old.execute("INSERT INTO CHARACTERS (CHARACTER_ID, NAME) VALUES (7, 'black_KNIGHT')")
        old.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (7, 'zelgius')")
    old.close()

    connection = connect(path)

    assert connection.execute("SELECT NAME FROM CHARACTERS").fetchall() == [("Black_Knight",)]
    assert connection.execute("SELECT ALIAS FROM ALIAS").fetchall() == [("Zelgius",)]
    connection.close()


def test_failed_migration_leaves_database_unchanged(tmp_path):
    path = tmp_path / "duplicates.db"
    old = unversioned_database(path)
    with old:
        old.execute("INSERT INTO CHARACTERS (NAME) VALUES ('Lucina')")
        old.execute("INSERT INTO CHARACTERS (NAME) VALUES ('lucina')")
    old.close()

    with pytest.raises(sqlite3.IntegrityError):
        connect(path)

    # 001 changes nothing on an existing database; 002 is rolled back completely
    connection = sqlite3.connect(path)
    assert user_version(connection) == 1
    assert "NEW_CHARACTERS" not in table_names(connection)
    assert connection.execute("SELECT NAME FROM CHARACTERS ORDER BY CHARACTER_ID").fetchall() == [
        ("Lucina",),
        ("lucina",),
    ]
    connection.close()


def test_migrations_are_committed(tmp_path):
    path = tmp_path / "new.db"
    connect(path).close()

    connection = sqlite3.connect(path)
    assert user_version(connection) == latest_version()
    connection.close()


def test_database_newer_than_the_migrations_is_refused(tmp_path):
    # E.g. a development database that ran migrations which were later merged into fewer
    path = tmp_path / "dev.db"
    connect(path).close()
    old = sqlite3.connect(path)
    old.execute(f"PRAGMA user_version = {latest_version() + 7}")
    old.close()

    with pytest.raises(sqlite3.DatabaseError, match="Delete a development database"):
        connect(path)
