from fjormcord.bot.artping.database import execute, get_database_connection
from fjormcord.bot.artping.model.resource import Resource


def get_resource(name: str) -> Resource | None:
    sql = """
        SELECT R.NAME AS name, R.CONTENT AS content, R.SOURCE AS source
        FROM RESOURCE R
        WHERE R.NAME = ?
        """

    row = get_database_connection().execute(sql, (name,)).fetchone()
    return Resource(**row) if row else None


def get_resource_names() -> list[str]:
    sql = """
        SELECT R.NAME
        FROM RESOURCE R
        ORDER BY R.NAME
        """

    # Each row holds just the one selected column
    return [name for (name,) in get_database_connection().execute(sql)]


def set_resource(resource: Resource):
    # Replaces a resource of the same name, including the casing of its name
    sql = """
        INSERT INTO RESOURCE (NAME, CONTENT, SOURCE)
        VALUES (?, ?, ?)
        ON CONFLICT (NAME) DO UPDATE SET NAME = excluded.NAME, CONTENT = excluded.CONTENT, SOURCE = excluded.SOURCE
        """

    execute(sql, (resource.name, resource.content, resource.source))


def remove_resource(name: str):
    sql = """
        DELETE FROM RESOURCE
        WHERE NAME = ?
        """

    execute(sql, (name,))
