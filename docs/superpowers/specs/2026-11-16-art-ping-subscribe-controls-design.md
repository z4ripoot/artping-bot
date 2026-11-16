# Subscribe controls under art pings

## Intent

Readers of an art ping should be able to subscribe to the pinged characters straight from the ping, without typing
`/addping`.

## What gets built

`art_ping_service.do_art_ping` adds controls for the characters that exist (the ones in the heading, alphabetically)
as the reply layout's `rows`. Both `/artping` and `~artping` get them, since the reply is built there.

- **1-5 characters:** one row with a `SubscribeButton` per character (the existing button, `subscribe:<character ID>`).
- **More than 5:** one multi-select dropdown, `SubscribeSelect` (new, in `view/subscribe_view.py`), with fixed
  `custom_id` `subscribe_select`. Its options are the characters, with the character ID as value, and
  `max_values` = the number of options. Discord takes at most 25 options, so a larger `~artping` lists the first 25
  alphabetically (`/artping` takes 25 characters at most anyway).
- **No character exists:** no controls (the reply is a `CommandError`, as now).

The footer hint changes when controls are shown (`~addping` in the `~` syntax):

- 1 character: `Want to be pinged for Lucina? Use /addping Lucina or click the button below`
- 2-5: `Want to be pinged for Lucina? Use /addping Lucina or click one of the buttons below to subscribe to the
  corresponding character`
- more than 5: `Want to be pinged for Lucina? Use /addping Lucina or pick characters from the menu below to subscribe
  to them`

A long ping split by `split_layout` keeps the controls on its last message, as it already does with rows.

## Behaviour of the dropdown

A pick subscribes the clicker to every picked character and answers privately with one reply: the pings added, and
the characters they already followed (`Ping for Lucina, Chrom has been added` / `You are already subscribed to
Robin`). Characters removed since the ping are reported as no longer existing; the rest still go through. A new
service function, `art_ping_service.subscribe_many(user_id, character_ids)`, holds this. Like the Subscribe button it
is not a command (no cooldown), anyone may use it, it works after a restart (a `DynamicItem` registered in
`setup_hook`, rebuilt from the message's select in `from_custom_id`), and it is answered through
`interaction_util.answer_click`.

## Approaches

1. **Multi-select dropdown (chosen):** several characters in one pick; fewest clicks.
2. Single-select dropdown: simpler, but one menu opening per character.
3. Up to 25 buttons in 5 rows: no dropdown needed, but a wall of buttons under an already long mention list.

## Calls made by Claude (correct if wrong)

- `~artping` gets the controls too.
- The message is not edited after a pick, so the clicker keeps seeing their picks in the menu until they reload;
  only they see it, and editing a ping message just to clear it isn't worth the risk to the mentions.
- Non-goals: unsubscribing from the ping, controls on the `Nobody is subscribed` reply being different (it gets them
  like any other).

## Tests

Service tests for the rows and each hint variant (1, 5, 6 characters, `~` and slash), the 25-option cap, and
`subscribe_many` (new, already subscribed, deleted character); view tests for the select after a restart.
