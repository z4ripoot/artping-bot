# Subscribe Controls Under Art Pings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Art pings (`/artping`, `~artping`) carry Subscribe buttons for up to 5 characters, or a multi-select dropdown
for more, so readers can subscribe without typing `addping`.

**Architecture:** `art_ping_service.do_art_ping` puts the controls in its `Layout`'s `rows`; `view/subscribe_view.py`
builds them (the existing `SubscribeButton` and a new `SubscribeSelect`). A pick in the dropdown calls a new
`art_ping_service.subscribe_many` through `interaction_util.answer_click`, like the button.

**Tech Stack:** Python 3, discord.py 2.x (`DynamicItem`, `ui.Select`), SQLite, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-11-16-art-ping-subscribe-controls-design.md`

## Global Constraints

- Run commands from the repository root with `.venv/Scripts/python`.
- Hint copy, verbatim (`~addping` in the `~` syntax, `/addping` for slash):
  - 1 character: `Want to be pinged for Lucina? Use /addping Lucina or click the button below`
  - 2-5: `Want to be pinged for Lucina? Use /addping Lucina or click one of the buttons below to subscribe to the corresponding character`
  - more than 5: `Want to be pinged for Lucina? Use /addping Lucina or pick characters from the menu below to subscribe to them`
- At most 5 buttons (`MAX_SUBSCRIBE_BUTTONS = 5`), at most 25 dropdown options (`MAX_SELECT_OPTIONS = 25`, its own
  constant, not `MAX_SLASH_OPTIONS`); the dropdown lists the first 25 alphabetically.
- Picks and clicks are not commands: no cooldown, anyone may use them.
- `art_ping_service` and `subscribe_view` import each other as modules only (`from fjormcord.bot.artping.view import
  subscribe_view`), never names.
- Ruff before each commit: `.venv/Scripts/python -m ruff check --fix src tests && .venv/Scripts/python -m ruff format src tests`.

## Review Focus

- A dropdown pick after a restart: the select must be rebuilt from the message's own options (`from_custom_id`
  returns `cls(item)`), or the pick reads no options. Test: Task 1 `test_pick_after_restart_subscribes`.
- A pick mixing new, already-followed and deleted characters must still add the new ones and answer once. Test: Task
  1 `test_pick_reports_added_existing_and_removed`.
- A ping with a missing name and 6+ existing characters keeps the `addcharacter` line under the menu hint. Test: Task
  2 `test_art_ping_hint_with_menu_keeps_add_character_line`.
- A long ping split over several messages keeps the controls on the last one only. Test: Task 2 (update of the
  existing split test in `test_art_ping_handlers.py`).
- Duplicate names (`~artping Lucina lucina`) give one button, not two. Test: Task 2
  `test_art_ping_buttons_once_per_character`.

---

### Task 1: SubscribeSelect and subscribe_many

**Files:**
- Modify: `src/fjormcord/bot/artping/service/art_ping_service.py`
- Modify: `src/fjormcord/bot/artping/view/subscribe_view.py`
- Modify: `src/fjormcord/bot/artping/bot.py:48` (register `SubscribeSelect`)
- Test: `tests/fjormcord/bot/artping/view/test_subscribe_view.py`, `tests/fjormcord/bot/artping/test_bot.py:122`

**Interfaces:**
- Produces:
  - `art_ping_service.subscribe_many(user_id: str, character_ids: list[int]) -> str`
  - `subscribe_view.SUBSCRIBE_SELECT_ID = "subscribe_select"`, `MAX_SELECT_OPTIONS = 25`
  - `subscribe_view.SubscribeSelect(select: discord.ui.Select)`, `SubscribeSelect.for_characters(characters:
    list[Character]) -> SubscribeSelect` (options: label `name[:100]`, value `str(id)`, in the given order, cut to
    `MAX_SELECT_OPTIONS`; `placeholder="Subscribe to characters"`, `min_values=1`, `max_values=len(options)`)

- [ ] **Step 1: Write the failing tests** in `test_subscribe_view.py`, with a `pick(select, character_ids,
  user_id=7)` helper that rebuilds the select with `after_restart`, sets `rebuilt.item._values = [str(id) ...]` (as
  `test_scoreboard_view.pick` does) and returns `FakeInteraction(user_id).sent` after the callback.

```python
def test_select_lists_the_characters_and_allows_picking_all():
    select = SubscribeSelect.for_characters([Character(1, "Chrom"), Character(2, "Lucina")])
    assert [(o.label, o.value) for o in select.item.options] == [("Chrom", "1"), ("Lucina", "2")]
    assert (select.item.custom_id, select.item.min_values, select.item.max_values) == ("subscribe_select", 1, 2)

def test_select_holds_at_most_25_characters():
    select = SubscribeSelect.for_characters([Character(i, f"C{i:02}") for i in range(30)])
    assert len(select.item.options) == 25 and select.item.max_values == 25

def test_pick_after_restart_subscribes():
    chrom, lucina = add_character("Chrom"), add_character("Lucina")
    select = SubscribeSelect.for_characters([chrom, lucina])
    assert pick(select, [chrom.id, lucina.id]) == [("Ping for Chrom, Lucina has been added", True, None)]
    assert art_ping_repository.get_art_ping_users([lucina.id]) == ["7"]

def test_pick_reports_added_existing_and_removed():
    chrom, lucina, robin = add_character("Chrom"), add_character("Lucina"), add_character("Robin")
    art_ping_repository.add_ping(robin.id, "7")
    select = SubscribeSelect.for_characters([chrom, lucina, robin])
    character_repository.remove_character(lucina.id)
    assert pick(select, [chrom.id, lucina.id, robin.id]) == [(
        "Ping for Chrom has been added\nYou are already subscribed to Robin\n"
        "Some picked characters don't exist anymore", True, None)]

def test_pick_has_no_cooldown(): ...  # two picks by user 7 in a row both subscribe (mirror test_click_has_no_cooldown)
```

  In `test_bot.py:122` expect `[TrackButton, PageButton, CurrencySelect, SubscribeButton, SubscribeSelect, VoteButton]`.

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping/view/test_subscribe_view.py tests/fjormcord/bot/artping/test_bot.py -q`
Expected: FAIL with `ImportError: cannot import name 'SubscribeSelect'`.

- [ ] **Step 3: Implement `subscribe_many` in `art_ping_service.py`.** Walk the IDs in order: added names, already
  subscribed names, and whether any ID has no character. Reply lines in that order, joined with `\n`, each only when
  non-empty: `Ping for <names, ", "-joined> has been added` (through `log_and_reply`), `You are already subscribed to
  <names>`, `Some picked characters don't exist anymore`. Never raises `CommandError`.

- [ ] **Step 4: Implement `SubscribeSelect` in `subscribe_view.py`**, modelled on `scoreboard_view.CurrencySelect`
  (`template=SUBSCRIBE_SELECT_ID`, `from_custom_id` returns `cls(item)`). Its callback calls `answer_click(self,
  interaction, lambda: art_ping_service.subscribe_many(str(interaction.user.id), [int(v) for v in self.item.values]),
  "Something went wrong while subscribing")`. Register it in `bot.py`'s `add_dynamic_items`, after `SubscribeButton`.

- [ ] **Step 5: Run to verify they pass**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass.

- [ ] **Step 6: Ruff and commit**

```bash
git add src tests
git commit -m "Add a dropdown that subscribes to several characters"
```

### Task 2: Controls and hints under art pings

**Files:**
- Modify: `src/fjormcord/bot/artping/service/art_ping_service.py` (`do_art_ping`)
- Modify: `src/fjormcord/bot/artping/view/subscribe_view.py` (`subscribe_rows`)
- Modify: `CLAUDE.md` (Art pings bullet and `view/` bullet: the controls, `SubscribeSelect`, `subscribe_select`)
- Test: `tests/fjormcord/bot/artping/legacy/handler/test_art_ping_handlers.py`,
  `tests/fjormcord/bot/artping/slash/cog/test_art_ping_cog.py:44`, `tests/fjormcord/bot/artping/test_bot.py:27`

**Interfaces:**
- Consumes: `SubscribeButton.for_character`, `SubscribeSelect.for_characters` (Task 1).
- Produces: `subscribe_view.MAX_SUBSCRIBE_BUTTONS = 5`; `subscribe_view.subscribe_rows(characters:
  list[Character]) -> tuple[tuple[discord.ui.Item, ...], ...]`: `()` for none, one row of `SubscribeButton`s for
  1-5, one row holding one `SubscribeSelect` for more.

- [ ] **Step 1: Write the failing tests** in `test_art_ping_handlers.py` (read buttons with `button_labels(to_view(out))`
  and options with `select_options(to_view(out))` from `tests.fakes` / `view.layout`):
  - `test_art_ping_one_character_has_a_button`: `~artping lucina` → `out.texts[1] == "Want to be pinged for Lucina? Use ~addping Lucina or click the button below"`, labels `["Subscribe to Lucina"]`.
  - `test_art_ping_five_characters_have_buttons`: five characters → the 2-5 hint for the alphabetically first, five labels in alphabetical order.
  - `test_art_ping_six_characters_have_a_menu`: six → the menu hint, `select_options` lists the six alphabetically, no buttons.
  - `test_art_ping_hint_with_menu_keeps_add_character_line`: six existing + `Marth` → `texts[1]` is the menu hint, `\n`, `Use ~addcharacter Marth to start a vote to add it`.
  - `test_art_ping_buttons_once_per_character`: `~artping Lucina lucina` → one label.
  - Update every existing expected hint in this file, `test_art_ping_cog.py:44` (slash, `/addping`) and
    `test_bot.py:27` to the 1-character hint; the split test's `sent[-1]` ends with it and only the last sent message
    has the button. The only-unknown-names test keeps its hint and has no controls.

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/fjormcord/bot/artping -q`
Expected: the new and updated tests FAIL on the old hint text / missing controls.

- [ ] **Step 3: Implement `subscribe_rows`** in `subscribe_view.py`, and in `do_art_ping` pass `rows=
  subscribe_view.subscribe_rows(characters)` to the returned `Layout` and append to the addping footer line the hint
  ending that fits `len(characters)` (see Global Constraints). The `CommandError` layout (no characters) is unchanged.

- [ ] **Step 4: Run all tests**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Update `CLAUDE.md`, ruff, commit**

```bash
git add src tests CLAUDE.md
git commit -m "Add Subscribe buttons or a dropdown under art pings"
```
