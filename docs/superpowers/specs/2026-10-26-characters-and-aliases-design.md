# Characters and aliases: design

Describes the bot as built. Characters are what users subscribe to for art pings (see the art pings spec);
non-admins add them by vote (see the character votes spec).

## Intent

Keep one list of characters that everyone refers to the same way, whatever casing or nickname they type:
`black_knight`, `BLACK_KNIGHT` and an alias like `Zelgius` all reach the same character, and replies always
show its one name.

## Commands

| Command | Who | Reply on success |
|---|---|---|
| `~addcharacter (character name)` | everyone; for non-admins a vote (votes spec) | `Character Black_Knight has been added` |
| `~removecharacter (character name)` | admins | `Character Black_Knight has been removed` |
| `~checkcharacter (character name)` | everyone | see below |
| `~addalias (character name) (alias)` | admins | `Alias Zelgius has been added to Black_Knight` |
| `~removealias (character name) (alias)` | admins | `Alias Zelgius has been removed from Black_Knight` |
| `~setprimaryname (alias)` | admins | `Zelgius is now the primary name; Black_Knight has become an alias` |

`~checkcharacter` replies with up to three lines (aliases alphabetically); the aliases line is left out when there are none, and the
users line is always there (empty after `Users: ` when nobody is subscribed):

```
Character entry found for Furina
Aliases: Archon, Focalors
Users: Alice, Bob
```

Users are shown by display name: the client's cache first, a Discord request only on a miss, and
`Unknown user (id)` when the user can't be found.

## Rules

- **Lookup:** every command that takes a character name accepts the name or any alias, and replies with the
  name. Matching ignores case.
- **Name casing:** names and aliases are normalized when read from a message: each part, split on `_`, `!` or
  `'`, gets a capital and the rest lowercase (`black_KNIGHT` → `Black_Knight`, `m!robin` → `M!Robin`,
  `l'arachel` → `L'Arachel`). They are stored, and echoed in replies, that way, including unknown names in
  error replies.
- **One name, one owner:** a name is either one character's name or one alias, never both. Adding a
  character or alias whose name is taken answers `Character Lucina already exists` or
  `Focalors is already an alias of Furina`.
- **Removing a character** removes its aliases and every subscription to it.
- **`~setprimaryname`** swaps an alias with the name in one transaction; subscriptions and other aliases are
  kept. Naming the current name answers `Black_Knight is already the primary name`.
- **`~removealias`** with a name that isn't that character's alias answers `X is not an alias of Black_Knight`.
- **Errors:** an unknown character answers `Character Marth doesn't exist`. `~addalias`/`~removealias` with
  only the character answer `Alias is missing. Usage: ...`; more than two words answers the one-name hint.
- **Admin adds and open votes:** an admin's `~addcharacter` also closes open votes for that name (votes spec).

## Data

`CHARACTERS (CHARACTER_ID, NAME UNIQUE COLLATE NOCASE)` and `ALIAS (CHARACTER_ID, ALIAS UNIQUE COLLATE NOCASE)`,
with `ON DELETE CASCADE` to `CHARACTERS`. The database only enforces uniqueness within each table;
`character_service.require_unused_name` checks across both. Migration `004` normalized existing names with the
`NORMALIZE_NAME` SQL function.

## Non-goals

- Currency names are not normalized (gacha currency spec).
- No renaming other than through an alias and `~setprimaryname`.

## Tests

`tests/fjormcord/bot/artping/service/test_character_service.py`, `test_alias_service.py`,
`util/test_name_util.py`.
