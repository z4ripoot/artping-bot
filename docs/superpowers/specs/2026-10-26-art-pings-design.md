# Art pings: design

Describes the bot as built. Characters themselves are covered by the characters and aliases spec.

## Intent

Someone who posts art of a character can notify everyone who wants to see that character's art, without
knowing who they are. Users opt in per character and are mentioned whenever art of it is announced.

## Commands

| Command | Reply on success | Refusals |
|---|---|---|
| `~artping (character name)...` | `Furina, Lucina: <@1> <@2>` | see below |
| `~addping (character name)` | `Ping for Lucina has been added` | `Ping for Lucina already exists` |
| `~removeping (character name)` | `Ping for Lucina has been removed` | `Ping for Lucina doesn't exist` |
| `~checkping` | `Furina, Lucina` | `You are not subscribed to any characters` (a reply, not an error) |

All are open to everyone. Every character name may be an alias and any casing; an unknown one answers
`Character Marth doesn't exist`.

## `~artping`

- Takes one or more character names, separated by spaces.
- The characters are listed alphabetically, each once even when named twice or by several aliases.
- Every user subscribed to at least one of them is mentioned once (`<@id>`), even if subscribed to several.
- Nobody subscribed: `Nobody is subscribed to Lucina`.
- Unknown names are reported in the same reply, before the ping, normalized:
  `No character entry for Marth\nLucina: <@1>`. When none of the names exist, that first line is the whole
  reply (sent as a refusal, so no cooldown starts).
- A reply with many mentions is split into several messages under Discord's limit (command handling spec).
- Cooldown: `art_ping.cooldown_seconds` per user (default 1); admins exempt (command handling spec).

## `~checkping`

Lists the caller's characters by name, alphabetically, comma-separated.

## Data

`PINGS (CHARACTER_ID, USER)`, primary key on both, `ON DELETE CASCADE` from `CHARACTERS`: removing a character
removes its subscriptions. Users are Discord user IDs as text. A passed character vote subscribes its voters
(character votes spec).

## Non-goals

- No pinging of roles or `@everyone`; the client blocks those mentions.
- Users can only manage their own subscriptions.

## Tests

`tests/fjormcord/bot/artping/service/test_art_ping_service.py`; splitting and cooldowns in `test_bot.py`.
