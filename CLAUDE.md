# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Discord bot for the Fjormcord community, built on discord.py (2.x) with a SQLite database. Features: character "art pings" (users subscribe to characters and get mentioned when art of them is posted), a gacha-currency wallet/scoreboard, and a scheduled Fire Emblem Heroes Coliseum closing reminder. The user-facing command list lives in `README.md`.

## Commands

```bash
.venv/Scripts/python -m pip install -e ".[dev]"     # editable install with test dependencies (pyproject.toml)
.venv/Scripts/python -m fjormcord.bot.artping        # run the bot (exits unless config.ini sets discord.token); also: artping-bot
.venv/Scripts/python -m pytest                       # run all tests
.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/service/test_art_ping_service.py::test_add_and_remove_ping   # single test
```

To reset a local database, delete the file; it is recreated on the next start.

Without the editable install, run with `PYTHONPATH=src`. Use `-e` rather than a plain `pip install .`: `config.py` locates the config files relative to its own file in `src/`, which breaks once the code is copied into `site-packages`. There is no linter configured.

## Layout

`src/` layout: all code is in the `fjormcord.bot.artping` package under `src/fjormcord/bot/artping/`. `fjormcord/` and `fjormcord/bot/` are PEP 420 namespace packages — they deliberately have **no `__init__.py`** (don't add one), so other distributions can share the `fjormcord` namespace; `artping/` is a regular package. Paths below are relative to `src/fjormcord/bot/artping/`.

Tests live in `tests/fjormcord/bot/artping/`, mirroring the source tree one-to-one (e.g. `tests/fjormcord/bot/artping/service/` ↔ `src/fjormcord/bot/artping/service/`); shared fixtures and fakes stay in `tests/` itself. Test directories only have an `__init__.py` where they contain Python files, so `tests/fjormcord/` and `tests/fjormcord/bot/` have none. pytest therefore imports the test modules as `artping.…` (e.g. `artping.service.test_currency_service`); never add a top-level `artping` package, or it would collide. pytest finds the package via `pythonpath` in `pyproject.toml`, so tests run without installing.

## Configuration

`config.example.ini` (committed, in the repository root) holds the defaults: an empty `discord.token`, `database.path` (`test.db`), `tasks.coliseum_notification_channel_id` (empty: no Coliseum reminders), and custom emoji IDs under `[emoji]`. `config.ini` (gitignored) is read after it and overrides any setting; it holds the real token, and production edits it by hand. The bot exits with a hint when no token is set. `config.py` locates both, and resolves relative paths in them, against the repository root, so the bot can be started from any directory. Never put a token in `config.example.ini`.

The database file is gitignored. Tests need neither `config.ini` nor a database file.

## Database migrations

The schema is defined only by the numbered scripts in `db/migrations/` (`001_initial_schema.sql`, `002_unique_names.sql`, ...); there is no separate schema file. `database.connect` applies every script numbered above the database's `PRAGMA user_version`, each in its own transaction together with the version bump, so a new database runs them all and the live one gets upgraded on its next start. `__main__` opens the database before connecting to Discord, so a failing migration stops the bot.

- To change the schema, add the next numbered script; never edit one that has been released, since the live database already ran it.
- `001` uses `CREATE TABLE IF NOT EXISTS` because the live database predates versioning (`user_version` 0, tables already present).
- Migrations run before `PRAGMA foreign_keys` is enabled: SQLite can't alter constraints, so changing one means rebuilding the table (create `NEW_X`, copy, drop `X`, rename), and with foreign keys on, dropping the table would cascade-delete its pings and wallets. The runner checks `PRAGMA foreign_key_check` before committing.

## Architecture

Layered, all module-level functions:

- `__main__.py` — entry point; sets up logging, checks the token, opens (and migrates) the database, sets intents (`message_content` is required) and runs `ArtPingClient`.
- `bot.py` — `ArtPingClient(discord.Client)`: `on_message` looks the first word up in `COMMANDS_BY_NAME` (case-insensitive, exact match), silently ignores `admin_only` commands from non-admins, calls the handler and sends the returned string. Handler exceptions are logged and answered with a generic failure message. `on_ready` starts the Coliseum reminder.
- `easter_eggs.py` — the custom-emoji replies to whole messages such as "thanks lorenz" and "chromk" (`EASTER_EGG_REPLIES`, emoji from the `[emoji]` config section); `on_message` sends them before command dispatch.
- `coliseum.py` — the Coliseum closing reminder: a module-level `tasks.loop` (times in UTC) that `start_coliseum_notification(client)` starts with the client, once, and only when `tasks.coliseum_notification_channel_id` is set.
- `commands.py` — the `COMMANDS` table. Each `Command` holds its name, handler, help text/usage, help section and `admin_only` flag; `~help` is generated from it (admin commands only shown to admins). Adding a command = write a service handler + add a `Command` entry, keeping the list grouped by section with admin-only commands last.
- `service/` — one module per feature. Every handler has the signature `handler(client, message)` and returns the reply string, either directly or as a coroutine (only the handlers that resolve usernames through the client are `async`). Handlers reject a command by raising rather than returning the error: `MissingArgument("character name")` when a required argument is missing (answered with "Character name is missing. Usage: …", formatted from the command's `usage` tuple by `commands.format_usage`, the same formatter `~help` uses), and `CommandError(message)` for anything else (logged as a warning and sent as the reply). Both live in `message_util`, along with `get_single_name(content, "character name")` for commands that take exactly one name; `require_character` / `require_currency` (in their services) look a name up or raise "… doesn't exist". `~artping` has a per-character cooldown (`ART_PING_COOLDOWN_SECONDS`, admins exempt), kept in memory in `art_ping_service._last_pinged`.
- `repository/` — raw SQL against SQLite through the single shared connection from `database.get_database_connection()`. Queries read `sqlite3.Row`s, but only the repository touches column names: it returns the `model/` dataclasses, plain values, or a `bool` from the `has_…` checks, so services use attributes like `character.id`. Lookups return `None` when nothing is found, writes use `with conn:` to commit. Database errors are not caught here — they propagate to the client's generic handler. Character and currency names are `UNIQUE COLLATE NOCASE`, so a plain `NAME = ?` already matches case-insensitively (and uses the index); don't wrap them in `LOWER(...)`.
- `model/` — the frozen dataclasses the repositories return, one module per feature (`character.Character`; `currency.Currency`, `WalletEntry`, `ScoreboardEntry`). They hold data only and import nothing from the project.
- `util/` — message handling (`message_util`: whitespace-split arguments after the command word, and `split_message`, which `on_message` uses to keep replies under Discord's 2000-character limit) and users (`user_util.is_administrator`, which lives here rather than in `commands.py` so services can use it without a circular import; `user_util.get_username`: the client's cache first, a Discord request only on a miss; never raises — look users up only for what is shown, e.g. one scoreboard page).

The connection enables `PRAGMA foreign_keys`, which the schema's `ON DELETE CASCADE` relies on (removing a character/currency removes its pings/wallets). Tests swap in an in-memory database built by `database.connect(":memory:")` via `set_database_connection` (autouse fixture in `tests/conftest.py`, which also clears the art ping cooldowns, since every test's database reuses the same character IDs); fake messages and a fake client are in `tests/fakes.py`, along with `reply(handler, client, message)`, which runs a handler as the bot does (awaiting it, and turning a `CommandError` into its message).

Schema (`db/migrations/`): `CHARACTERS`, `ALIAS`, `PINGS` (character ↔ user ID), `GACHA_CURRENCY`, `GACHA_CURRENCY_WALLET`. Users are stored as Discord user ID text and rendered as `<@id>` mentions.

The `~addalias` / `~removealias` commands are registered but `service/alias_service.py` only replies that aliases aren't supported yet. Migrating dispatch to `discord.ext.commands` is a noted TODO in `commands.py`.
