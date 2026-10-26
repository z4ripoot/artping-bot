# Slash commands: design

Adds slash commands (`/artping`, `/addping`, ...) next to the existing `~` commands. Describes a change, not
the bot as built; the existing behaviour is in the other specs, in particular command handling.

Marked **(my call)**: decisions the designer made that the owner didn't state; the owner can still overrule
them. Everything else was decided with the owner.

## Intent

Some community members prefer the `~` syntax and will keep using it, so it stays exactly as it is. Slash
commands are added as a second way to use the same bot: Discord shows the commands, their arguments and their
descriptions while typing, can autocomplete names, and hides admin commands from non-admins. This is the TODO
in `commands.py` ("consider migrating to `discord.ext.commands` (Bot + Cogs)"), done as an addition instead of
a replacement.

The current `~` implementation is kept as the **legacy** path: still supported, unchanged for its users, but
no longer where the command logic lives.

## Goals

- Every `~` command has a slash counterpart with the same name and the same effect, built on
  `discord.ext.commands.Bot` with one cog per feature and `discord.app_commands`.
- Both syntaxes run in one bot process and call the same service code, so a feature (or a fix) is written once
  and both behave the same.
- Anyone using `~` notices no difference: same replies, same errors, same `~help`, same silence towards
  non-admins using admin commands, same resource fallback.

## Non-goals

- Converting the `~` commands to `ext.commands` prefix commands. The legacy dispatch keeps its own table and
  loop (`on_message`).
- Moving the other non-command parts (the message easter eggs, the Coliseum reminder) into cogs. They stay
  where they are. **(my call)** Character voting does move, into its own cog (see Character votes).
- Removing or deprecating the `~` commands, or announcing that they will go.
- Context menus, modals, `hybrid_command`s, and buttons other than the vote button.

## Anti-goals (a failure even if it works)

- A `~` user sees a changed reply, error message, `~help` text or behaviour, beyond the single `~help` line
  below and the vote button, which the owner chose for both syntaxes.
- The two syntaxes drifting apart: a check, limit or message implemented in only one of them.
- A `/` command that can ping `@everyone`, `@here` or roles, or a resource post that pings anyone.
- The slash side making the bot fail to start when Discord rejects the command sync.

## Constraints

- discord.py stays at the pinned `2.7.1`; no new dependencies.
- The layering in `CLAUDE.md` stays: services hold the logic, repositories the SQL, models the data.
- A Discord interaction must be answered within 3 seconds, or deferred first.
- Only one cooldown store, one database connection, one vote flow.

## Structure

### Services take typed arguments

Today each handler is `handler(client, message)` and parses `message.content` itself. That is split in two:

- **Service functions** take what the command needs as typed arguments and return the reply string or raise
  `CommandError`, e.g. `art_ping_service.add_ping(user_id: str, name: str) -> str`,
  `currency_service.set_currency(user_id: str, name: str, amount: int) -> str`,
  `character_service.check_character(client, name: str) -> str`. They contain every check and message that
  exists today (unknown character, already subscribed, negative amount, page out of range, ...), so both
  syntaxes get them.
- **Legacy handlers** keep the `handler(client, message)` signature. They only parse the words of the message
  (`get_single_name`, `get_entries`, `MissingArgument`, "Only one name is allowed", "Please enter a valid
  amount", ...) and call the service function.

Three service replies name a command to use next: `check_wallet` ("Use ~setcurrency to add a currency"),
`get_scoreboard` ("Use ~scoreboard {currency} {page} for the next page") and `list_resources`
("Resources: ~hof, ..."). Slash users see the slash form instead ("Use /setcurrency ...", "Use /scoreboard
currency:{currency} page:{page} ...", "Resources: hof, ... (post one with /resource)"). These functions take
a parameter saying which syntax to answer in, with legacy as the default, so the legacy texts stay
byte-for-byte the same. **(my call)**

Argument-count and argument-format errors belong to the legacy handlers. Range and existence checks belong to
the services. Where a check is about the value itself (an amount that isn't a number), the slash side gets it
from Discord's option types instead.

The existing service tests keep running against the legacy handlers unchanged, which proves the `~` side
didn't change. New tests cover the service functions directly where the legacy tests don't already. **(my
call)**

### The legacy package **(my call)**

The `~` path moves into `fjormcord.bot.artping.legacy`:

- `legacy/commands.py`: the current `commands.py` (`Command`, `COMMANDS`, `COMMANDS_BY_NAME`,
  `format_usage`, `show_help`, `COMMAND_PREFIX`), with the TODO comment replaced by a pointer to this design.
- `legacy/handlers/` or one `legacy/<feature>_handlers.py` per service: the parsing handlers. The layout is
  the builder's choice.
- `legacy/dispatch.py`: what `ArtPingClient.on_message` / `get_message` / `send_resource` do today (command
  lookup, admin silence, cooldown check, error-to-reply, splitting long replies, resource fallback).
  `on_message` calls it.
- `MissingArgument`, `get_entries`, `get_single_name` and `MULTI_WORD_HINT` are legacy-only and may move with
  it; `CommandError` and `split_message` are shared and stay in `util/message_util`.

The tests move to mirror the source tree (`tests/fjormcord/bot/artping/legacy/...`).

### The slash package

`fjormcord.bot.artping.slash`, one cog per feature **(my call)**:

| Cog | Commands |
|---|---|
| `ArtPingCog` | `/artping`, `/addping`, `/removeping`, `/checkping` |
| `CharacterCog` | `/addcharacter`, `/checkcharacter`, `/removecharacter`, `/addalias`, `/removealias`, `/setprimaryname` |
| `CurrencyCog` | `/setcurrency`, `/clearcurrency`, `/checkwallet`, `/scoreboard`, `/addcurrency`, `/removecurrency` |
| `ResourceCog` | `/resource`, `/resources`, `/setresource`, `/removeresource` |
| `EasterEggCog` | `/lorenz`, `/chromk` |
| `CharacterVoteCog` | no commands: the vote button, and the vote listeners (see Character votes) |

Each command is a thin adapter: read the options, call the service function, send the reply. No checks or
messages of its own beyond Discord specifics (deferring, visibility).

### The client

`ArtPingClient` becomes a subclass of `discord.ext.commands.Bot` instead of `discord.Client`, so it can hold
cogs. It overrides `on_message` (as it does now) and never calls `process_commands`, so `ext.commands` prefix
handling never runs. The `command_prefix` that `Bot` requires is therefore unused, and `help_command=None`.
`setup_hook` adds the cogs and syncs the command tree.

## Commands

The names are the legacy names without `~`. Descriptions come from the legacy `COMMANDS` table, shortened
where Discord's 100-character limit for descriptions requires it.

### Options

- Character name and alias options autocomplete from the characters' names and aliases. Currency options
  autocomplete from the currencies. Resource options autocomplete from the resources. Autocomplete only
  suggests: typed values that match nothing still reach the service, which answers "... doesn't exist" as
  today.
- `/setcurrency amount` is an integer option with minimum 0, `/scoreboard page` an optional integer option
  with minimum 1. The service still checks the maximum amount and the page count.
- `/setresource link` is a string option; the service accepts the same links as today.

### Spaces in names

Slash options can contain spaces, which `~` arguments can't. The slash side trims the value and turns every
run of whitespace into one underscore before the name reaches the service, so `/addping Black Knight` finds
`Black_Knight` and `/addcharacter black knight` stores `Black_Knight`. This applies to character names,
aliases and currency names. Resource names keep their own rule (letters, digits, `_` and `-`), so a space
there is still refused by the service. Autocomplete suggests the stored names, with underscores.

### `/artping` with several characters

`~artping` takes any number of names. `/artping` has one required `character` option and optional ones
(`character2`, `character3`, ...) up to a configurable total, each autocompleted. The filled-in options go to
the service in order, which handles duplicates, aliases of the same character and unknown names as it does
today. Pinging more characters than the limit at once means using `~artping`.

- The limit is the new setting `art_ping.slash_max_characters`, default `10` in `config.example.ini`, with a
  `Settings` field and parsing in `load_settings`.
- Discord allows at most 25 options per command, so a value outside 1–25 stops the bot at startup with a
  clear message, like other invalid settings.
- The options are part of the command's registration with Discord, so the limit is read once when the cogs
  are set up. A change takes effect after a restart, through the sync that runs on every start.
- discord.py builds a command's options from its callback's signature, so the builder has to generate the
  `/artping` callback (or its signature) from the setting. How is up to the builder, but the result has to be
  testable with the limit set to other values.

### `/resource name`

Replaces `~<resource>`, which has no slash equivalent, since slash command names are fixed. It posts the
content with `AllowedMentions.none()`, split into several messages like today if it is too long. The `~`
check that a resource can't be named after a command keeps referring to the legacy table.

### `/lorenz` and `/chromk`

These are slash versions of the easter eggs, which have no `~` command. They post the same reply as the
message easter eggs: `/lorenz` the `lorenz_smile` emoji, `/chromk` the 3×4 picture, both taken from
`easter_eggs.py` so they stay in step. Replies are public, anyone can use them, and there's no cooldown,
like the message easter eggs. The message easter eggs ("thanks lorenz", "chromk") stay as they are.

### Admin commands

- They are marked with `app_commands.default_permissions(administrator=True)`, so Discord hides them from
  non-admins.
- Server admins can override that visibility in the server settings, so each admin command also checks
  `user_util.is_administrator(interaction.user)`. A non-admin gets an ephemeral "This command is for admins
  only". A slash command has to be answered, so the legacy silence can't carry over. **(my call)**

### No `/help`

Discord's command picker already lists every slash command with its description and options, so there is no
`/help`. **(my call)** `~help` gets one extra line under the multi-word hint: "All commands are also
available as slash commands, type /". This is the only visible change to the legacy side. **(my call)**

### DMs

Slash commands work wherever the `~` command works today. `/addcharacter` from a non-admin in a DM gets the
same "Votes can only be started in a server" error. Admin commands are `guild_only`. **(my call)**

## Replies

- A reply is sent as the interaction response with the same allowed mentions as today (users only).
  `/artping` therefore pings the subscribers just like `~artping`.
- Successful replies are public, like the `~` replies. **(my call)**
- `CommandError` replies are ephemeral, so a typo isn't posted for everyone. **(my call)**
- Other exceptions are logged with their traceback and answered, ephemerally, with
  `Something went wrong while running /command`. One cog-level or tree-level error handler does this for
  every command.
- Replies longer than 2000 characters are split with `split_message`: the first part is the response, the
  rest are follow-ups.
- An empty reply (a passed-on vote) sends nothing more.
- Commands that wait on Discord (`/checkcharacter`, `/scoreboard`, `/setresource`, `/addcharacter`) defer
  first. After a defer Discord fixes the visibility, so their errors follow the defer's visibility rather than
  being ephemeral. The builder decides which commands defer and how, within the 3-second rule.

## Character votes

Votes change from ⭐ reactions to a **Vote button** on the vote message, for votes started with
`~addcharacter` and with `/addcharacter` alike (owner's decision). Everything else about votes stays as the
character votes spec describes: who gets a vote (non-admins, when `votes_needed` is 2 or more), the vote
message text, admins passing a vote at once, adding the character and subscribing exactly the voters in one
transaction, closing the other votes for the name, dropping a vote whose message is deleted or whose name
got taken, and votes never expiring.

### Starting a vote

`character_vote_service.start_vote` takes a `discord.Message` today and sends the vote message itself. It is
changed to take what it really needs: a way to send the vote message (with the button) and get the sent
message back, for its ID, plus the channel ID, whether this is in a server, and the proposer's user ID.
Legacy sends to the message's channel. Slash sends the vote message as the interaction response and stores
the ID of that response message (`interaction.original_response()`).

The vote message text no longer asks users to react. It says to click the button, e.g. `Vote to add
Black_Knight. Votes needed: 5`. The button's label shows the count: `Vote (0/5)`.

### Clicking the button

- A click from a user who hasn't voted records their vote. A click from a user who has voted takes it back
  (owner's decision).
- The clicker gets a short ephemeral confirmation ("Your vote for Black_Knight has been added" / "... has been
  taken back"), and the button label is updated to the new count. **(my call)**
- A click from an admin passes the vote right away, as an admin's reaction does now. The admin is subscribed
  along with the other voters. The click comes from a server member, so `is_administrator(interaction.user)`
  works without fetching the member.
- When the count reaches `votes_needed`, the vote passes: the message says `Character Black_Knight has been
  added` and the button is removed. The other vote messages for the name are edited as today, and lose their
  button too.
- A click on a vote whose name got taken another way, e.g. by an alias, drops the vote, as checking it does
  today. The message says why and loses its button.
- The proposer gets no automatic vote and votes by clicking, just as today they react like anyone else.
  **(my call)**
- Bots can't click buttons, so the "bots excluded" rule no longer needs code.

### Storage

Reactions were counted from Discord. Buttons keep no list of who clicked, so the voters are stored: a new
migration `007` adds a table of (vote message ID, user ID), with a foreign key to `CHARACTER_VOTE` that is
`ON DELETE CASCADE`, so closing or dropping a vote removes its voters. Passing a vote reads the voters from
it, in the same transaction as today.

### Restarts

The button must keep working after a restart, since votes don't expire. It is a persistent view: a fixed
`custom_id` and no timeout, registered with `bot.add_view` in `setup_hook`. The vote is found by
`interaction.message.id`. Clicks made while the bot is offline fail on the user's side ("This interaction
failed"), and the user can click again. At startup the open votes are checked as now, so a vote that already
meets a lowered `votes_needed` passes, and one whose name got taken is dropped.

### Converting the open ⭐ votes

Votes open in the live database when this is released have a ⭐ reaction and no button. At startup the bot
converts each one once: the users (bots excluded) who reacted with `character_vote.emoji` are stored as
voters, and the message is edited to the new text with the button. If that already reaches `votes_needed`,
or a reactor is an admin, the vote passes during the conversion. The existing reaction-reading code is kept
only for this. How a converted vote is recognised (a stored marker, or the message already having the
button) is up to the builder. It must not convert a vote twice or lose voters on a second start.

### What goes away

- `on_raw_reaction_add` and counting votes from reactions (apart from the one-off conversion).
- `character_vote.emoji` keeps its meaning as the vote's emoji, now shown on the button. The default ⭐ stays.
  **(my call)**

### The voting cog

The vote handling moves out of `bot.py` into a `CharacterVoteCog`. That cog holds:

- the persistent button view
- the `on_raw_message_delete` listener
- the startup check of the open votes, and the conversion

The logic stays in `character_vote_service` and its repository. `/addcharacter` stays in `CharacterCog`.
`~addcharacter` still goes through the legacy handler, and both call `start_vote`.

The character votes spec, README (the voting paragraph and the permissions: "Add Reactions" is no longer
needed), and the manual test plan are updated to the button.

## Cooldowns

One `Cooldowns` on the client serves both syntaxes. The key becomes the command name without prefix
(`artping`), so a cooldown started with `~artping` also holds back `/artping`, and the other way around.
The cooldown time comes from the same setting. Admins are exempt, and only a successful command starts the
cooldown. The legacy message keeps saying `You used ~artping recently...`. The slash message says
`/artping` and is ephemeral. **(my call)**

## Command sync

- A new setting `discord.guild_id` (default empty in `config.example.ini`, a `Settings` field, parsed in
  `load_settings`), for development only. **(my call)**
  - When set, `setup_hook` copies the global commands to that server and syncs there, which takes effect
    immediately. It also syncs an empty global set, so the commands don't show up twice. A developer's bot is
    their own application (README, local setup), so this never touches production.
  - When empty, as in production, it syncs globally, which also makes the slash commands available in DMs.
    Commands left over from a guild sync on that application aren't cleared automatically. The README says
    how to clear them: start once with `guild_id` set and an empty tree, or leave them. It's a one-off for
    developers.
- The sync runs on every start. A failed sync is logged and the bot keeps running with the `~` commands.
- The bot has to be invited with the `applications.commands` scope. The README's local setup and deployment
  notes say so. The production bot may need to be re-invited once.

## Documentation

- README: a short section on slash commands (same names, `/resource` for posting resources, spaces in
  names become underscores, `/artping` takes up to `art_ping.slash_max_characters` characters, `/lorenz`
  and `/chromk`) and the new setting and invite scope.
- `CLAUDE.md`: the new `legacy/` and `slash/` packages, the typed service functions, the new handler
  signature rule ("services take typed arguments; legacy handlers parse messages; cogs read options"),
  adding a command = service function + legacy handler and `Command` entry + slash command.
- A spec for the slash side in `docs/superpowers/specs/` describing it as built, and the command handling
  spec updated for the legacy move. `docs/manual-test-plan.md` gets slash cases.

## Testing

- The legacy tests prove the `~` side is unchanged. Moving them must not change their assertions.
- A parity test: every legacy `Command` has a slash command of the same name, apart from `~help`, and the
  other way around, except `/resource`, `/lorenz` and `/chromk`.
- `/artping` gets as many options as `art_ping.slash_max_characters` says (tested with at least two
  values), and an out-of-range setting is refused.
- Slash adapters are tested through a fake interaction in `tests/fakes.py` (response, follow-ups,
  `original_response`, `user`, `guild`, `channel`), covering at least option passing, ephemeral errors,
  admin refusal, reply splitting, the shared cooldown and starting a vote.
- Votes:
  - The existing vote tests are rewritten for the button: clicking to vote and to take a vote back, the count
    on the label, an admin's click, passing at `votes_needed`, a taken name, deleted messages, restarts.
  - New tests cover converting a ⭐ vote, including one that passes during conversion and one that is
    converted only once over two starts.
  - Migration `007` is tested like the others.
- Autocomplete callbacks are tested for prefix matching and the 25-choice limit.

## Left to the builder

- The exact module and class names in `legacy/` and `slash/`, and how the service functions are named where
  the legacy handler keeps the old name.
- How to make the deferring commands fit the 3-second rule.
- Autocomplete matching details (prefix vs contains, case-insensitive, at most 25 choices).
- Whether `Settings` grows a helper for the sync target.
- The order of the work. Doing the service split first, with the legacy tests green, before anything slash
  is the obvious one.
