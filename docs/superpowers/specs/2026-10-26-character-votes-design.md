# Character votes: design

Votes were first cast by reacting with an emoji and are now cast with a **Vote button** (see "The vote button"
at the end; the slash commands design has the details). The sections below describe the original design;
where the button changed something it is marked, and the end section wins.

## Intent

Today only admins can add characters (`~addcharacter`). Non-admins should be able to propose a character
themselves, with the community deciding: the bot posts a vote message, users vote on it (first by reacting with
a configured emoji, now with a button), and once enough users have voted the character is added and everyone who voted is subscribed to its art
pings. Admins keep adding characters directly.

## Goals

- `~addcharacter` works for non-admins and starts a vote instead of adding the character.
- The number of votes needed and the vote emoji are configurable.
- When a vote reaches the number, the character is added and the users who reacted to *that* message are
  subscribed to it (as if each had used `~addping`).
- Open votes are stored in the database and survive bot restarts.

## Non-goals

- Votes don't expire. An open vote stays open until it passes or is dropped.
- No voting for removing characters, aliases or currencies.
- No command to list or cancel open votes.

## Anti-goals

- A vote must never add a character twice or fail halfway: either the character is added together with all
  its voters' subscriptions, or nothing changes.
- A user who isn't on the vote message (or only reacted with another emoji) must never get subscribed.
- The bot's own reaction never counts as a vote.

## Behavior (decided with the user)

- **Admins:** `~addcharacter` adds the character right away, as it does now.
- **Non-admins:** `~addcharacter Black_Knight` runs the same checks as now (missing argument, more than one
  name, the name already being a character or an alias); on failure they get the same reply and no vote is
  started. Otherwise the bot posts a vote message.
- Several votes for the same name may be open at once. The first to reach the number adds the character, and
  only the users who reacted to that message are subscribed.
- When a character gets added, by a vote passing or by an admin, every other open vote for that name is
  dropped.
- Votes are stored in the database (migration `005`).
- With `votes_needed` below 2 there are no votes: `~addcharacter` adds the character directly for everyone.
- A reaction of an admin with the vote emoji passes the vote right away; the admin is subscribed like any voter.
  Reactions list uncached members as plain users without permissions, so while a vote is short the reactors
  are looked up with `guild.fetch_member` (fewer requests than the votes needed); one who left the server
  still counts as a vote, not as an admin.

## Behavior (my calls, the user can override)

- **Vote message:** e.g. `Vote to add Black_Knight: react with ⭐. Votes needed: 5` The bot adds the
  emoji to the message itself so people can just click it (the button replaced both, see the end). The name in it is normalized
  (`name_util.normalize_name`), as everywhere else.
- **Counting (reaction votes; now only read for the conversion):** reactions are not stored. On each reaction add/remove on a vote message, the bot fetches the
  message from Discord and counts the users who reacted with the vote emoji, excluding bots. Reactions with
  other emoji are ignored. Removing a reaction therefore takes the vote back; there is nothing to do on
  removal other than not counting it, so only reaction *adds* need to trigger a check.
- **Events:** the client uses `on_raw_reaction_add` (and `on_raw_message_delete`), which fire for messages
  not in the cache, i.e. vote messages posted before a restart. `Intents.default()` already includes
  reactions; no change in the Discord developer portal is needed.
- **Startup:** in `on_ready`, every open vote is checked once, so a vote that reached the number while the bot
  was offline passes then. `on_ready` can fire again after a reconnect; the check is idempotent.
- **Passing:** the character is added and its voters subscribed in one transaction, the vote row and every
  other open vote for that name are deleted in it too. The vote message is edited to
  `Character Black_Knight has been added` (without listing the voters as mentions, so they aren't
  pinged) and the other votes' messages are edited to `Character Black_Knight has already been added`.
- **Dropped by an admin add:** the open votes for that name are deleted and their messages edited to
  `Character Black_Knight has already been added`.
- **Deleted vote message:** its vote row is deleted. A vote message that can't be found when checked
  (`discord.NotFound`) is dropped the same way.
- **Name taken by an alias:** an admin can take a voted name without adding a character (`~addalias`,
  `~setprimaryname`). No hooks are added there; instead a vote is dropped lazily whenever it is checked (a
  reaction, or startup) and its name fails `character_service.require_unused_name`. Its message is edited to
  that error's text (e.g. `Black_Knight is already an alias of Black_Knight_Zelgius`).
- **Missing permissions:** voting needed the bot to have Add Reactions and Read Message History in the channel;
  with the button only Read Message History is left, for the conversion and for fetching vote messages.
  A `discord.Forbidden` while reacting to the new vote message, or while fetching it to count, is logged as a
  warning and the vote is kept, so it works once the permissions are fixed (the startup check picks it up).
  `README.md` mentions the two permissions.
- **The proposer** counts only if they react, like everyone else.
- **DMs:** a non-admin `~addcharacter` in a DM is turned down with a `CommandError` ("Votes can only be
  started in a server"), because votes belong in a shared channel.
- **Cooldown:** none; there is none for other commands either except `~artping`.
- **`~help`:** `~addcharacter` moves out of the admin section into the art ping section, with a description
  like "Add a character that users can be pinged for; for non-admins this starts a vote". `README.md` is
  updated to match.

## The vote button

Votes are cast with a **Vote button** on the vote message, for `~addcharacter` and `/addcharacter` alike.

- The vote message reads `Vote to add Black_Knight. Votes needed: 5`, the button `Vote (0/5)` with
  `character_vote.emoji` as its emoji. The label is edited to the new count after each click.
- A click from a user who hasn't voted adds their vote, a second click takes it back. The clicker gets an
  ephemeral confirmation (`Your vote for Black_Knight has been added` / `... has been taken back`): the button
  defers ephemerally first ("thinking"), since passing a vote edits every vote message for the name, and then
  sends the confirmation as a follow-up.
- A click from an admin passes the vote at once, and the admin is subscribed like any voter. Bots can't click.
- At `votes_needed` the message becomes `Character Black_Knight has been added` and loses its button; the other
  votes for the name are edited to `... has already been added` and lose theirs. A click on a vote whose name
  got taken (an alias) drops it, as checking it does.
- The voters are stored (migration `007`, table `CHARACTER_VOTE_VOTER`: message ID and user ID, cascading with
  the vote), since a button keeps no list of who clicked. `CHARACTER_VOTE.USES_BUTTON` is `1` for votes counted
  by their stored voters and `0` for the votes that were open when the button came.
- The button is a persistent view (fixed `custom_id`, no timeout), registered with `bot.add_view` by
  `CharacterVoteCog`, so it works on vote messages from before a restart. The vote is found by the clicked
  message's ID. Clicks made while the bot is offline fail on the user's side and can be repeated.
- **Conversion:** at startup (`check_open_votes`) each vote with `USES_BUTTON = 0` is converted once: the users
  (bots excluded) who reacted with `character_vote.emoji` become stored voters, `USES_BUTTON` is set, and the
  message gets the new text and the button. If that reaches `votes_needed`, or a reactor is an admin, the vote
  passes during the conversion. A converted vote isn't converted again. This is the only place reactions are
  still read; `on_raw_reaction_add` is gone, `on_raw_message_delete` stays.
- **Re-rendering:** the startup check also compares each vote with `votes_needed`, and re-renders the message of
  every vote that stays open with the current text and count. Open votes follow a `votes_needed` changed while
  the bot was offline, and a converted vote whose edit failed gets its button on the next start.

## Configuration

New section in `config.example.ini`, following the existing pattern (default, `Settings` field, parsing in
`load_settings`):

```ini
[character_vote]
# Number of users who have to react to a vote message before the character is added
votes_needed=5
# Emoji users react with to vote; a Unicode emoji or a custom one as <:name:id>
emoji=⭐
```

Defaults are my call. The emoji is compared as text with `str(payload.emoji)` / `str(reaction.emoji)`, which
gives the Unicode character or `<:name:id>` for a custom emoji. The config files are read with UTF-8 (check
`config.read` passes `encoding='utf-8'`; it doesn't today).

## Database

`db/migrations/005_character_votes.sql`:

```sql
CREATE TABLE CHARACTER_VOTE (
    MESSAGE_ID TEXT NOT NULL PRIMARY KEY,
    CHANNEL_ID TEXT NOT NULL,
    CHARACTER_NAME TEXT NOT NULL COLLATE NOCASE,
    PROPOSER TEXT NOT NULL
);
CREATE INDEX CHARACTER_VOTE_NAME ON CHARACTER_VOTE (CHARACTER_NAME);
```

IDs as text, like `PINGS.USER`. Not unique on the name, since several votes for one name may be open.
`CHARACTER_NAME` isn't a foreign key: the character doesn't exist yet.

## Fitting the architecture

- **model:** `model/character_vote.CharacterVote` (frozen dataclass: `message_id`, `channel_id`,
  `character_name`, `proposer`).
- **repository:** `repository/character_vote_repository.py`: add a vote, get one by message ID, get all,
  delete one, delete (and return) all for a name; plus the pass operation as one transaction (add character,
  add pings, delete the votes for the name) returning the deleted other votes so their messages can be edited.
  Placing the pass transaction in the repository mirrors `alias_repository.set_primary_name`.
- **service:** `service/character_vote_service.py` holds starting a vote and checking one (count, pass or
  wait, drop when the message is gone). `character_service.add_character` branches on
  `user_util.is_administrator(message.author)`: admins add directly and drop open votes; non-admins start a
  vote.
- **commands:** `~addcharacter` loses `admin_only=True` and moves to the art ping section.
- **bot:** `ArtPingClient` got `on_raw_reaction_add`, `on_raw_message_delete`, and the open-vote check in
  `on_ready`; they now live in `CharacterVoteCog` (without the reaction listener). Errors in these handlers are logged, never raised (there is no user to reply to).

### Handler reply

A handler returns the reply string, which `on_message` sends. Starting a vote needs the sent `Message` (to
store its ID and react to it), so the vote handler sends the vote message itself. It then needs to return
"nothing to send": `on_message` should send nothing for an empty reply (`split_message("")` already returns
`[]`, so returning `""` works today; make that explicit with a comment or a test). This is the builder's call
if a cleaner shape fits.

### Concurrency

Between fetching reactions and passing, other events can run (awaits). After the fetch, re-read the vote row
and only pass if it still exists and the character still doesn't; the database work after that is
synchronous, so no other handler can interleave.

## Tests

- Service tests against the in-memory database: starting a vote (row stored, bot reaction added, checks
  rejected the same as today), counting (other emoji and bots ignored), passing (character added, exactly the
  voters of that message subscribed, other votes for the name dropped and edited), admin add drops open votes,
  deleted/missing message drops the vote, startup check passes a vote that is already over the number,
  passing twice is harmless.
- `test_bot.py`: non-admin `~addcharacter` now posts a vote rather than being ignored (replaces
  `test_admin_command_ignored_for_non_admin` for this command; keep that test with another admin command).
- `test_config.py`: the new settings.
- `test_database.py`: migration `005` applies.
- `tests/fakes.py` needs fakes for a sent message (ID, `add_reaction`, `edit`), its reactions (`emoji`,
  async `users()`), a channel that returns the sent message and can `fetch_message`, and a client with
  `get_channel`/`fetch_channel` and `user`.

## Left to the builder

- Exact message wording.
- Names of functions and the split between service and repository beyond what is above.
- Whether the "nothing to send" reply is `""` or a small explicit change in `on_message`.
- Update `CLAUDE.md` (architecture and schema sections) and `README.md`.
