# Text Display Layouts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lay out the scoreboard, art ping, add character, check ping, check character, check wallet, resources, help and the scheduled messages as Components V2 containers, with pagination and a currency dropdown.

**Architecture:** Services return a `Layout` (a frozen dataclass: the texts and the rows of controls) instead of a string where the reply is laid out. One module, `view/layout.py`, turns a `Layout` into a `discord.ui.LayoutView` (a `Container` with text displays, separators and action rows) and into the keyword arguments of a send. Every control is a `DynamicItem`, so the one builder serves all messages and every control works after a restart.

**Tech Stack:** Python 3.14, discord.py 2.7.1 (`LayoutView`, `Container`, `TextDisplay`, `Separator`, `ActionRow`, `DynamicItem`), SQLite, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-10-28-text-display-layouts-design.md`

## Global Constraints

- Both syntaxes (`~` and slash) get the same layout; services build it, they never see a message or interaction.
- Every layout is one `discord.ui.Container` with `accent_colour=discord.Colour.blurple()` (a constant, not a setting).
- A Components V2 message has no `content`: send with `view=` only; edit with `content=None, view=...`.
- At most 4000 characters of text per message; a longer layout is split, the first message keeping the start, the last keeping the end and all the controls.
- Replies keep `ALLOWED_MENTIONS`; mentions in text displays must still notify.
- discord.py interaction replies fail on `view=None`: never pass it.
- Page size 10 for the scoreboard, check ping and check character; no page buttons on a single page.
- Errors, confirmations, click replies, easter eggs and posted resources stay plain text.
- Run `.venv/Scripts/python -m ruff check --fix src tests && .venv/Scripts/python -m ruff format src tests` before each commit; comments and strings within 120 characters.
- Each task updates `CLAUDE.md` and `docs/manual-test-plan.md` for what it changes (`README.md` where a command's description changes).
- `tests/fakes.py` and `docs/manual-test-plan.md` use CRLF line endings; keep them (use the Edit tool, not a text-mode script).

## Review Focus

1. Mentions inside a text display: an art ping or Voting Gauntlet message must still pass `ALLOWED_MENTIONS` (users allowed) to the send. Test in Tasks 1 and 5.
2. An art ping whose mentions pass 4000 characters (about 180 subscribers): every mention is sent, header first, footer and nothing else last. Test in Task 5.
3. A vote message posted before this change (plain content, a `character_vote` button): re-rendering it at startup must clear its content, and a click on its old button must still reach the vote. Test in Task 2.
4. A control on a message whose subject has gone (removed currency in the dropdown, removed character on a page click, a page that no longer exists): a private reply, the message unchanged. Tests in Tasks 3 and 4.
5. A closed vote whose message keeps a button (an edit failed): clicking it must not leave an empty message, since removing the view of a layout removes its text. Test in Task 2.

---

### Task 1: The layout model, its rendering and sending

**Files:**
- Create: `src/fjormcord/bot/artping/model/layout.py`
- Create: `src/fjormcord/bot/artping/view/layout.py`
- Modify: `src/fjormcord/bot/artping/util/message_util.py` (add `split_layout`)
- Modify: `src/fjormcord/bot/artping/exception/command_error.py`
- Modify: `src/fjormcord/bot/artping/legacy/dispatch.py`, `src/fjormcord/bot/artping/slash/runner.py`
- Modify: `tests/fakes.py`
- Test: `tests/fjormcord/bot/artping/view/test_layout.py`, `tests/fjormcord/bot/artping/util/test_message_util.py`, `tests/fjormcord/bot/artping/slash/test_runner.py`, `tests/fjormcord/bot/artping/test_bot.py`

**Interfaces:**
- Produces:
  - `model.layout.Layout(texts: tuple[str, ...], rows: tuple[tuple[discord.ui.Item, ...], ...] = ())`, frozen. Rendered as: the texts with a separator between each, then (when there are rows and texts) a separator, then one `ActionRow` per row.
  - `view.layout.ACCENT_COLOUR = discord.Colour.blurple()`
  - `view.layout.to_view(layout: Layout) -> discord.ui.LayoutView` (timeout `None`)
  - `view.layout.layout_text(view: discord.ui.LayoutView) -> str`: the text displays' contents joined with `"\n"`, for logs and tests.
  - `view.layout.message_options(reply: str | Reply | Layout) -> list[dict]`: one dict of send keyword arguments per message: `{"content": chunk}` for each `split_message` chunk of a string (a `Reply` as today: `{"content": …, "view": …}` on the last), `{"view": to_view(part)}` for each `split_layout` part of a `Layout`. `Reply` support is removed in Task 3.
  - `util.message_util.split_layout(layout: Layout, limit: int = 4000) -> list[Layout]`
  - `util.message_util.MAX_LAYOUT_TEXT_LENGTH = 4000`
  - `CommandError(message: str, layout: Layout | None = None)` with attribute `layout`; the import of `Layout` only under `TYPE_CHECKING` (exceptions import nothing from the project at runtime).
  - `slash.runner.run(interaction, call, *, defer=False, ephemeral=False, allowed_mentions=ALLOWED_MENTIONS)`: `ephemeral=True` makes every reply, and the defer, private.
  - Fakes: `FakeChannel.send(content=None, allowed_mentions=None, view=None)`, `FakeInteractionResponse.send_message(content=None, …)` and `FakeFollowup.send(content=None, …)` record `layout_text(view)` as the content when `view` is a `LayoutView`; `FakeSentMessage.edit` and `FakeInteraction.edit_original_response` raise `AssertionError("A layout message can't have content")` when given a `LayoutView` with content other than `None`, and set `content` to `layout_text(view)`. `fakes.button_labels(view) -> list[str]`: the labels of every button, unwrapping `DynamicItem`s, in order; `fakes.select_options(view) -> list[str]`: the labels of the dropdown's options.

- [ ] **Step 1: Write the failing tests**

`test_layout.py`:
```python
def test_layout_is_a_container_of_texts_separators_and_rows():
    button = discord.ui.Button(label="x", custom_id="x")
    view = to_view(Layout(("### Head", "Body"), ((button,),)))
    [container] = view.children
    assert isinstance(container, discord.ui.Container)
    assert container.accent_colour == discord.Colour.blurple()
    assert [type(item).__name__ for item in container.children] == [
        "TextDisplay", "Separator", "TextDisplay", "Separator", "ActionRow"]
    assert view.is_persistent()

def test_layout_without_rows_ends_with_its_text():  # ["TextDisplay"] for Layout(("Only",))
def test_layout_text_joins_the_text_displays():  # layout_text(to_view(Layout(("a", "b")))) == "a\nb"
def test_message_options_of_a_string_are_its_chunks():  # message_options("hi") == [{"content": "hi"}]
def test_message_options_of_a_layout_are_views():  # one dict, only key "view", a LayoutView
```
`test_message_util.py`:
```python
def test_split_layout_keeps_a_short_layout_whole():
    layout = Layout(("a", "b"))
    assert split_layout(layout) == [layout]

def test_split_layout_splits_a_long_text_and_keeps_the_rows_on_the_last_part():
    rows = ((discord.ui.Button(label="x", custom_id="x"),),)
    body = " ".join(f"<@{n:018d}>" for n in range(300))
    parts = split_layout(Layout(("### Head\n" + body, "Footer"), rows), limit=4000)
    assert len(parts) > 1
    assert parts[0].texts[0].startswith("### Head")
    assert parts[-1].texts[-1] == "Footer" and parts[-1].rows == rows
    assert all(part.rows == () for part in parts[:-1])
    assert all(sum(map(len, part.texts)) <= 4000 for part in parts)
    assert " ".join(" ".join(part.texts) for part in parts).split().count("<@000000000000000299>") == 1
```
`test_runner.py`: a call returning a `Layout` is sent as a view with `ALLOWED_MENTIONS`; `run(…, ephemeral=True)` sends it ephemerally (and with `defer=True` defers with `{"ephemeral": True}`); a `CommandError("No", layout=Layout(("No", "Hint")))` is sent ephemerally as that layout, with the text `"No\nHint"`.
`test_bot.py`: a `~` handler returning a `Layout` is sent with `view=` and no content; a `CommandError` with a layout is sent as the layout.

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/view/test_layout.py tests/fjormcord/bot/artping/util/test_message_util.py -q`
Expected: FAIL (`ModuleNotFoundError: fjormcord.bot.artping.model.layout`)

- [ ] **Step 3: Implement `Layout`, `to_view`, `layout_text`, `message_options`, `split_layout`, `CommandError.layout`, the fakes**

`split_layout`: pack the texts into parts in order; a text that doesn't fit the room left is split with `split_message(text, room)` (or `limit` in a fresh part); the rows go on the last part only.

- [ ] **Step 4: Send through `message_options` in `legacy.dispatch.handle_message` and `slash.runner.run`; send a `CommandError`'s layout when it has one**

`dispatch.get_message` returns `e.layout or str(e)`; in `runner`, the error path sends `message_options(e.layout)` ephemerally after the placeholder handling of `_send_error`. Drop `split_reply` and `view_option` from `message_util` once nothing uses them; `_send` passes `**options` only.

- [ ] **Step 5: Run the whole suite**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass

- [ ] **Step 6: Update `CLAUDE.md` (the `model/`, `util/` and `view/` bullets, `runner.run`'s `ephemeral`, the fakes) and commit**

```bash
git add -A && git commit -m "Add layouts: services can reply with a container of text displays and controls"
```

---

### Task 2: Add character and the votes as layouts

**Files:**
- Modify: `src/fjormcord/bot/artping/view/vote_view.py` (replace `VoteView` with `VoteButton`)
- Modify: `src/fjormcord/bot/artping/view/subscribe_view.py` (drop `SubscribeView`)
- Modify: `src/fjormcord/bot/artping/service/character_service.py`, `service/character_vote_service.py`, `model/character_vote.py`
- Modify: `src/fjormcord/bot/artping/legacy/handler/character_handlers.py`, `slash/cog/character_cog.py`, `slash/cog/character_vote_cog.py`, `bot.py`
- Test: `tests/fjormcord/bot/artping/service/test_character_vote_service.py`, `slash/cog/test_character_cog.py`, `slash/cog/test_character_vote_cog.py`, `view/test_subscribe_view.py`, `view/test_vote_view.py` (new), `test_bot.py`

**Interfaces:**
- Consumes: `Layout`, `to_view`, `layout_text` (Task 1).
- Produces:
  - `vote_view.VoteButton(count: int = 0)`: a `DynamicItem[discord.ui.Button]` with `template=r"character_vote"` and `custom_id="character_vote"` (unchanged, so vote messages posted before still route), label `Vote (count/votes_needed)`, the configured emoji, primary style; its callback is today's `VoteView.vote`.
  - `subscribe_view.SubscribeButton.for_character(character: Character) -> SubscribeButton` (classmethod; label `Subscribe to <name>` cut to 80).
  - `VoteChannel.send: Callable[[discord.ui.LayoutView], Awaitable[Any]]`.
  - `character_service.add_character(...) -> str | Layout`; the direct add is `Layout(("Character Lucina has been added",), ((SubscribeButton.for_character(c),),))`.
  - `bot.setup_hook` registers `TrackButton, PageButton, SubscribeButton, VoteButton` with `add_dynamic_items`; `CharacterVoteCog` no longer calls `add_view`.

- [ ] **Step 1: Write the failing tests**

In `test_character_vote_service.py` (`label(message)` becomes `button_labels(message.view)` from the fakes):
- the vote message's text is `Vote to add Lucina. Votes needed: 2`, its labels `["Vote (1/2)"]`;
- a passed vote: text `Character Lucina has been added`, labels `["Subscribe to Lucina"]`; the other open votes for the name: `Character Lucina has already been added`, `["Subscribe to Lucina"]`;
- a vote dropped for a taken name: text `Hector is already an alias of Lucina`, labels `[]`;
- `test_old_plain_vote_message_is_rerendered_as_a_layout`: a vote whose message was posted with `content="Vote to add Lucina. Votes needed: 2"` and no layout is, after `check_votes(client)`, a layout with that text and `["Vote (0/2)"]` (the fake's edit asserts the content was cleared);
- `test_click_on_a_closed_vote_keeps_a_text`: a vote message whose vote is gone, clicked: the message becomes `This vote has already been closed` with no buttons.

`test_vote_view.py`:
```python
def test_vote_button_keeps_the_custom_id_of_old_vote_messages():
    assert VoteButton(1).custom_id == "character_vote"
    assert VoteButton.__discord_ui_compiled_template__.fullmatch("character_vote")
```
`test_character_cog.py` / `test_bot.py`: a direct add is sent as a layout with text `Character Lucina has been added` and labels `["Subscribe to Lucina"]`; `setup_hook` registers the four dynamic items and no persistent view.

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/service/test_character_vote_service.py -q`
Expected: FAIL

- [ ] **Step 3: Implement**

`character_vote_service._edit(vote_message, layout: Layout)` edits with `content=None, view=to_view(layout)`; every edit in the service goes through it with the layouts above. `start_vote` sends `to_view(Layout((_vote_text(name),), ((VoteButton(1),),)))`. The legacy `VoteChannel` sends `message.channel.send(view=view)`, the slash one `interaction.followup.send(view=view, wait=True)`.

- [ ] **Step 4: Run the whole suite**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass

- [ ] **Step 5: Update `CLAUDE.md` (Character votes, `view/`) and the manual test plan (sections 5 and 7: the layouts, and an old vote message re-rendered at startup), then commit**

```bash
git add -A && git commit -m "Lay out the add character and vote messages"
```

---

### Task 3: Scoreboard layout with a currency dropdown and generic page buttons

**Files:**
- Create: `src/fjormcord/bot/artping/view/page_view.py` (the generic `PageButton`)
- Create: `src/fjormcord/bot/artping/util/page_util.py`
- Modify: `src/fjormcord/bot/artping/view/scoreboard_view.py` (only `CurrencySelect`), `service/currency_service.py`, `repository/currency_repository.py`, `bot.py`
- Delete: `src/fjormcord/bot/artping/model/reply.py` and the `Reply` branch of `message_options`
- Test: `tests/fjormcord/bot/artping/view/test_scoreboard_view.py`, `view/test_page_view.py` (new), `util/test_page_util.py` (new), `service/test_typed_services.py`, `legacy/handler/test_currency_handlers.py`, `slash/cog/test_currency_cog.py`

**Interfaces:**
- Consumes: `Layout`, `to_view` (Task 1).
- Produces:
  - `page_util.PAGE_SIZE = 10`; `page_util.get_page(entries: list[T], page: int, description: str) -> tuple[list[T], int]`: the entries on the page and the page count; raises `CommandError(f"Page {page} doesn't exist. {description} has {count} page(s)")` with `page` for 1 and `pages` otherwise. Called only with non-empty `entries`.
  - `page_view.PageButton(kind: str, subject_id: int, page: int, label: str, disabled: bool = False)`: `template=r"page:(?P<kind>scoreboard|pings|character):(?P<subject_id>\d+):(?P<page>\d+)"`. The callback, as today's scoreboard button (cooldown, defer, private errors, `"Something went wrong while turning the page"`), awaits `PAGES[kind](interaction.client, subject_id, page)` and edits the message with `content=None, view=to_view(layout)`. `PAGES` maps `"scoreboard"` to `currency_service.get_scoreboard_page`; Task 4 adds the others. Services are imported as modules.
  - `page_view.page_buttons(kind: str, subject_id: int, page: int, page_count: int) -> tuple[PageButton, ...]`: `()` for one page, else `◀ Previous` (page - 1, disabled on 1) and `Next ▶` (page + 1, disabled on the last).
  - `scoreboard_view.CurrencySelect(currencies: list[Currency], current_id: int)`: `DynamicItem[discord.ui.Select]`, `template=r"scoreboard_currency"`, options labelled by name with the currency ID as value, the current one `default=True`. The callback is a command like a page click and renders `get_scoreboard_page(client, int(value), 1)`.
  - `currency_repository.get_currencies(limit: int) -> list[Currency]`, alphabetically ignoring case.
  - `currency_service.get_scoreboard(client, name, page=1) -> Layout` and `get_scoreboard_page(client, currency_id, page) -> Layout` (removed currency: `CommandError("This currency doesn't exist anymore")`).

- [ ] **Step 1: Write the failing tests**

- `test_typed_services.py`: with 11 users, `get_scoreboard(client, "Orbs")` has `texts == ("### Scoreboard for Orbs (page 1/2)", "1. user11 (11)\n…\n10. user2 (2)")` and labels `["◀ Previous", "Next ▶"]`; with one currency there is no dropdown; with a second currency `Gems`, `select_options(to_view(layout)) == ["Gems", "Orbs"]` with Orbs the default; one page: `("### Scoreboard for Orbs", "1. Alice (5)")` and no buttons; nobody set: `("### Scoreboard for Orbs", "Nobody has set their Orbs yet")`, still with the dropdown when there are 2 currencies.
- `test_currency_handlers.py`: the existing page tests compare `texts`; the out-of-range error is `Page 4 doesn't exist. The scoreboard for Orbs has 3 pages` and, for one page, `… has 1 page`.
- `test_scoreboard_view.py`: picking `Gems` turns the message to `### Scoreboard for Gems`; picking a removed currency answers `[("This currency doesn't exist anymore", True, None)]` and leaves the message; a pick within the cooldown is turned down; the existing page tests move to `test_page_view.py` with `custom_id`s `page:scoreboard:<id>:<page>`.
- `test_page_util.py`: page 2 of 25 entries is entries 11–20 and count 3; page 4 raises the error above.

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/service/test_typed_services.py tests/fjormcord/bot/artping/util/test_page_util.py -q`
Expected: FAIL

- [ ] **Step 3: Implement `page_util`, `PageButton`, `page_buttons`, `CurrencySelect`, `get_currencies` and the scoreboard layout**

The scoreboard's rows: the dropdown row when `get_currencies(25)` has at least 2, then the page buttons row when there are several pages. `bot.setup_hook` registers `page_view.PageButton` and `CurrencySelect` in place of the scoreboard's `PageButton`.

- [ ] **Step 4: Delete `Reply` and run the whole suite**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass

- [ ] **Step 5: Update `CLAUDE.md` and the manual test plan (section 8 and 11.31–11.34: the layout, the dropdown, a removed currency in it), then commit**

```bash
git add -A && git commit -m "Lay out the scoreboard, with a currency dropdown"
```

---

### Task 4: Check ping and check character, paged

**Files:**
- Modify: `src/fjormcord/bot/artping/service/art_ping_service.py`, `service/character_service.py`, `repository/art_ping_repository.py` (if a sorted list is missing), `view/page_view.py` (`PAGES`)
- Modify: `src/fjormcord/bot/artping/legacy/handler/art_ping_handlers.py`, `slash/cog/art_ping_cog.py`
- Test: `tests/fjormcord/bot/artping/legacy/handler/test_art_ping_handlers.py`, `legacy/handler/test_character_handlers.py`, `slash/cog/test_art_ping_cog.py`, `slash/cog/test_character_cog.py`, `view/test_page_view.py`

**Interfaces:**
- Consumes: `page_util.get_page`, `page_view.page_buttons`, `PAGES` (Task 3).
- Produces:
  - `art_ping_service.check_ping(client, user_id: str, page: int = 1) -> str | Layout` (async): `"You are not subscribed to any characters"` when empty; otherwise `texts = ("### Alice's pings", "Chrom\nLucina")`, with ` (page 1/2)` after the header when several pages; the name is `get_username(client, user_id)`; error description `The list of Alice's pings`.
  - `art_ping_service.check_ping_page(client, user_id: int, page: int) -> str | Layout`, registered as `PAGES["pings"]`.
  - `character_service.check_character(client, name, page: int = 1) -> Layout` and `check_character_page(client, character_id: int, page: int) -> Layout` (removed: `CommandError("This character doesn't exist anymore")`), registered as `PAGES["character"]`: `texts = ("### Lucina's pings\nAliases: Luci", "Alice\nBob")`, without the aliases line when there are none, `Nobody is subscribed to Lucina` as the body when nobody is; usernames looked up only for the page shown; error description `The list of Lucina's pings`.
  - `/checkping` runs with `ephemeral=True, defer=True`; `/checkcharacter` stays public.

- [ ] **Step 1: Write the failing tests**

The exact texts above for: ping list of 3; 12 characters (`(page 1/2)`, labels `["◀ Previous", "Next ▶"]`, the `custom_id`s `page:pings:<user id>:2`); the empty ping list; `/checkping` sent ephemerally (`interaction.sent[0].ephemeral is True`, deferred with `{"ephemeral": True}`); a character with aliases and 2 subscribers; with no subscribers; a page click on a removed character answered `[("This character doesn't exist anymore", True, None)]`; turning to page 2 of a character with 12 subscribers shows users 11–12.

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/legacy/handler/test_art_ping_handlers.py tests/fjormcord/bot/artping/legacy/handler/test_character_handlers.py -q`
Expected: FAIL

- [ ] **Step 3: Implement the services, the handler and cog changes, and the `PAGES` entries**

- [ ] **Step 4: Run the whole suite**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass

- [ ] **Step 5: Update `CLAUDE.md`, `README.md` (`/checkping` is private), the manual test plan (4.19, 5.x check character, 11.8), then commit**

```bash
git add -A && git commit -m "Lay out check ping and check character, with pages"
```

---

### Task 5: Art ping layout

**Files:**
- Modify: `src/fjormcord/bot/artping/service/art_ping_service.py`, `legacy/handler/art_ping_handlers.py`, `slash/cog/art_ping_cog.py`
- Test: `tests/fjormcord/bot/artping/legacy/handler/test_art_ping_handlers.py`, `slash/cog/test_art_ping_cog.py`, `service/test_typed_services.py`

**Interfaces:**
- Consumes: `Layout`, `CommandError(message, layout)` (Task 1); `character_vote_service.is_voting_enabled()`.
- Produces: `art_ping_service.do_art_ping(names: list[str], administrator: bool, slash: bool = False) -> Layout`. The legacy handler passes `is_administrator(message.author)`, the cog `is_administrator(interaction.user)` and `slash=True`.

Texts, in the syntax used (`/` or `~`):
- `texts[0]`: `### Chrom, Lucina`, then `No character entry for Marth` when names are missing, then the mentions or `Nobody is subscribed to Chrom, Lucina`, each on its own line.
- `texts[1]` (the footer): `Want to be pinged for Chrom? Use /addping Chrom` for the first existing character, then, for the first missing name, `Use /addcharacter Marth to start a vote to add it`, or `Use /addcharacter Marth to add it` for an admin or when voting is off.
- No name exists: `CommandError("No character entry for Marth", layout=Layout(("No character entry for Marth", "Use /addcharacter Marth to start a vote to add it")))`, so it stays private for slash and starts no cooldown.

- [ ] **Step 1: Write the failing tests**

The texts above for: two existing characters; one existing and one missing (non-admin); the same for an admin; voting off (`use_settings(monkeypatch, character_votes_needed=1)`); nobody subscribed; only missing names, for `/artping` (ephemeral) and `~artping` (public, and the user's cooldown not started); `test_art_ping_with_many_subscribers_is_split`: 300 subscribers to Lucina, sent through `~artping` with the fake channel: several messages, the first text starting `### Lucina`, the last ending with the footer, every `<@id>` present once, and every send passing the client's allowed mentions (`sent_allowed_mentions` entries `None`, the client default, which allows users); the slash form sends with `ALLOWED_MENTIONS`.

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/legacy/handler/test_art_ping_handlers.py -q`
Expected: FAIL

- [ ] **Step 3: Implement**

- [ ] **Step 4: Run the whole suite**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass

- [ ] **Step 5: Update `CLAUDE.md` and the manual test plan (section 4 and 11.9: the layout, the footer, the hint, a long ping list), then commit**

```bash
git add -A && git commit -m "Lay out the art ping, with a footer reminder and hint"
```

---

### Task 6: Check wallet, resources and help

**Files:**
- Modify: `src/fjormcord/bot/artping/service/currency_service.py`, `service/resource_service.py`, `legacy/commands.py`
- Test: `tests/fjormcord/bot/artping/legacy/handler/test_currency_handlers.py`, `legacy/handler/test_resource_handlers.py`, `legacy/test_commands.py`, `service/test_typed_services.py`, the slash cog tests of wallet and resources

**Interfaces:**
- Produces:
  - `check_wallet(user_id, display_name, slash=False) -> str | Layout`: the empty sentence as today; else `("### user1's wallet", "Feathers: 10\nOrbs: 250")`.
  - `list_resources(slash=False) -> str | Layout`: the empty sentence as today; legacy `("### Resources", "~faq\n~hof")`; slash `("### Resources", "faq\nhof", "Post one with /resource")`.
  - `show_help(client, message) -> Layout`: `texts[0]` is `## Commands`, `Content in brackets is what to add when using a command`, `MULTI_WORD_HINT`, `All commands are also available as slash commands, type /`, one per line; then one text per section, `### <section>` followed by each command as `**~artping (character name)**` and its description on the next line. Sections: `SECTION_ART_PING = "Art Ping Commands"`, `SECTION_CURRENCY = "Gacha Currency Commands"`, `SECTION_ADMIN = "Admin Commands"` (admins only). `Handler` returns `str | Layout | Awaitable[str | Layout]`.

- [ ] **Step 1: Write the failing tests**

The texts above; help for a non-admin has 3 texts and no `Admin Commands`, for an admin 4; the admin help's text is under 4000 characters, so it is one message.

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/legacy/test_commands.py -q`
Expected: FAIL

- [ ] **Step 3: Implement**

- [ ] **Step 4: Run the whole suite**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass

- [ ] **Step 5: Update `CLAUDE.md` and the manual test plan (`~help`, 8.18–8.19, 9.x resources, 11.29–11.30), then commit**

```bash
git add -A && git commit -m "Lay out check wallet, resources and help"
```

---

### Task 7: Scheduled messages

**Files:**
- Modify: `src/fjormcord/bot/artping/coliseum.py`, `voting_gauntlet.py`, `view/voting_gauntlet_view.py` (drop `TrackView`)
- Test: `tests/fjormcord/bot/artping/test_coliseum.py`, `test_voting_gauntlet.py`, `view/test_voting_gauntlet_view.py`

**Interfaces:**
- Consumes: `Layout`, `message_options` (Task 1).
- Produces:
  - `voting_gauntlet_view.track_buttons(tournament_id: int, matchup: tuple[Entrant, Entrant]) -> tuple[TrackButton, TrackButton]`, in the site's order.
  - `voting_gauntlet.format_matchup(matchup, trackers, tournament_id: int) -> Layout`: `texts[0]` is today's lines (`Edelgard (Stronger)`, `12,345`, …); `texts[1]`, only with trackers, the mentions; rows: the two Track buttons. Sent part by part with `message_options`, each part an own message.
  - The Coliseum reminder is sent as `message_options(Layout((message,)))`.

- [ ] **Step 1: Write the failing tests**

The Coliseum message is a layout with today's text; a matchup without trackers has one text and labels `["Track Edelgard", "Track Dimitri"]`; with trackers, two texts, the second the mentions; a matchup with 300 trackers is split, the buttons only on the last message.

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/test_coliseum.py tests/fjormcord/bot/artping/test_voting_gauntlet.py -q`
Expected: FAIL

- [ ] **Step 3: Implement**

- [ ] **Step 4: Run the whole suite and ruff**

Run: `.venv/Scripts/python -m pytest -q` and the ruff command of the Global Constraints
Expected: all pass, `All checks passed!`

- [ ] **Step 5: Update `CLAUDE.md` (`coliseum.py`, `voting_gauntlet.py`) and the manual test plan (sections 10 and 13), then commit**

```bash
git add -A && git commit -m "Lay out the Coliseum reminder and the Voting Gauntlet matchups"
```
