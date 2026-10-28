# Text display layouts

## Intent

The bot's informational replies are walls of plain text. Discord's Components V2 (`discord.ui.LayoutView` with
`TextDisplay`, `Separator` and `ActionRow`, available in the installed discord.py 2.7.1) lets a message be laid out
as a header, a body and a footer, with the buttons and dropdowns placed inside the message. This change moves the
bot's informational and scheduled messages to such layouts so they are easier to read, adds pagination where lists
can grow long, and adds a currency dropdown to the scoreboard.

Builds on the scoreboard page buttons and the Subscribe button (commit `2fc54c7`, not released yet), which already
exist as `DynamicItem`s in `src/fjormcord/bot/artping/view/`.

## Goals

Each message below becomes a layout: one `discord.ui.Container` (the box with a coloured bar on its left) holding the
whole anatomy, its buttons and dropdown included. "Separator" is a `discord.ui.Separator`; "text" is a `TextDisplay`
(markdown works in it). Both syntaxes, `~` and slash, get the same layout, since both run the same service.

### Scoreboard (`~scoreboard`, `/scoreboard`)

- Text: the header, `Scoreboard for Orbs`, with `(page 1/3)` when there are several pages.
- Separator, then text: the ranking, as today (`1. Alice (250)`, 10 per page).
- Separator, then the controls:
  - A dropdown of the currencies. Picking one turns the same message to page 1 of that currency's scoreboard.
  - The existing `◀ Previous` / `Next ▶` buttons, only when there are several pages.
- Dropdown: anyone may use it, it has the cooldown (it is a command, like turning a page), and it keeps working
  after a restart. It lists the currencies, alphabetically, as they were when the message was rendered; Discord
  allows 25 options, so beyond 25 it lists the first 25. The current currency is the selected option.
- "Nobody has set their Orbs yet" becomes this layout too, with that sentence as the body, so the dropdown can switch
  away from an empty scoreboard.
- A currency picked from the dropdown that has been removed since is answered privately, like a removed currency on
  a page click today ("This currency doesn't exist anymore").

### Art ping (`~artping`, `/artping`)

- Text: the header, the names of the characters that exist (e.g. `Lucina, Chrom`).
- Text: the body.
  - `No character entry for Marth` when some names match no character, above the pings.
  - The pings: `<@id> <@id> …` (they must still notify the users), or `Nobody is subscribed to Lucina, Chrom`.
- Separator, then text: the footer, one line for each that applies:
  - When a character exists: `Want to be pinged for Lucina? Use /addping Lucina`, for the first existing character.
  - When a name matches no character: for a non-admin `Use /addcharacter Marth to start a vote to add it`, for an
    admin `Use /addcharacter Marth to add it`, for the first missing name.
  - The commands are named in the syntax that was used: `~addping`, `~addcharacter` for `~artping`.
- When no name matches a character there is no header and no pings: the body is `No character entry for Marth`, then
  the separator and the footer hint. For `/artping` this reply is private (ephemeral), as the error is today; for
  `~artping` it is public, as every `~` reply is.

### Add character (`~addcharacter`, `/addcharacter`, and the vote messages)

- Every message: text, a separator, then the button.
- Vote message: `Vote to add Lucina. Votes needed: 5`, separator, the Vote button (`Vote (1/5)`, as today).
- Added, by an admin directly or by a vote that passed: `Character Lucina has been added`, separator,
  `Subscribe to Lucina`.
- The other open votes for the name, closed by that: `Character Lucina has already been added`, separator,
  `Subscribe to Lucina`.
- A vote dropped because its name got taken another way (`Hector is already an alias of Lucina`): the text only, no
  separator, no button.
- Open votes posted before this change get the new layout at the next startup: `check_open_votes` already re-renders
  every open vote message then.

### Check ping (`~checkping`, `/checkping`)

- Text: the header `Alice's pings` (the user's name, see Decided), with `(page 1/3)` when there are several pages.
- Separator, then text: the characters, one per line, 10 per page.
- Separator, then `◀ Previous` / `Next ▶`, only when there are several pages; they work like the scoreboard's (the
  cooldown, a restart), and turn the page of that user's list.
- `/checkping` is private (ephemeral), so only the user sees it and can turn its pages. `~checkping` stays public:
  a `~` reply can't be private.

### Check character (`~checkcharacter`, `/checkcharacter`)

- Like check ping, public, with the header `Lucina's pings` and the subscribed users (usernames, as today), one per
  line, 10 per page. The character's aliases (`Aliases: Luci`), when it has any, stay with the header.
- With no subscribers it is the same layout with `Nobody is subscribed to Lucina` as the body (today it shows an
  empty `Users:` line), so the aliases still show.
- Anyone may turn the pages. A click on a character that has been removed since is answered privately
  (`This character doesn't exist anymore`). The buttons hold the character's ID, so a renamed character still works.

### Check wallet (`~checkwallet`, `/checkwallet`) and resources (`~resources`, `/resources`)

- The same format without pagination: the header (`user1's wallet`, `Resources`), a separator, the list one per
  line (`Orbs: 250`; `~hof` or `hof` as today's reply names them for each syntax, with today's hint that `/resource`
  posts one for slash).

### Help (`~help`; there is no `/help`)

- A title (`Commands`), with the two tips under it (underscores for multi-word names; every command is also a slash
  command).
- One part per help section of `COMMANDS` (the general commands, Gacha Currency Commands, and Admin Commands for
  admins only), each after a separator, with a small heading and per command its usage in bold on one line and its
  description on the next.
- Generated from `COMMANDS`, as today, so a new command shows up without touching the layout.

### Scheduled messages

- Coliseum reminder: the text `Coliseum/Aether Raids closes <t:…:R> at <t:…:f>` as a text display.
- Voting Gauntlet, one message per matchup as today: text with both characters, their status and score; then, when
  the Weaker character has trackers, a separator and the mentions (they must still notify); then the two Track
  buttons.

## Non-goals

- Confirmations (`Ping for Lucina has been added`, `Your Orbs has been set to 10`, the admin replies), errors, the
  replies to button clicks, the easter eggs and posted resources stay plain text.
- Empty results other than the scoreboard's and check character's stay a plain sentence, as today: `You are not subscribed to any
  characters`, `Your wallet is empty. Use /setcurrency to add a currency`, `No resources have been set yet`.
- No dropdown on check ping or check character. No pagination on check wallet or resources.
- No DM for `~checkping`.

## Anti-goals

- Mentions that stop notifying. Art pings and Voting Gauntlet trackers exist to notify; a layout that shows the
  mentions but doesn't ping them is a failure even if it looks right.
- A reply that fails to send because it is too long. Today long replies are split at 2000 characters; a layout has
  its own limits (4000 characters of text across a message's text displays, 40 components), and an art ping with
  many subscribers, or a long Voting Gauntlet tracker list, must still go out completely.
- The `~` and slash forms drifting apart in content.

## Constraints

- A Components V2 message has no `content` and no embeds; all text is in text displays. discord.py sets the message
  flag when it sends a `LayoutView`.
- A message can be edited from plain content to a layout, not back. Editing a vote message posted before this
  change into its layout must clear its content.
- In a `LayoutView`, buttons and selects go in an `ActionRow` (or a `Section` accessory); a `View` can't hold a text
  display.
- Persistent: no timeout, a fixed or dynamic `custom_id` (as `view/` does today), registered at startup, so every
  button and dropdown works after a restart. A `custom_id` holds 100 characters at most, which is why the existing
  buttons hold IDs, not names.
- `discord.py` interaction replies fail on `view=None` (see `util.message_util.view_option`).
- `AllowedMentions` still applies: replies keep `ALLOWED_MENTIONS` (no `@everyone`, no roles).
- Project rules in `CLAUDE.md`: services build the reply and never see a message or interaction; the services that
  name a command take the syntax (`slash=False`); both syntaxes covered by tests; `README.md`,
  `docs/manual-test-plan.md` and `CLAUDE.md` updated.

## Decided

- The anatomies above are the user's, as are: the currency dropdown on the scoreboard; pagination for check ping and
  check character only; `/checkping` private and `~checkping` public; the footer `Want to be pinged for X? Use
  /addping X`; the add-character hint depending on whether the user is an admin; help and the scheduled messages in
  layouts; the `~` commands affected too; every layout in a `Container`.
- My calls (the user can override them while reviewing):
  - 10 entries per page for check ping and check character, like the scoreboard; no buttons on a single page.
  - A separator between the list and the controls on the scoreboard, as on check ping.
  - One accent colour for every container, a constant in the code (not a setting), Discord's blurple.
  - The dropdown lists 25 currencies at most, alphabetically, and is shown only when there are at least 2.
  - Aliases stay with the check character header.
  - Empty results other than the scoreboard's and check character's stay plain sentences; check character with no
    subscribers keeps its layout, with `Nobody is subscribed to Lucina` as the body.
  - Anyone may turn the pages of a public `~checkping`, as on the scoreboard; the list is public anyway.
  - The check ping header names the user as the scoreboard does (`get_username`: their global name), so a page
    turned after a restart, which only has the user ID, shows the same header.
  - "The first character" in the art ping footer is the first in the reply's alphabetical order.
  - An art ping in which no name matches a character still doesn't start the cooldown, as today's error doesn't.
  - A dropped vote's message becomes a layout holding only its text (it can't go back to plain content).

## Left to the builder

- How a service hands a layout to the two syntaxes. Today it returns `str | Reply(content, view)`, and
  `legacy.dispatch` and `slash.runner` send it. It must stay testable as text (tests compare reply text
  throughout), and the private replies (`/checkping`, `/artping` with no existing character) need a way to say so.
- How replies longer than a layout allows are split, within the anti-goal above.
- The markdown inside the text displays (headings, bold), within the anatomies above.
- How the dropdown is made persistent (a `DynamicItem` around a `Select`, or a fixed `custom_id` registered once)
  and what its option values hold.
- How the fakes in `tests/fakes.py` represent a layout message.
