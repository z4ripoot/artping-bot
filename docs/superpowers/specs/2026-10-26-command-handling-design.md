# Command handling: design

Describes the bot as built. Covers how messages become commands and replies (the legacy `~` path); the commands
themselves are in the feature specs (art pings, characters and aliases, character votes, gacha currency), and
the slash commands, which share the services and the cooldowns, in the slash commands design.

## Intent

Community members type short `~` commands in a channel and get a plain-text reply in the same channel. The
dispatch is one small loop around a table of commands, so adding a command means writing one handler and one
table entry, and `~help` stays in step with the table automatically.

## Dispatch (`legacy/dispatch.py`, called by `ArtPingClient.on_message`)

1. Messages from bots, this one included, get no reply at all (no commands, no easter eggs), so no bot can
   make this one spam or ping users. Messages without text are ignored too.
2. Easter eggs are answered first (see the easter eggs spec); this doesn't stop dispatch.
3. A message is a command when it starts with `~` and its first word, lowercased, is exactly a command name
   (`~CheckPing` works, `~checkpingx` doesn't). Otherwise, a resource of that name (ignoring case) is posted
   with no mentions allowed (resources spec); commands are looked up first, so a resource never hides one.
   Anything else gets no reply.
4. An `admin_only` command from a non-admin gets **no reply at all**, so the commands can't be used to make
   the bot spam. An admin is a member with the server's Administrator permission; in DMs nobody is an admin.
5. The cooldown is checked, the handler runs, and its reply is sent.

The table, the handlers (`legacy/*_handlers.py`, which only parse the message and call a service function) and
the dispatch all live in the `legacy` package.

## Arguments

Arguments are the whitespace-separated words after the command; repeated whitespace is ignored. Names can't
contain spaces: multi-word names use underscores (`Black_Knight`), and `~help` says so. A command taking one
name that gets more words answers `Only one name is allowed. Use underscores for multi-word names, e.g.
Black_Knight`.

## Handlers and errors

- Every handler is `handler(client, message)` and returns the reply, directly or as a coroutine.
- A missing argument raises `MissingArgument("character name")`, answered with
  `Character name is missing. Usage: ~addping (character name)`; the usage comes from the command's `usage`
  tuple, formatted the same way `~help` does.
- Any other refusal raises `CommandError(text)`: the text is logged as a warning and sent as the reply.
- Any other exception is logged with its traceback and answered with
  `Something went wrong while running ~command`.
- An empty reply sends nothing (used when a handler sent its own message, e.g. a vote).

## Replies

- Replies longer than Discord's 2000 characters are split into several messages: at line breaks where
  possible, then at spaces, and only a single word longer than the limit is cut.
- Replies echo user input, so the client never lets a reply mention `@everyone`, `@here` or roles; user
  mentions (art pings) are allowed.

## Cooldowns (`cooldowns.py`)

- One cooldown per user for every command (`commands.cooldown_seconds`, default 1): after a command, the
  user can't use any other command, `~` or slash, until it runs out. Other users are not held back. Posting a
  resource (`~hof`) counts as a command; easter egg replies and vote clicks don't.
- A user still cooling down is answered `You used a command recently. Try again in 3 seconds` (rounded up,
  `1 second` singular).
- Only a command that **succeeded** starts the cooldown, so a typo can be corrected right away.
- Admins never get a cooldown.
- Cooldowns are kept in memory and reset when the bot restarts. The clock is injectable for tests.

## `~help` (`legacy/commands.show_help`)

Generated from the `COMMANDS` table, in table order:

```
Commands (content in brackets is what to add when using command):
Use underscores for multi-word names, e.g. Black_Knight
All commands are also available as slash commands, type /
~artping (character name): Ping users for art of this character
...

Gacha Currency Commands:
...

Admin Commands:
...
```

Each line is the usage (`~setcurrency (currency name) (amount)`) and the description. The art ping section
has no heading. Admin commands are listed only to admins, under `Admin Commands:`. The table therefore keeps
each section together and admin-only commands last.

## Non-goals

- No quoted arguments or typed argument conversion. The `~` commands are not `discord.ext.commands` prefix
  commands: the client is a `commands.Bot` for its cogs, but `on_message` dispatches by hand and never calls
  `process_commands`.
- No reply to unknown commands (that aren't a resource either) or to admin commands from non-admins.

## Tests

`tests/fjormcord/bot/artping/test_bot.py` (dispatch, errors, splitting, mentions, cooldowns),
`legacy/test_commands.py` (`~help`), `test_cooldowns.py`, `util/test_message_util.py`.
