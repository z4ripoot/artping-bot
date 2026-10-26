# Slash Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add slash commands next to the unchanged `~` commands, sharing typed service functions, and switch character votes from ⭐ reactions to a persistent Vote button.

**Architecture:** Services get typed arguments. The `~` path moves to a `legacy/` package whose handlers only parse message words. A new `slash/` package holds one `commands.Cog` per feature, as thin adapters run through one shared runner. `ArtPingClient` becomes a `commands.Bot` that keeps its own `on_message`. Votes store their voters (migration `007`) and are driven by a persistent `discord.ui.View`.

**Tech Stack:** Python ≥ 3.10, discord.py 2.7.1 (`discord.ext.commands`, `discord.app_commands`, `discord.ui`), SQLite, pytest 9.

**Spec:** `docs/superpowers/specs/2026-10-26-slash-commands-design.md`. Read it with this plan, together with `CLAUDE.md`.

## Global Constraints

- discord.py stays pinned at `2.7.1`; no new dependencies.
- `~` users see no change. The only exceptions are the new `~help` line `All commands are also available as slash commands, type /` and the vote button.
- **Legacy test assertions don't change** when tests move. Only imports and helpers may change, except the vote tests, which Task 7 rewrites.
- Every service check and message lives in the service. Cogs only read options, call the service and reply.
- Replies never mention `@everyone`, `@here` or roles. Resource posts mention nobody.
- A failed command sync is logged, and the bot keeps running.
- **Settings:** every new setting gets a default in `config.example.ini`, a `Settings` field and parsing in `load_settings`.
- **Migrations:** never edit a released migration; schema changes go in `007`.
- **Package layout:** `fjormcord/` and `fjormcord/bot/` keep having no `__init__.py`. New test directories get an `__init__.py` only where they hold Python files.
- **Commit messages:** plain imperative sentences, as in `git log`, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Commands:**
  - Run all tests: `.venv/Scripts/python -m pytest`.
  - Run a single test: `.venv/Scripts/python -m pytest <path>::<name> -v`.

## Review Focus

1. **A click on a vote that is already closed:** it was passed elsewhere, or an admin added the character directly. Expect an ephemeral `This vote has already been closed`, the button removed from that message, and no traceback. The test is in Task 7.
2. **A slash name that is only whitespace (`"   "`):** expect an ephemeral `A name can't be empty`, never a lookup of `""`. The test is in Task 8.
3. **A slash reply over 2000 characters** (`/checkcharacter` with many users, a long `/resource`): expect the response plus follow-ups, each within the limit. The test is in Task 8.
4. **The same character twice in `/artping`, or a name and its alias:** expect it to be pinged once, as `~artping` does. The test is in Task 9.
5. **The sync is rejected** (`discord.Forbidden` when the bot was invited without `applications.commands`): expect it to be logged, and the `~` commands still work. The test is in Task 8.

---

## File structure

```
src/fjormcord/bot/artping/
  bot.py                       ArtPingClient(commands.Bot): on_message -> legacy.dispatch, setup_hook adds cogs + syncs
  config.py                    + guild_id, art_ping_slash_max_characters
  vote_view.py                 VoteView: the persistent Vote button (shared by both syntaxes)
  legacy/__init__.py
  legacy/commands.py           moved from commands.py (+ help line)
  legacy/dispatch.py           command lookup, admin silence, cooldown, error -> reply, resource fallback
  legacy/art_ping_handlers.py  legacy/character_handlers.py  legacy/alias_handlers.py
  legacy/currency_handlers.py  legacy/resource_handlers.py
  slash/__init__.py
  slash/runner.py              run(): admin check, cooldown, defer, errors, splitting
  slash/options.py             to_name(), autocomplete callbacks
  slash/sync.py                sync_commands()
  slash/art_ping_cog.py  slash/character_cog.py  slash/currency_cog.py
  slash/resource_cog.py  slash/easter_egg_cog.py  slash/character_vote_cog.py
  model/character_vote.py      + VoteChannel, CharacterVote.uses_button
  service/*.py                 typed signatures
db/migrations/007_character_vote_voters.sql
tests/fjormcord/bot/artping/legacy/   tests/fjormcord/bot/artping/slash/
```

---

### Task 1: New settings

**Files:**
- Modify: `config.example.ini`, `src/fjormcord/bot/artping/config.py`
- Test: `tests/fjormcord/bot/artping/test_config.py`, `tests/fjormcord/bot/artping/test_main.py` (its `Settings(...)` gets the new fields)

**Interfaces:**
- Produces: `Settings.guild_id: int | None`, `Settings.art_ping_slash_max_characters: int`, `config.MAX_SLASH_OPTIONS = 25`

- [ ] **Step 1: Write the failing tests.** Extend `test_defaults_come_from_the_example` with `settings.guild_id is None` and `settings.art_ping_slash_max_characters == 10`. Extend `test_config_ini_overrides_the_example`: `[discord] guild_id=456` gives `456`, and `[art_ping] slash_max_characters=3` gives `3`. Add:

```python
@pytest.mark.parametrize("value", ["0", "26"])
def test_slash_max_characters_must_fit_discord_limit(directory, value):
    (directory / "config.ini").write_text(f"[art_ping]\nslash_max_characters={value}\n")
    with pytest.raises(ValueError, match="art_ping.slash_max_characters must be between 1 and 25"):
        load_settings(directory)
```

- [ ] **Step 2:** Run `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/test_config.py -v`. Expected: FAIL (`AttributeError` / no `ValueError`).
- [ ] **Step 3: Implement the settings.**
  - `config.example.ini`:
    - `[discord] guild_id=`, with a comment: for development, syncs the slash commands to this server only, instantly; empty in production.
    - `[art_ping] slash_max_characters=10`, with a comment: how many characters `/artping` takes, 1–25, applied on restart.
  - Add both `Settings` fields; `guild_id` is parsed like `coliseum_channel_id`.
  - Raise `ValueError` with the message above when the value is outside 1–25.
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Add settings for the slash command server and the /artping limit".

---

### Task 2: Legacy package and the Bot client

A pure move plus the client switch. `~` behaviour stays the same, apart from the `~help` line.

**Files:**
- Create: `src/fjormcord/bot/artping/legacy/__init__.py` (empty), `legacy/commands.py` (moved with `git mv` from `commands.py`), `legacy/dispatch.py`
- Modify: `bot.py`, `util/message_util.py` (gets `ALLOWED_MENTIONS`), `service/resource_service.py` (`_require_not_a_command` imports `legacy.commands`)
- Test: move `tests/.../test_commands.py` to `tests/fjormcord/bot/artping/legacy/test_commands.py` (create `legacy/__init__.py` there); `test_bot.py` stays and gets updated imports.

**Interfaces:**
- Produces:
  - `message_util.ALLOWED_MENTIONS` (moved from `bot.py`, same value).
  - `legacy.dispatch.handle_message(client: ArtPingClient, message: discord.Message) -> Awaitable[None]`: the body of today's `on_message`, `get_message`, `send_resource` and the cooldown helpers.
  - `legacy.commands.cooldown_key(command: Command) -> str`: returns `command.name.removeprefix(COMMAND_PREFIX)`, e.g. `"artping"`. The `Cooldowns` keys use it, so Task 9 can share them.
  - `ArtPingClient(commands.Bot)`:
    - `__init__(**options)` defaults `command_prefix` to `commands.when_mentioned` (unused), `help_command=None` and `allowed_mentions`, and keeps `self.cooldowns`.
    - `on_message` awaits `legacy.dispatch.handle_message(self, message)` and never calls `process_commands`.

- [ ] **Step 1: Write the failing tests.**
  - In `legacy/test_commands.py`, add `test_help_mentions_slash_commands`: asserts `"All commands are also available as slash commands, type /"` is in `show_help(None, make_message("~help"))`, on the line after the multi-word hint.
  - In `test_bot.py`, add `test_client_is_a_bot_without_prefix_commands`: `isinstance(bot, commands.Bot)` and `bot.help_command is None`.
- [ ] **Step 2:** Run `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping -v`. Expected: the 2 new tests FAIL, after fixing the imports.
- [ ] **Step 3: Implement.**
  - Move the code as listed.
  - Replace the TODO comment in `legacy/commands.py` with `# The ~ commands; slash commands are in fjormcord.bot.artping.slash (docs/superpowers/specs/2026-10-26-slash-commands-design.md)`.
  - Add the help line.
  - `__main__.py` is unchanged: `ArtPingClient(intents=intents)` still works.
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS, and no existing assertion was edited.
- [ ] **Step 5:** Commit: "Move the ~ commands into a legacy package and make the client a commands.Bot".

---

### Task 3: Typed services for art pings, characters and aliases

**Files:**
- Create: `legacy/art_ping_handlers.py`, `legacy/character_handlers.py`, `legacy/alias_handlers.py`
- Modify: `service/art_ping_service.py`, `service/character_service.py`, `service/alias_service.py`, `service/character_vote_service.py` (`start_vote` only), `model/character_vote.py`, `legacy/commands.py` (points at the handlers), `tests/fakes.py` (`FakeChannel.send` accepts `view=None` and ignores it until Task 7)
- Test: move `tests/.../service/test_art_ping_service.py`, `test_character_service.py` and `test_alias_service.py` to `tests/fjormcord/bot/artping/legacy/test_<feature>_handlers.py`, importing the handlers. Add `tests/.../service/test_typed_services.py` for the new signatures.

**Interfaces:**
- Produces, in `model/character_vote.py`:

```python
@dataclass(frozen=True)
class VoteChannel:
    # Where a vote message goes: legacy sends to the message's channel, slash as the interaction's follow-up
    channel_id: str
    in_guild: bool
    # send(content, view) -> the sent message, whose ID the vote is stored by
    send: Callable[[str, Any], Awaitable[Any]]
```

- Produces these services. Each normalizes names itself with `normalize_name`, as today's handlers do, and raises `CommandError` with today's texts.
  - `art_ping_service.do_art_ping(names: list[str]) -> str`
  - `art_ping_service.add_ping(user_id: str, name: str) -> str`
  - `art_ping_service.remove_ping(user_id: str, name: str) -> str`
  - `art_ping_service.check_ping(user_id: str) -> str`
  - `character_service.add_character(client, user: discord.abc.User, name: str, vote_channel: VoteChannel) -> Awaitable[str]`
  - `character_service.remove_character(name: str) -> str`
  - `character_service.check_character(client, name: str) -> Awaitable[str]`
  - `alias_service.add_alias(name: str, alias: str) -> str`
  - `alias_service.remove_alias(name: str, alias: str) -> str`
  - `alias_service.set_primary_name(alias: str) -> str`
  - `character_vote_service.start_vote(vote_channel: VoteChannel, proposer_id: str, name: str) -> Awaitable[str]`
    - With `in_guild` False it raises `Votes can only be started in a server`.
    - Otherwise it sends with `view=None` for now (Task 7 adds the button) and keeps today's text and ⭐ reaction.
- Produces legacy handlers with the old names and the `(client, message)` signature, in the matching `legacy/*_handlers.py`.
  - They only parse: `get_single_name`, `get_entries`, `MissingArgument`, `MESSAGE_ONE_NAME_ONLY`.
  - `~addcharacter` builds `VoteChannel(str(message.channel.id), message.guild is not None, lambda content, view: message.channel.send(content, view=view))`.

- [ ] **Step 1: Write the failing tests** in `test_typed_services.py`:
  - `test_add_ping_takes_user_and_name`: after `add_character` of Lucina, `add_ping("5", "lucina") == "Ping for Lucina has been added"`.
  - `test_do_art_ping_takes_names`: `do_art_ping(["Lucina", "Nobody"])` starts with `"No character entry for Nobody"`.
  - `test_add_alias_normalizes`: `add_alias("lucina", "marth_mask") == "Alias Marth_Mask has been added to Lucina"`.
  - `test_start_vote_refuses_outside_a_server`: a `VoteChannel` with `in_guild=False` raises `CommandError("Votes can only be started in a server")`.
- [ ] **Step 2:** Run the new file. Expected: FAIL (`TypeError`: wrong arguments).
- [ ] **Step 3: Implement** the signatures above. Move only the parsing into the handlers, and keep the order of checks the same.
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS. The moved tests' assertions are unchanged, and `test_character_vote_service.py` still passes with the ⭐ flow.
- [ ] **Step 5:** Commit: "Give the art ping, character and alias services typed arguments".

---

### Task 4: Typed currency service

**Files:**
- Create: `legacy/currency_handlers.py`
- Modify: `service/currency_service.py`, `legacy/commands.py`
- Test: move `tests/.../service/test_currency_service.py` to `tests/.../legacy/test_currency_handlers.py`, and add cases to `tests/.../service/test_typed_services.py`.

**Interfaces:**
- Produces:
  - `add_currency(name: str) -> str`
  - `remove_currency(name: str) -> str`
  - `set_currency(user_id: str, name: str, amount: int) -> str`
    - It checks negative, then too large, then `require_currency`, in today's order.
    - `Please enter a valid amount for your {entry}` stays in the legacy handler.
  - `clear_currency(user_id: str, name: str) -> str`
  - `check_wallet(user_id: str, display_name: str, slash: bool = False) -> str`
  - `get_scoreboard(client, name: str, page: int = 1, slash: bool = False) -> Awaitable[str]`
  - With `slash=True`:
    - the empty wallet reads `Your wallet is empty. Use /setcurrency to add a currency`
    - the next-page hint reads `Use /scoreboard currency:{name} page:{page + 1} for the next page`

- [ ] **Step 1: Write the failing tests**:
  - `test_check_wallet_names_the_slash_command`: `check_wallet("5", "user5", slash=True) == "Your wallet is empty. Use /setcurrency to add a currency"`.
  - `test_scoreboard_hint_uses_slash_syntax`: 11 users set Orbs; `get_scoreboard(client, "Orbs", slash=True)` ends with `"Use /scoreboard currency:Orbs page:2 for the next page"`.
  - `test_set_currency_takes_an_int`: `set_currency("5", "Orbs", 3) == "Your Orbs has been set to 3"`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3: Implement.** The legacy handler parses the page (`int`, or `MESSAGE_ONE_NAME_ONLY`) and the amount, then calls the service.
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Give the currency service typed arguments".

---

### Task 5: Typed resource service

**Files:**
- Create: `legacy/resource_handlers.py`
- Modify: `service/resource_service.py`, `legacy/commands.py`, `legacy/dispatch.py` (still uses `get_resource_content`)
- Test: move `tests/.../service/test_resource_service.py` to `tests/.../legacy/test_resource_handlers.py`, and add cases to `test_typed_services.py`.

**Interfaces:**
- Produces:
  - `set_resource(client, name: str, link: str) -> Awaitable[str]`: name parsing (`~` prefix, allowed characters), the command-name refusal and link unwrapping (`<link>`) all stay in the service.
  - `remove_resource(name: str) -> str`
  - `list_resources(slash: bool = False) -> str`: with `slash=True` it returns `Resources: hof, faq (post one with /resource)`.
  - `post_resource(name: str) -> str`: returns the content, or raises `CommandError(f"Resource {name} doesn't exist")`.
  - `get_resource_content(name) -> str | None`: unchanged.

- [ ] **Step 1: Write the failing tests**:
  - `test_list_resources_in_slash_syntax`: the hint text above.
  - `test_post_resource_refuses_unknown`: `CommandError` with `Resource hof doesn't exist`.
  - `test_set_resource_takes_name_and_link`: `set_resource(client, "hof", "https://example.com/hof")` returns `Resource hof has been set`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Give the resource service typed arguments".

---

### Task 6: Vote voter storage (migration 007)

**Files:**
- Create: `db/migrations/007_character_vote_voters.sql`
- Modify: `repository/character_vote_repository.py`, `model/character_vote.py`
- Test: `tests/fjormcord/bot/artping/test_database.py`, plus a repository-level block in `tests/.../service/test_character_vote_service.py`

**Interfaces:**
- Migration:
  - `CREATE TABLE CHARACTER_VOTE_VOTER (MESSAGE_ID TEXT NOT NULL REFERENCES CHARACTER_VOTE (MESSAGE_ID) ON DELETE CASCADE, USER TEXT NOT NULL, PRIMARY KEY (MESSAGE_ID, USER));`
  - `ALTER TABLE CHARACTER_VOTE ADD COLUMN USES_BUTTON INTEGER NOT NULL DEFAULT 0;`
  - A header comment that voters are now stored and `USES_BUTTON` marks votes converted from reactions.
- `CharacterVote` gets `uses_button: bool = True` as its last field. `_SELECT_VOTE` adds `V.USES_BUTTON AS uses_button`, and `add_vote` inserts it.
- Produces:
  - `add_voter(message_id: str, user_id: str)`
  - `remove_voter(message_id: str, user_id: str)`
  - `has_voter(message_id: str, user_id: str) -> bool`
  - `count_voters(message_id: str) -> int`
  - `convert_vote(message_id: str, user_ids: Iterable[str])`: stores the voters and sets `USES_BUTTON = 1` in one transaction.
  - `pass_vote(message_id: str, character_name: str)`: replaces `pass_vote(character_name, user_ids)`. It subscribes `SELECT USER FROM CHARACTER_VOTE_VOTER WHERE MESSAGE_ID = ?` in the same transaction as today.

- [ ] **Step 1: Write the failing tests**:
  - `test_existing_votes_are_marked_as_reaction_votes` (in `test_database.py`): a database at version 6 with one vote, migrated to 7, gives `uses_button == 0` and no voters.
  - `test_removing_a_vote_removes_its_voters`: `add_voter` then `remove_vote` gives `count_voters == 0`.
  - `test_pass_vote_subscribes_the_stored_voters`: after voters "1" and "2", `pass_vote` makes the subscribers `{"1", "2"}`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3: Implement.** Update the existing `check_vote` call to the new `pass_vote` by storing the reactors with `add_voter` first, so the ⭐ tests keep passing until Task 7.
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Store the voters of character votes".

---

### Task 7: Vote button, conversion and CharacterVoteCog

**Files:**
- Create: `src/fjormcord/bot/artping/vote_view.py`, `slash/__init__.py` (empty), `slash/character_vote_cog.py`
- Modify: `service/character_vote_service.py`, `bot.py` (drop `on_raw_reaction_add`, `on_raw_message_delete` and the vote check in `on_ready`), `tests/fakes.py`
- Test: rewrite `tests/.../service/test_character_vote_service.py`, and create `tests/fjormcord/bot/artping/slash/__init__.py` and `slash/test_character_vote_cog.py`

**Interfaces:**
- Produces `vote_view.py`:
  - `VOTE_BUTTON_ID = "character_vote"`.
  - `class VoteView(discord.ui.View)`, `__init__(self, count: int = 0)`, `timeout=None`.
    - One button: `custom_id=VOTE_BUTTON_ID`, `label=f"Vote ({count}/{votes_needed})"`, `emoji=settings.character_vote_emoji`, primary style.
    - The callback runs `reply = await character_vote_service.toggle_vote(interaction.client, interaction.message, interaction.user)` and answers `interaction.response.send_message(reply, ephemeral=True)`.
    - Import `character_vote_service` as a module, since it imports this one.
- Produces `character_vote_service`:
  - `start_vote` sends `f"Vote to add {name}. Votes needed: {needed}"` with `VoteView(0)` and stores the vote with `uses_button=True`. It no longer adds a reaction.
  - `toggle_vote(client, message, user) -> Awaitable[str]` returns the ephemeral text:
    - no stored vote: `This vote has already been closed`, and edits the message with `view=None`.
    - name taken: the vote is dropped, the message is edited to the error with `view=None`, and the error text is returned.
    - admin: `add_voter` if missing, then the vote passes.
    - already voted: `remove_voter`, returns `Your vote for {name} has been taken back`.
    - otherwise: `add_voter`, returns `Your vote for {name} has been added`. The vote passes when `count_voters >= votes_needed`.
    - Passing edits the message to `Character {name} has been added` with `view=None`, and closes the other votes (today's `_close`, which now also passes `view=None`).
    - Not passing edits `view=VoteView(count)`.
  - `check_open_votes(client)`, run at startup, handles each vote:
    - It fetches the message: `NotFound` drops the vote; `Forbidden` keeps it.
    - When `not vote.uses_button`, it converts the vote: reactors (bots excluded) with `character_vote_emoji` go to `convert_vote`. If one of them is an admin (today's `_has_administrator`), the vote passes. Otherwise the message is edited to the new text with `VoteView(count)`.
    - A taken name drops the vote.
    - `count >= votes_needed` passes it.
  - `drop_deleted_vote` is unchanged.
  - `check_vote` and the reaction listener are gone.
- Produces `CharacterVoteCog(commands.Cog)`:
  - `cog_load` calls `self.bot.add_view(VoteView())`.
  - `@commands.Cog.listener() on_ready` awaits `check_open_votes`, with the exception logged.
  - `@commands.Cog.listener() on_raw_message_delete` calls `drop_deleted_vote`, with the exception logged.
- `tests/fakes.py`:
  - `FakeChannel.send(content, allowed_mentions=None, view=None)` and `FakeSentMessage.edit(content=_UNCHANGED, view=_UNCHANGED)` record the `view`, so `message.view` is readable.
  - New `click(client, message, user_id, administrator=False) -> str` runs `toggle_vote` with `make_member`.

- [ ] **Step 1: Rewrite the vote tests for the button.** Keep every scenario of today's file that still applies, and add:
  - `test_non_admin_add_character_starts_a_vote`: `channel.sent == ["Vote to add Black_Knight. Votes needed: 2"]`, the button label is `Vote (0/2)`, and there are no reactions.
  - `test_click_adds_a_vote_and_updates_the_count`: the reply is `Your vote for Black_Knight has been added`, and the label is `Vote (1/2)`.
  - `test_second_click_takes_the_vote_back`: the reply is `Your vote for Black_Knight has been taken back`, and the label is `Vote (0/2)`.
  - `test_vote_passes_and_subscribes_the_voters`: clicks by 1 and 2 add the character, the subscribers are `{"1", "2"}`, the message is `Character Black_Knight has been added`, and `view is None`.
  - `test_admin_click_passes_the_vote`: subscribers `{"9"}`.
  - `test_click_on_a_closed_vote` (Review Focus 1): after an admin `~addcharacter`, a click on the old vote returns `This vote has already been closed`, and `view is None`.
  - `test_reaction_vote_is_converted_at_startup`: a vote stored with `uses_button=False` and ⭐ reactions from 1, plus the bot, gets `count_voters == 1`, text `Vote to add Black_Knight. Votes needed: 2` and label `Vote (1/2)`.
  - `test_reaction_vote_passes_during_conversion`: reactions from 1 and 2.
  - `test_reaction_vote_with_admin_passes_during_conversion`.
  - `test_conversion_happens_once`: run `check_open_votes` twice; voters unchanged, and the click count still works.
  - In `test_character_vote_cog.py`:
    - `test_vote_view_is_persistent`: `VoteView().is_persistent()` is true.
    - `test_cog_registers_the_view`: a fake bot records `add_view`.
- [ ] **Step 2:** Run the vote tests. Expected: FAIL.
- [ ] **Step 3: Implement.** In `bot.py`, `setup_hook` adds `CharacterVoteCog(self)`. `on_ready` keeps only the Coliseum start.
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Vote on characters with a button instead of reactions".

---

### Task 8: Slash runner, options and sync

**Files:**
- Create: `slash/runner.py`, `slash/options.py`, `slash/sync.py`
- Modify: `bot.py` (`setup_hook` ends with `await sync_commands(self.tree, config.read_settings().guild_id)`), `tests/fakes.py`, `repository/character_repository.py` and `repository/currency_repository.py` (name lists)
- Test: `tests/fjormcord/bot/artping/slash/test_runner.py`, `test_options.py`, `test_sync.py`

**Interfaces:**
- Produces `slash/runner.py`:

```python
async def run(interaction: discord.Interaction, command_name: str, call: Callable[[], str | Awaitable[str]], *,
              admin_only: bool = False, cooldown_seconds: float = 0, defer: bool = False,
              allowed_mentions: discord.AllowedMentions = ALLOWED_MENTIONS) -> None
```

  The steps, in order:
  1. Admin check: a non-admin (`is_administrator(interaction.user)`) gets an ephemeral `This command is for admins only`.
  2. Cooldown on `interaction.client.cooldowns` with key `command_name`: an ephemeral `You used /{command_name} recently. Try again in N second(s)`, worded and rounded as the legacy message.
  3. `defer` when `defer` is set (public).
  4. Call `call()`, awaiting the result when it is awaitable.
  5. Start the cooldown on success, unless the user is an admin.
  6. Send `split_message(out)`: the first chunk with `interaction.response.send_message`, or `interaction.followup.send` after a defer; the rest as follow-ups. An empty reply sends nothing.
  - `CommandError` is answered with an ephemeral message of its text.
  - Any other exception is logged and answered with an ephemeral `Something went wrong while running /{command_name}`.
- Produces `slash/options.py`:
  - `to_name(value: str) -> str` returns `"_".join(value.split())`, and raises `CommandError("A name can't be empty")` when that is empty.
  - Autocomplete callbacks, each returning at most 25 `app_commands.Choice`s whose names start with `to_name`-style input, ignoring case:
    - `character_choices(interaction, current)`: from the new `character_repository.get_all_names() -> list[str]` (names and aliases, sorted)
    - `currency_choices(interaction, current)`: from the new `currency_repository.get_currency_names() -> list[str]`
    - `resource_choices(interaction, current)`: from `resource_repository.get_resource_names()`
- Produces `slash/sync.py`:
  - `async def sync_commands(tree, guild_id: int | None) -> None`.
  - With a guild: `copy_global_to(guild)`, `sync(guild=guild)`, `clear_commands(guild=None)`, `sync()`.
  - Without one: `sync()`.
  - `discord.HTTPException` is logged with `logging.exception`, never raised.
- Produces in `tests/fakes.py`:
  - `FakeInteraction(user_id=1, administrator=False, channel=None, client=None, in_guild=True)` with `.user`, `.client`, `.channel`, `.channel_id`, `.guild`, `.message`, `.response` and `.followup`.
    - `.response` has `send_message`, `defer`, `is_done` and `edit_message`.
    - `.followup.send(..., wait=False)` returns a `FakeSentMessage` posted in the channel.
    - `interaction.sent` is a list of `(content, ephemeral, allowed_mentions)`.
  - `FakeClient` gets `cooldowns = Cooldowns(FakeClock())`.
  - `invoke(command, interaction, cog=None, **options)` runs an app command's callback with `asyncio.run`.

- [ ] **Step 1: Write the failing tests**:
  - `test_reply_is_public`: `run(..., lambda: "hi")` gives `sent == [("hi", False, ALLOWED_MENTIONS)]`.
  - `test_command_error_is_ephemeral`.
  - `test_unexpected_error_is_logged_and_ephemeral`: `Something went wrong while running /checkping`.
  - `test_admin_only_refuses_non_admin`: `This command is for admins only`, ephemeral, and `call` not called.
  - `test_cooldown_turns_down_and_is_shared_with_legacy`: start key `"artping"` via `client.cooldowns.start`; `run(... "artping", cooldown_seconds=1)` gives an ephemeral `You used /artping recently. Try again in 1 second`.
  - `test_admins_skip_cooldown`.
  - `test_long_reply_is_split` (Review Focus 3): 4500 characters across lines give 1 response + 2 follow-ups, each ≤ 2000.
  - `test_empty_reply_sends_nothing`.
  - `test_deferred_reply_goes_to_followup`.
  - `test_to_name_turns_spaces_into_underscores`: `to_name("  black   knight ") == "black_knight"`.
  - `test_to_name_refuses_blank` (Review Focus 2).
  - `test_character_choices_match_prefix_and_aliases`: `current="mar"` with alias `Marth_Mask` gives `["Marth_Mask"]`.
  - `test_choices_are_capped_at_25`.
  - `test_sync_to_guild_clears_global`: a fake tree records the call order.
  - `test_sync_failure_is_logged` (Review Focus 5): the fake tree raises `discord.Forbidden`; `sync_commands` returns normally.
- [ ] **Step 2:** Run `tests/fjormcord/bot/artping/slash`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Add the slash command runner, name options and command sync".

---

### Task 9: ArtPingCog with the generated /artping, and EasterEggCog

**Files:**
- Create: `slash/art_ping_cog.py`, `slash/easter_egg_cog.py`
- Modify: `bot.py` (`setup_hook` adds both cogs before syncing)
- Test: `tests/fjormcord/bot/artping/slash/test_art_ping_cog.py`, `test_easter_egg_cog.py`

**Interfaces:**
- Produces:
  - `build_art_ping_command(max_characters: int) -> app_commands.Command`.
    - The callback signature is generated: `interaction`, required keyword-only `character: str`, and optional `character2 … character{max}: str | None = None`. Set `callback.__signature__`; this was checked to work with discord.py 2.7.1.
    - Each option autocompletes with `character_choices`.
    - It runs `run(interaction, "artping", lambda: do_art_ping([to_name(v) for v in filled values]), cooldown_seconds=settings.art_ping_cooldown_seconds)`.
  - `ArtPingCog(commands.Cog)`:
    - `cog_load` adds `build_art_ping_command(settings.art_ping_slash_max_characters)` to `self.bot.tree`, and `cog_unload` removes it.
    - `/addping character`, `/removeping character` and `/checkping`, with the descriptions from the legacy table, cut to ≤ 100 characters.
  - `EasterEggCog`: `/lorenz` replies `easter_eggs.LORENZ_SMILE` and `/chromk` replies `easter_eggs.CHROMK`, both through `run` with no cooldown.

- [ ] **Step 1: Write the failing tests**:
  - `test_art_ping_options_follow_the_setting`: `[p.name for p in build_art_ping_command(3).parameters] == ["character", "character2", "character3"]`, and 10 for `build_art_ping_command(10)`.
  - `test_art_ping_pings_subscribers`: `/artping character="Lucina"` gives a public `Lucina: <@5>`.
  - `test_art_ping_pings_a_character_once` (Review Focus 4): `character="Lucina", character2="marth mask"` (an alias of Lucina) gives `Lucina: <@5>`.
  - `test_add_ping_with_spaces`: Black_Knight exists; `/addping character="black knight"` gives `Ping for Black_Knight has been added`.
  - `test_lorenz_and_chromk_post_the_easter_eggs`.
  - `test_descriptions_fit_discord`: every command in all cogs has a description of at most 100 characters (extend this as cogs are added).
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Add /artping, /addping, /removeping, /checkping, /lorenz and /chromk".

---

### Task 10: CharacterCog

**Files:**
- Create: `slash/character_cog.py`
- Modify: `bot.py`
- Test: `tests/fjormcord/bot/artping/slash/test_character_cog.py`

**Interfaces:**
- Consumes: `character_service.add_character(client, user, name, vote_channel)`, `VoteChannel`, `run`, `to_name`, `character_choices`.
- Produces:
  - `/addcharacter character` (`defer=True`): `VoteChannel(str(interaction.channel_id), interaction.guild is not None, lambda content, view: interaction.followup.send(content, view=view, wait=True))`.
  - `/checkcharacter character` (`defer=True`).
  - Admin commands, each with `@app_commands.default_permissions(administrator=True)`, `@app_commands.guild_only()` and `admin_only=True`:
    - `/removecharacter character`
    - `/addalias character alias`
    - `/removealias character alias`
    - `/setprimaryname alias`
  - Every character and alias option goes through `to_name`. The character options autocomplete.

- [ ] **Step 1: Write the failing tests**:
  - `test_admin_add_character`: `Character Black_Knight has been added`.
  - `test_non_admin_add_character_starts_a_button_vote`: the follow-up message has a `VoteView` and the vote is stored under its ID; a click on it counts.
  - `test_add_character_vote_refused_in_dms`.
  - `test_admin_commands_hidden_and_checked`: `default_permissions.administrator` is true for the four admin commands, and a non-admin `/removecharacter` gets `This command is for admins only`.
  - `test_add_alias_with_spaces`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Add the character and alias slash commands".

---

### Task 11: CurrencyCog

**Files:**
- Create: `slash/currency_cog.py`
- Modify: `bot.py`
- Test: `tests/fjormcord/bot/artping/slash/test_currency_cog.py`

**Interfaces:**
- Produces:
  - `/setcurrency currency amount: app_commands.Range[int, 0, None]`
  - `/clearcurrency currency`
  - `/checkwallet`: passes `interaction.user.display_name` and `slash=True`.
  - `/scoreboard currency page: app_commands.Range[int, 1, None] = 1`: `defer=True`, `slash=True`.
  - Admin commands: `/addcurrency currency` and `/removecurrency currency`.
  - Currency options go through `to_name` and autocomplete with `currency_choices`.

- [ ] **Step 1: Write the failing tests**:
  - `test_set_currency`.
  - `test_amount_too_large_is_refused_by_the_service`: `amount=2**63` gives `Failed to set currency. The amount is too large`.
  - `test_empty_wallet_names_slash_command`.
  - `test_scoreboard_next_page_hint`.
  - `test_admin_currency_commands_are_admin_only`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Add the currency slash commands".

---

### Task 12: ResourceCog and parity

**Files:**
- Create: `slash/resource_cog.py`
- Modify: `bot.py`
- Test: `tests/fjormcord/bot/artping/slash/test_resource_cog.py`, `tests/fjormcord/bot/artping/slash/test_parity.py`

**Interfaces:**
- Produces:
  - `/resource name`: `run(..., lambda: post_resource(name), allowed_mentions=discord.AllowedMentions.none())`.
  - `/resources`: `slash=True`.
  - Admin commands:
    - `/setresource name link` (`defer=True`)
    - `/removeresource name`
  - Resource names do **not** go through `to_name`, and they autocomplete with `resource_choices`.

- [ ] **Step 1: Write the failing tests**:
  - `test_resource_is_posted_without_mentions`: the allowed mentions are all `False`.
  - `test_unknown_resource_is_refused`: an ephemeral `Resource hof doesn't exist`.
  - `test_long_resource_is_split`.
  - `test_resource_name_with_space_is_refused`: `Resource names can only contain letters, digits, _ and -`.
  - `test_every_legacy_command_has_a_slash_command` in `test_parity.py`:
    - `{c.name.removeprefix("~") for c in COMMANDS} - {"help"}` equals the slash command names minus `{"resource", "lorenz", "chromk"}`.
    - The slash names are collected from the cogs' `get_app_commands()` plus `build_art_ping_command(1)`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS.
- [ ] **Step 5:** Commit: "Add the resource slash commands".

---

### Task 13: Documentation

**Files:**
- Modify:
  - `README.md`
    - a slash command section: same names, spaces become underscores, `/artping` up to `art_ping.slash_max_characters`, `/resource`, `/lorenz`, `/chromk`, admin commands hidden
    - the `applications.commands` invite scope (production may need a re-invite)
    - `discord.guild_id` for development, and how to clear leftover guild commands
    - `art_ping.slash_max_characters`
    - the voting paragraph for the button, with "Add Reactions" no longer needed
  - `CLAUDE.md`
    - the Layout and Architecture sections for `legacy/`, `slash/`, `vote_view.py`, typed services and `VoteChannel`
    - "Adding a command = service function + legacy handler and `Command` entry + slash command in its cog"
    - the cooldown key
    - migration `007`
    - the vote button
  - `docs/superpowers/specs/2026-10-26-command-handling-design.md`: the legacy paths and the `~help` line.
  - `docs/superpowers/specs/2026-10-26-character-votes-design.md`: the button, stored voters, conversion.
  - `docs/superpowers/specs/2026-10-26-slash-commands-design.md`: change the header line to "Describes the bot as built" and drop the "(my call)" markers, which were decisions on a draft.
  - `docs/manual-test-plan.md`: slash cases for every cog, the vote button (vote, take back, admin click, pass, restart) and the conversion of a ⭐ vote.

- [ ] **Step 1: Make the edits.**
- [ ] **Step 2:** Run `.venv/Scripts/python -m pytest`. Expected: all PASS. Then `git grep -n "react with\|on_raw_reaction_add\|fjormcord.bot.artping.commands"` should return nothing outside history.
- [ ] **Step 3:** Commit: "Document the slash commands and the vote button".
