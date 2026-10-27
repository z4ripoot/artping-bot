# Easter eggs: design

Describes the bot as built.

## Intent

Community in-jokes: a few exact phrases get a custom-emoji reply from the bot.

## Behavior

| Message (whole message, any casing) | Reply |
|---|---|
| `thank you lorenz`, `thanks lorenz` | the `lorenz_smile` emoji |
| `chromk` | a picture of 12 emoji pieces, `chromk_1` to `chromk_12`, in 3 lines of 4 |

- Only the whole message matches: `thanks lorenz!` or `ok thanks lorenz` get no reply.
- Messages from bots, this one included, are ignored. Easter eggs are answered before command dispatch; no phrase starts with
  `~`, so a message is never both.
- Any user can trigger them, without a cooldown.

## Configuration

The emoji are custom server emoji, set under `[emoji]` in `config.example.ini` as `<:Name:id>`. A server with
other emoji overrides them in `config.ini`. The bot must be in the server that owns the emoji for them to
render.

## Adding one

Add the phrase, lowercased, to `EASTER_EGG_REPLIES` in `easter_eggs.py`; new emoji go into `[emoji]`.

## Tests

`tests/fjormcord/bot/artping/test_easter_eggs.py`, plus one dispatch test in `test_bot.py`.
