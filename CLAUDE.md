# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Discord bot for the Fjormcord community, built on discord.py (2.x) with a SQLite database. Features: character "art pings" (users subscribe to characters and get mentioned when art of them is posted), a gacha-currency wallet/scoreboard, and a scheduled Fire Emblem Heroes Coliseum closing reminder. The user-facing command list lives in `README.md`.

## Commands

```bash
.venv/Scripts/python -m pip install -e ".[dev]"     # editable install with test dependencies (pyproject.toml)
.venv/Scripts/python -m fjormcord.bot.artping        # run the bot (needs discord.token in config.ini); also: artping-bot
.venv/Scripts/python -m pytest                       # run all tests
.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/service/test_art_ping_service.py::test_add_and_remove_ping   # single test
sqlite3 test.db < db/schema.sql                      # (re)create the schema — DROPs all tables first
```

Without the editable install, run with `PYTHONPATH=src`. Use `-e` rather than a plain `pip install .`: `config.py` locates `config.ini` relative to its own file in `src/`, which breaks once the code is copied into `site-packages`. There is no linter configured.

## Layout

`src/` layout: all code is in the `fjormcord.bot.artping` package under `src/fjormcord/bot/artping/`. `fjormcord/` and `fjormcord/bot/` are PEP 420 namespace packages — they deliberately have **no `__init__.py`** (don't add one), so other distributions can share the `fjormcord` namespace; `artping/` is a regular package. Paths below are relative to `src/fjormcord/bot/artping/`.

Tests live in `tests/fjormcord/bot/artping/`, mirroring the source tree one-to-one (e.g. `tests/fjormcord/bot/artping/service/` ↔ `src/fjormcord/bot/artping/service/`); shared fixtures and fakes stay in `tests/` itself. Test directories only have an `__init__.py` where they contain Python files, so `tests/fjormcord/` and `tests/fjormcord/bot/` have none. pytest therefore imports the test modules as `artping.…` (e.g. `artping.service.test_currency_service`); never add a top-level `artping` package, or it would collide. pytest finds the package via `pythonpath` in `pyproject.toml`, so tests run without installing.

## Configuration

`config.ini` (committed, in the repository root) holds `discord.token`, `database.path` (defaults to the committed `test.db`), `tasks.coliseum_notification_channel_name`, and custom emoji IDs under `[emoji]`. `config.py` locates it, and resolves relative paths in it, against the repository root, so the bot can be started from any directory. Do not commit a real token.

## Architecture

Layered, all module-level functions:

- `__main__.py` — entry point; sets up logging, intents (`message_content` is required) and runs `ArtPingClient`.
- `bot.py` — `ArtPingClient(discord.Client)`: `on_message` looks the first word up in `COMMANDS_BY_NAME` (case-insensitive, exact match), enforces `admin_only`, calls the handler and sends the returned string. Handler exceptions are logged and answered with a generic failure message. Also hosts the easter-egg replies and the Coliseum `tasks.loop`.
- `commands.py` — the `COMMANDS` table. Each `Command` holds its name, handler, help text/usage, help section and `admin_only` flag; `~help` is generated from it (admin commands only shown to admins). Adding a command = write a service handler + add a `Command` entry, keeping the list grouped by section with admin-only commands last.
- `service/` — one module per feature. Every handler has the signature `handler(client, message)` and returns the reply string, either directly or as a coroutine (only the handlers that resolve usernames through the client are `async`).
- `repository/` — raw SQL against SQLite through the single shared connection from `database.get_database_connection()`. Rows are `sqlite3.Row` (access columns by name, e.g. `row['NAME']`); lookups return `None` when nothing is found, writes use `with conn:` to commit. Database errors are not caught here — they propagate to the client's generic handler. Names are matched case-insensitively with `LOWER(...)`.
- `util/` — argument parsing (`message_util`: whitespace-split arguments after the command word) and username lookup (`user_util.get_username`, never raises).

The connection enables `PRAGMA foreign_keys`, which the schema's `ON DELETE CASCADE` relies on (removing a character/currency removes its pings/wallets). Tests swap in an in-memory database built from `db/schema.sql` via `set_database_connection` (autouse fixture in `tests/conftest.py`); fake messages and a fake client are in `tests/fakes.py`.

Schema (`db/schema.sql`): `CHARACTERS`, `ALIAS`, `PINGS` (character ↔ user ID), `GACHA_CURRENCY`, `GACHA_CURRENCY_WALLET`. Users are stored as Discord user ID text and rendered as `<@id>` mentions.

The `~addalias` / `~removealias` commands are registered but `service/alias_service.py` only replies that aliases aren't supported yet. Migrating dispatch to `discord.ext.commands` is a noted TODO in `commands.py`.
