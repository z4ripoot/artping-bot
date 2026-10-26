# Configuration and database: design

Describes the bot as built: startup, settings and the SQLite schema with its migrations.

## Intent

Run from any directory with one hand-edited file holding the secrets, and upgrade the live database safely on
start, without a separate migration step.

## Startup (`__main__.py`)

1. Logging to the console (`time [LEVEL] file function message`).
2. Settings are read. Without a token the bot exits with
   `No Discord token configured. Create config.ini with your bot's token, see README.md`.
3. The database is opened and migrated **before** connecting to Discord, so a failing migration stops the bot
   instead of failing every command.
4. Intents: the defaults plus `message_content`, which must also be enabled in the Discord developer portal.
   The default intents include reactions, used by character votes.

## Configuration (`config.py`)

- `config.example.ini` (committed) holds a default for every setting; `config.ini` (gitignored, edited by hand
  in production) is read after it and overrides any setting. Both are in the repository root and read as
  UTF-8, with or without a byte order mark.
- Both files, and relative paths in them, are located against the repository root, not the working
  directory.
- They are read once into a frozen `Settings` dataclass (`config.read_settings()`); code uses its typed
  fields, not section and key names.
- A setting missing from both files stops the bot at startup.
- Adding a setting means a default in `config.example.ini`, a `Settings` field and its parsing in
  `load_settings`. A token never goes in `config.example.ini`.

| Setting | Default | Meaning |
|---|---|---|
| `discord.token` | empty | the bot's token; empty exits at startup |
| `database.path` | `test.db` | the SQLite file, created when missing |
| `art_ping.cooldown_seconds` | `1` | `~artping` cooldown per user; 0 turns it off |
| `character_vote.votes_needed` | `5` | reactions a vote needs; below 2 turns voting off |
| `character_vote.emoji` | `⭐` | the vote emoji, Unicode or `<:name:id>` |
| `tasks.coliseum_notification_channel_id` | empty | Coliseum reminder channel; empty turns them off |
| `[emoji]` | the community's emoji | custom emoji for easter eggs |

## Database (`database.py`)

- One shared SQLite connection, opened on first use, rows readable by column name.
- `PRAGMA foreign_keys` is on, which the schema's `ON DELETE CASCADE` relies on.
- `NORMALIZE_NAME` is registered as an SQL function for migrations (characters and aliases spec).

## Migrations

- The schema is defined only by the numbered scripts in `db/migrations/`; there is no separate schema file.
- `PRAGMA user_version` is the number of the last applied script. On open, every higher script runs in its
  own transaction together with the version bump, so it is applied entirely or not at all, and is checked with
  `PRAGMA foreign_key_check` before committing.
- Migrations run before foreign keys are enabled, because changing a constraint means rebuilding the table
  (create `NEW_X`, copy, drop `X`, rename), and with foreign keys on the drop would cascade-delete the rows
  referencing it.
- A released script is never edited; a change is the next numbered script.
- `001` uses `CREATE TABLE IF NOT EXISTS` because the live database predates versioning.

| Script | Change |
|---|---|
| `001_initial_schema.sql` | `CHARACTERS`, `ALIAS`, `PINGS`, `GACHA_CURRENCY`, `GACHA_CURRENCY_WALLET` |
| `002_unique_names.sql` | character and currency names unique ignoring case |
| `003_unique_aliases.sql` | aliases unique ignoring case |
| `004_normalize_names.sql` | normalized casing of existing names and aliases |
| `005_character_votes.sql` | `CHARACTER_VOTE` for open votes |

Resetting a local database means deleting the file; it is recreated on the next start.

## Tests

`tests/fjormcord/bot/artping/test_config.py`, `test_database.py`, `test_main.py`. Tests need neither
`config.ini` nor a database file: an autouse fixture swaps in an in-memory database.
