from fjormcord.bot.artping.database import connect


def table_names(connection):
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_new_database_gets_schema(tmp_path):
    connection = connect(tmp_path / "new.db")

    assert {"CHARACTERS", "PINGS", "GACHA_CURRENCY", "GACHA_CURRENCY_WALLET"} <= table_names(connection)
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
