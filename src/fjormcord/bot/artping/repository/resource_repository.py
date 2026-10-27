from fjormcord.bot.artping.database import execute, fetch_names, fetch_one
from fjormcord.bot.artping.model.resource import Resource


def get_resource(name: str) -> Resource | None:
    sql = """
        SELECT R.NAME AS name, R.CONTENT AS content, R.SOURCE AS source
        FROM RESOURCE R
        WHERE R.NAME = ?
        """

    return fetch_one(Resource, sql, (name,))


def get_resource_names(prefix: str = "", limit: int = -1) -> list[str]:
    return fetch_names("SELECT R.NAME FROM RESOURCE R", prefix, limit)


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
