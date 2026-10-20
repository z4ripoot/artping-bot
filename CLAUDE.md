# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Discord bot for the Fjormcord community, built on discord.py (2.x) with a SQLite database. Features: character "art pings" (users subscribe to characters and get mentioned when art of them is posted), a gacha-currency wallet/scoreboard, and a scheduled Fire Emblem Heroes Coliseum closing reminder. The user-facing command list lives in `README.md`.

## Running

There is no `requirements.txt`, build step, linter config or test suite. The local `.venv` (Python 3.14) has `discord.py` installed.

```bash
.venv/Scripts/python application.py   # run the bot (needs discord.token in config.ini)
sqlite3 test.db < init_db.sql          # (re)create the schema — DROPs all tables first
```

Run from the repository root: `config/art_ping_config.py` reads `config.ini` via a relative path.

## Configuration

`config.ini` (committed) holds `discord.token`, `database.path` (defaults to the committed `test.db`), `tasks.coliseum_notification_channel_name`, and custom emoji IDs under `[emoji]`. Do not commit a real token.

## Architecture

Layered, all module-level functions (no classes besides the client):

- `application.py` — entry point; sets up logging, intents (`message_content` is required) and runs `ArtPingClient`.
- `client/art_ping_client.py` — `ArtPingClient(discord.Client)`. `on_message` is a single `if/elif` dispatcher over `~`-prefixed command constants (matched with `startswith` on the lowercased content). Admin-only commands are gated here via `message.author.guild_permissions.administrator`, returning `MESSAGE_DENIED` otherwise. Also hosts easter-egg replies and the Coliseum `tasks.loop` (fires Mondays at 18:00 and 22:00 local time). The `~help` text is hardcoded here — keep it in sync with the README when adding commands.
- `service/` — one module per feature; each handler takes the `discord.Message`, parses arguments, calls repositories, and **returns the reply string** (the client sends it). Some handlers are `async` because they resolve users/members via the client.
- `repository/` — raw SQL against SQLite. Each module opens its own module-level `CONN`/`CURSOR` at import time (`util/repository_util.get_database_connection`), uses `?` parameters, compares names case-insensitively with `LOWER(...)`, and catches errors by logging and returning `None` — callers must handle `None`.
- `util/` — argument parsing (`message_util.get_entries` / `get_first` split the message on single spaces; argument at index 1+) and row-to-value helpers.

Schema (`init_db.sql`): `CHARACTERS`, `ALIAS`, `PINGS` (character ↔ user ID), `GACHA_CURRENCY`, `GACHA_CURRENCY_WALLET`. Users are stored as Discord user ID text and rendered as `<@id>` mentions.

The `~addalias` / `~removealias` commands are wired up but `service/alias_service.py` is still a stub.
