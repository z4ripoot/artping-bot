# Manual test plan

Commands to test every branch of the bot by hand in Discord. Expected replies are in `code`; "silence" means the bot
sends nothing at all. Sections 1 to 10 are mostly about the `~` commands, section 11 repeats every command as a
slash command, sections 7 and 12 cover the vote button, and section 13 the Voting Gauntlet scores.

## Setup

- **Invite:** the test bot is invited with the `applications.commands` scope as well as `bot`.
- **Accounts:** **A** is a server admin, **U1** and **U2** are non-admins. A DM with the bot is used for the DM cases.
- **Test `config.ini`:** a copy of `config.example.ini` with these changed:
  ```ini
  [discord]
  token=<test bot token>
  guild_id=<test server id>   ; the slash commands then appear at once, in that server only
  [commands]
  cooldown_seconds=10      ; long enough to test the cooldown by hand
  [character_vote]
  votes_needed=2           ; the smallest value that still has votes
  [tasks]
  coliseum_notification_channel_id=<test channel id>
  voting_gauntlet_channel_id=<test channel id>
  ```
- **Database:** start with a fresh one (delete `test.db`).

Some steps need the bot's log to check the result: 1.4, 1.8, 2.16, 7.12, 7.14, 7.15, 10.3, 11.45, 13.10, 13.11
and 13.12.

## 1. Startup and config

| # | Action | Expected |
|---|---|---|
| 1.1 | Empty `token` in config.ini, then start | Exits with `No Discord token configured. Create config.ini …` |
| 1.2 | Delete `test.db`, then start from another directory (e.g. `cd ~`) | `test.db` is created in the repo root, migrations run, `Bot is running` |
| 1.3 | Remove a key (e.g. `votes_needed`) from config.ini, then start | Exits with `Invalid configuration: No option 'votes_needed' in section: 'character_vote'` (config.example.ini is not read, so it doesn't fill in the key). Put the key back afterwards |
| 1.3a | Rename config.ini, then start | Exits with `Invalid configuration: … config.ini not found. Copy config.example.ini to config.ini and fill in your bot's token`. Rename it back |
| 1.4 | Start with `coliseum_notification_channel_id` and `voting_gauntlet_channel_id` empty | Log warnings `No channel ID is configured for the Coliseum notification task, so it will not be initiated` and the same for the `Voting Gauntlet scores` task |
| 1.5 | Start with `guild_id` set, then type `/` in the test server | All commands are listed (section 11) and each shows once |
| 1.6 | Empty `guild_id`, restart | The commands are registered globally (they can take a while to show up). Guild commands left over from 1.5 show twice until cleared (README, local setup) |
| 1.7 | Set `slash_max_characters=26`, then `0`, then start | Exits with `Invalid configuration: art_ping.slash_max_characters must be between 1 and 25`. Put it back afterwards |
| 1.7a | Set `autocomplete_max_choices=26`, then `0`, then start | Exits with `Invalid configuration: commands.autocomplete_max_choices must be between 1 and 25`. Put it back afterwards |
| 1.8 | Start with a wrong `guild_id`, or without network after login | Log `Syncing the slash commands failed`, the bot keeps running and `~help` still works |

## 2. Message dispatch (`on_message`)

| # | Who | Message | Expected |
|---|---|---|---|
| 2.1 | Webhook in the channel (Channel settings → Integrations → Webhook, post with curl) | `~help` | Silence (bots are ignored) |
| 2.2 | U1 | an image with no text | Silence |
| 2.3 | U1 | `hello` | Silence |
| 2.4 | U1 | `thanks lorenz` / `Thank You Lorenz` | LorenzSmile emoji |
| 2.5 | U1 | `CHROMK` | 3×4 grid of the chromk emoji |
| 2.6 | U1 | `thanks lorenz!` / `chromk please` | Silence (only whole-message matches count) |
| 2.7 | U1 | `~nonexistent` | Silence (no command and no resource) |
| 2.8 | U1 | `~HeLp` | Help (command names ignore case) |
| 2.9 | U1 | `~help extra words` | Help (extra arguments are ignored) |
| 2.10 | U1 | `~helpme` | Silence (exact match only) |
| 2.11 | U1 | `~addcurrency Orbs` (admin-only) | Silence |
| 2.12 | U1 in server | `~help` | No **Admin Commands:** section, but has the "Gacha Currency Commands:" section, the underscore hint and `All commands are also available as slash commands, type /` |
| 2.13 | A in server | `~help` | Includes **Admin Commands:** |
| 2.14 | A in **DM** | `~help`, then `~addcurrency X` | No admin section, and silence on `~addcurrency` (DMs have no permissions) |
| 2.15 | U1 | `~setcurrency @everyone 5` | Reply echoes `@everyone` but **nobody gets pinged** |
| 2.16 | A | Lock the DB: `sqlite3 test.db` → `BEGIN EXCLUSIVE;` (keep it open), then `~addcurrency Lock` | After about 5 s: `Something went wrong while running ~addcurrency`, with a traceback in the log. Then run `ROLLBACK;` |
| 2.17 | U1 | `~artping` followed by about 1900 characters of made-up names (`aaaaaaaaa bbbbbbbbb …`) | The reply (`No character entry for …`) arrives as **2 messages**, split under 2000 characters |

## 3. Cooldown (every command, cooldown 10 s)

Do these after creating the character `Lucina` (step 5.4).

| # | Who | Action | Expected |
|---|---|---|---|
| 3.1 | U1 | `~artping Lucina` twice quickly | 2nd: `You used a command recently. Try again in N seconds` |
| 3.1a | U1 | `~artping Lucina`, then `~checkping` and `~hof` straight away | Both turned down the same way: the cooldown holds back every command |
| 3.2 | U1 | Wait about 9.5 s and retry | `… Try again in 1 second` (singular) |
| 3.3 | U2 | `~artping Lucina` during U1's cooldown | Works (the cooldown is per user) |
| 3.4 | U1 | `~artping Nobody`, then `~artping Lucina` straight away | The 2nd works (a failed command doesn't start the cooldown) |
| 3.5 | U1 | `~artping`, then `~artping Lucina` | The 2nd works (a missing argument doesn't start it either) |
| 3.6 | A | `~artping Lucina` twice quickly | Both work (admins are exempt) |
| 3.7 | U1 | `~artping Lucina`, restart the bot, repeat | Works (cooldowns are in memory) |
| 3.7a | U1 | `Thanks Lorenz` twice quickly | Both answered (easter egg replies are not commands) |
| 3.8 | — | Set `cooldown_seconds=0`, restart, U1 spams `~artping Lucina` | Never turned down |

## 4. Art pings

Preparation: A creates `Lucina` and `Chrom`, and adds the alias `Luci` to Lucina. U1 subscribes to both, U2 to Lucina.

| # | Who | Message | Expected |
|---|---|---|---|
| 4.1 | U1 | `~artping` | `Character name is missing. Usage: ~artping (character name)` |
| 4.2 | U1 | `~artping marth` | `No character entry for Marth` |
| 4.3 | U1 | `~artping black_KNIGHT` | `No character entry for Black_Knight` (normalized) |
| 4.4 | U1 | `~artping Robin` (exists, no subscribers) | `Nobody is subscribed to Robin` |
| 4.5 | U1 | `~artping lucina` | `Lucina: <@U1> <@U2>`, and both get pinged |
| 4.6 | U1 | `~artping Luci` | `Lucina: …` (the alias resolves to the name) |
| 4.7 | U1 | `~artping Lucina Luci` | Lucina is listed once |
| 4.8 | U1 | `~artping Lucina Chrom` | `Chrom, Lucina: …` (sorted), U1 mentioned **once** |
| 4.9 | U1 | `~artping Lucina Marth` | Line 1 `No character entry for Marth`, line 2 the ping |
| 4.10 | U1 | `~addping` | `Character name is missing. Usage: ~addping (character name)` |
| 4.11 | U1 | `~addping Lucina Chrom` | `Only one name is allowed. Use underscores for multi-word names, e.g. Black_Knight` |
| 4.12 | U1 | `~addping marth` | `Character Marth doesn't exist` |
| 4.13 | U2 | `~addping luci` | `Ping for Lucina already exists` (if already subscribed). Otherwise `… has been added` |
| 4.14 | U2 | `~addping Chrom` | `Ping for Chrom has been added` |
| 4.15 | U2 | `~removeping`, `~removeping a b`, `~removeping marth` | Missing-argument, one-name and doesn't-exist errors as above |
| 4.16 | U2 | `~removeping Robin` (not subscribed) | `Ping for Robin doesn't exist` |
| 4.17 | U2 | `~removeping chrom` | `Ping for Chrom has been removed` |
| 4.18 | U2 | `~checkping` | `Lucina` (comma-separated, sorted when there are several) |
| 4.19 | new user / U2 after removing all | `~checkping` | `You are not subscribed to any characters` |

## 5. Characters (admin path)

| # | Who | Message | Expected |
|---|---|---|---|
| 5.1 | A | `~addcharacter` | `Character name is missing. Usage: ~addcharacter (character name)` |
| 5.2 | A | `~addcharacter Black Knight` | Only-one-name error |
| 5.3 | A | `~addcharacter black_KNIGHT` | `Character Black_Knight has been added` |
| 5.4 | A | `~addcharacter m!robin`, `~addcharacter l'arachel`, `~addcharacter Lucina` | `M!Robin`, `L'Arachel`, `Lucina` added |
| 5.5 | A | `~addcharacter LUCINA` | `Character Lucina already exists` |
| 5.6 | A | `~addcharacter luci` (alias) | `Luci is already an alias of Lucina` |
| 5.7 | A / U1 | `~checkcharacter`, `~checkcharacter a b`, `~checkcharacter marth` | Missing-argument, one-name and doesn't-exist errors |
| 5.8 | U1 | `~checkcharacter Black_Knight` (no aliases or users) | `Character entry found for Black_Knight` / `Users: ` (no Aliases line) |
| 5.9 | U1 | `~checkcharacter luci` | Header with **Lucina**, `Aliases: Luci`, `Users: <display names>` |
| 5.10 | A | `~removecharacter` / `a b` / `marth` | Missing-argument, one-name and doesn't-exist errors |
| 5.11 | A | `~removecharacter luci` | `Character Lucina has been removed`. Subscribers' `~checkping` no longer lists it, and `~artping Luci` now says no entry (the alias went too) |

## 6. Aliases (admin)

| # | Message | Expected |
|---|---|---|
| 6.1 | `~addalias` | `Character name is missing. Usage: ~addalias (character name) (alias)` |
| 6.2 | `~addalias Lucina` | `Alias is missing. Usage: ~addalias (character name) (alias)` |
| 6.3 | `~addalias Lucina a b` | Only-one-name error |
| 6.4 | `~addalias marth x` | `Character Marth doesn't exist` |
| 6.5 | `~addalias lucina LUCI` | `Alias Luci has been added to Lucina` |
| 6.6 | `~addalias Luci masked_marth` (alias used as the character) | `Alias Masked_Marth has been added to Lucina` |
| 6.7 | `~addalias Chrom luci` | `Luci is already an alias of Lucina` |
| 6.8 | `~addalias Chrom lucina` | `Character Lucina already exists` |
| 6.9 | `~removealias` / `~removealias Lucina` / `~removealias a b c` / `~removealias marth x` | The same argument and doesn't-exist errors |
| 6.10 | `~removealias Chrom luci` | `Luci is not an alias of Chrom` |
| 6.11 | `~removealias Lucina masked_marth` | `Alias Masked_Marth has been removed from Lucina` |
| 6.12 | `~setprimaryname` | `Alias is missing. Usage: ~setprimaryname (alias)` |
| 6.13 | `~setprimaryname a b` / `~setprimaryname marth` | One-name error / `Character Marth doesn't exist` |
| 6.14 | `~setprimaryname Lucina` | `Lucina is already the primary name` |
| 6.15 | `~setprimaryname luci` | `Luci is now the primary name; Lucina has become an alias`. `~checkcharacter Lucina` shows the header `Luci`, `Aliases: Lucina`, and the same users |

## 7. Character votes (non-admin `~addcharacter`, `votes_needed=2`)

Votes are cast with the Vote button. "Clicks" are button clicks; a click's reply is ephemeral (only the clicker sees it).

| # | Action | Expected |
|---|---|---|
| 7.1 | U1 in **DM**: `~addcharacter Marth` | `Votes can only be started in a server` |
| 7.2 | U1: `~addcharacter Lucina` (exists) | `Character Lucina already exists` (no vote) |
| 7.3 | U1: `~addcharacter marth` | Only the bot's message `Vote to add Marth. Votes needed: 2`, with a button `Vote (0/2)` showing ⭐. The bot adds no reaction and sends no other reply |
| 7.4 | U1 reacts with ⭐ or 👍 on the vote message | Nothing happens (reactions don't count) |
| 7.5 | U1 clicks the button | Ephemeral `Your vote for Marth has been added`; the label becomes `Vote (1/2)` |
| 7.6 | U1 clicks again | Ephemeral `Your vote for Marth has been taken back`; the label is `Vote (0/2)` again |
| 7.7 | U1 and U2 click | The message is edited to `Character Marth has been added` and loses its button. U1 and U2 both have Marth in `~checkping`. U2's click got `Your vote for Marth has been added` |
| 7.8 | U1: `~addcharacter ike` **twice** → two vote messages. U1 and U2 click the 1st | The 1st becomes `…has been added`, the 2nd `Character Ike has already been added`, and neither has a button |
| 7.9 | U1: `~addcharacter roy`. **A** clicks | Passes at once (an admin's vote). A is subscribed to Roy (U1 is not, as U1 didn't click) |
| 7.10 | U1: `~addcharacter eliwood` (2 votes). A runs `~addcharacter eliwood` | A gets `Character Eliwood has been added`, and both vote messages are edited to `…has already been added` without a button |
| 7.11 | U1: `~addcharacter hector`. A: `~addalias Lucina hector`. U2 clicks the vote | U2 gets an ephemeral `Hector is already an alias of Lucina`, and the vote message is edited to that text without a button. The vote is dropped |
| 7.12 | U1: `~addcharacter lyn`, then **delete** the vote message. A: `~addcharacter lyn` | Added, with no errors in the log about fetching the deleted vote (it was dropped on delete) |
| 7.13 | U1: `~addcharacter ephraim`, U1 clicks. Stop the bot, U2 tries to click (`This interaction failed`), start the bot, U2 clicks | The vote and U1's click survived the restart; U2's click now passes it (button votes survive restarts) |
| 7.14 | U1: `~addcharacter eirika`. Stop the bot, delete the vote message, start | Log: `The message of vote … is gone, dropping the vote` |
| 7.15 | U1: `~addcharacter seliph`. Remove the bot's **Read Message History** in that channel, restart | Log warning `Can't read the message of vote …`; the vote is kept. Clicks still work. Restore the permission and restart: no warning |
| 7.16 | U1: `~addcharacter alm`, U1 clicks. Stop the bot, set `votes_needed=1`, start | The vote passes at startup (`Character Alm has been added`) |
| 7.17 | U1: `~addcharacter celica`. Stop the bot, set `votes_needed=3`, start | At startup the message is re-rendered: `Vote to add Celica. Votes needed: 3` and `Vote (0/3)`. Put `votes_needed` back to 2 |
| 7.18 | Set `votes_needed=1`, restart. U1: `~addcharacter lucius` | `Character Lucius has been added` straight away (no vote). Put it back to 2 |
| 7.19 | Set `emoji=<:yourEmoji:id>` (a custom emoji in the server), restart, start a vote | The button shows the custom emoji |
| 7.20 | A clicks a vote button, then U1 starts another vote for the same name and A clicks that too | The 1st click passes the vote; the second vote was closed with it, so there is nothing to click |

## 8. Gacha currency

| # | Who | Message | Expected |
|---|---|---|---|
| 8.1 | A | `~addcurrency` / `~addcurrency a b` | Missing-argument / one-name error |
| 8.2 | A | `~addcurrency orbs` | `Currency orbs has been added` (**not** normalized) |
| 8.3 | A | `~addcurrency ORBS` | `Currency orbs already exists` |
| 8.4 | U1 | `~setcurrency` | `Currency name is missing. Usage: ~setcurrency (currency name) (amount)` |
| 8.5 | U1 | `~setcurrency orbs` | `Amount is missing. Usage: …` |
| 8.6 | U1 | `~setcurrency orbs 1 2` | Only-one-name error |
| 8.7 | U1 | `~setcurrency orbs abc` / `orbs 1.5` | `Failed to set currency. Please enter a valid amount for your orbs.` |
| 8.8 | U1 | `~setcurrency gems abc` (unknown + invalid) | The **amount** error (the amount is checked first) |
| 8.9 | U1 | `~setcurrency orbs -1` | `… The amount can't be negative` |
| 8.10 | U1 | `~setcurrency orbs 9223372036854775808` | `… The amount is too large` |
| 8.11 | U1 | `~setcurrency orbs 9223372036854775807` | Set to that amount |
| 8.12 | U1 | `~setcurrency gems 5` | `Currency gems doesn't exist` |
| 8.13 | U1 | `~setcurrency ORBS 100`, then `~setcurrency orbs 250` | `Your orbs has been set to 100`, then `… to 250` (overwrites) |
| 8.14 | U1 | `~setcurrency orbs +5` / `orbs 1_000` | Accepted as 5 / 1000 (Python `int()` takes these) |
| 8.15 | U1 | `~clearcurrency` / `a b` / `gems` | Missing-argument / one-name / doesn't-exist errors |
| 8.16 | U2 | `~clearcurrency orbs` (never set) | `You don't have any orbs set` |
| 8.17 | U1 | `~clearcurrency orbs` | `Your orbs has been cleared` |
| 8.18 | U2 | `~checkwallet` (empty) | `Your wallet is empty. Use ~setcurrency to add a currency` |
| 8.19 | U1 | Set `orbs` and `feathers` → `~checkwallet` | `User <display name>'s wallet:` then `feathers: …`, `orbs: …` (sorted) |
| 8.20 | U1 | `~scoreboard` | `Currency name is missing. Usage: ~scoreboard (currency name) (optional page number)` |
| 8.21 | U1 | `~scoreboard orbs 1 2` / `~scoreboard orbs abc` | Only-one-name error (both) |
| 8.22 | U1 | `~scoreboard gems` | `Currency gems doesn't exist` |
| 8.23 | U1 | `~scoreboard feathers` (A adds `~addcurrency feathers`, nobody has set it) | `Nobody has set their feathers yet` |
| 8.24 | U1 | `~scoreboard orbs` (U1 and U2 have set it) | `Scoreboard for orbs:` / `1. … (amount)` in descending order, no page info, no "next page" line |
| 8.25 | U1 | `~scoreboard orbs 0` / `orbs 2` | `Page 0 doesn't exist. The scoreboard for orbs has 1 pages` |
| 8.26 | — | Seed fake users (below), then `~scoreboard orbs` | `(page 1/2)` header, ranks 1–10, `Use ~scoreboard orbs 2 for the next page`. Fake IDs show as `Unknown user (<id>)` |
| 8.27 | U1 | `~scoreboard orbs 2` | `(page 2/2)`, ranks starting at 11, no next-page line |
| 8.28 | A | `~removecurrency` / `a b` / `gems` | Missing-argument / one-name / doesn't-exist errors |
| 8.29 | A | `~removecurrency ORBS` | `Currency orbs has been removed`. U1's `~checkwallet` no longer shows orbs |

Seed for 8.26 (run while the bot is stopped, or between commands):

```sql
-- sqlite3 test.db
INSERT INTO GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT)
SELECT (SELECT GACHA_CURRENCY_ID FROM GACHA_CURRENCY WHERE NAME='orbs'), 1000 + value, value
FROM generate_series(1, 11);   -- older sqlite3: use 11 separate INSERTs
```

## 9. Resources

| # | Who | Message | Expected |
|---|---|---|---|
| 9.1 | U1 | `~setresource hof https://example.com` | Silence (admin only) |
| 9.2 | A | `~setresource` / `~setresource hof` | `Resource name is missing. Usage: …` / `Link is missing. Usage: …` |
| 9.3 | A | `~setresource hof a b` | Only-one-name error |
| 9.4 | A | `~setresource h@f https://x.com` | `Resource names can only contain letters, digits, _ and -` |
| 9.5 | A | `~setresource help https://x.com` / `HELP` / `~help` | `~help is a command, so it can't be a resource` |
| 9.6 | A | `~setresource hof www.example.com` | `That isn't a link to a Discord message or a website` |
| 9.7 | A | `~setresource guide https://example.com/guide` | `Resource guide has been set`. `~guide` posts the link |
| 9.8 | A | `~setresource ~hof <https://discord.com/channels/…/…/…>` (copied link of a text message, in `<>`) | `Resource hof has been set` |
| 9.9 | A | The same with the link changed to `ptb.discord.com`, `canary.discord.com`, `discordapp.com` | All accepted |
| 9.10 | A | A link whose message ID is wrong (change the last digit) | `Couldn't read that message. Check the link, and that the bot can read that channel` |
| 9.11 | A | A link to a message in a channel the bot can't see | Same "Couldn't read" error |
| 9.12 | A | A link to an image-only message, or a forwarded message | `That message has no text` |
| 9.13 | U1 | `~hof`, `~HOF`, `~hof extra words` | All post the stored text |
| 9.14 | A | Source message contains `@everyone` and `<@U2>`: set it, then U1 runs `~hof` | The text is shown, **nobody is pinged** |
| 9.15 | A | Edit the source message, then U1 runs `~hof` | Still the old text (a snapshot). After running `~setresource` again → the new text |
| 9.16 | A | Source message over 2000 characters (Nitro), set it, then `~hof` | Posted as 2 or more messages |
| 9.17 | A | `~setresource HOF https://example.com` (existing, different case) | Overwrites it, and `~resources` now lists `~HOF` |
| 9.18 | U1 | `~resources` with none, then with some | `No resources have been set yet` / `Resources: ~guide, ~HOF` (sorted) |
| 9.19 | A | `~removeresource` / `a b` / `h@f` | Missing-argument / one-name / invalid-name errors |
| 9.20 | A | `~removeresource nope` | `Resource nope doesn't exist` |
| 9.21 | A | `~removeresource ~hof` | `Resource HOF has been removed`. `~hof` → silence |

## 10. Coliseum reminder (runs Mondays at 18:00 and 22:00 UTC)

| # | Setup | Expected |
|---|---|---|
| 10.1 | Channel ID set, bot running on a Monday through 18:00 or 22:00 UTC | Message in the channel: `Coliseum/Aether Raids closes <t:…:R> at <t:…:f>`. The timestamp shows 23:00 UTC in your local time |
| 10.2 | Same, on a non-Monday at those times | Nothing |
| 10.3 | Channel ID set to a channel the bot can't see (or a wrong ID) | At the trigger time, log error `Channel … not found. Task will be skipped` |
| 10.4 | Disconnect the network briefly so `on_ready` fires again | No `RuntimeError` about the task already running, and no duplicate reminders (nor duplicate Voting Gauntlet scores, section 13) |
| 10.5 | Channel empty | See 1.4. No reminders |

To test the reminder without waiting for Monday, temporarily change the time constants and the `weekday() == 0` check
in `coliseum.py`. Don't commit that change.

## 11. Slash commands

Every case of sections 4 to 9 also holds for the slash command; what differs is listed here. Errors are ephemeral
(only the person who ran the command sees them), successful replies are public. Options autocomplete from the
database. Run each command as the account named in the section it comes from.

| # | Who | Command | Expected |
|---|---|---|---|
| 11.1 | U1 | Type `/` | The admin commands (`removecharacter`, `addalias`, `removealias`, `setprimaryname`, `addcurrency`, `removecurrency`, `setresource` and `removeresource`) aren't listed for U1; A sees them all. There is no `/help` |
| 11.2 | A | Type `/` | All commands of the README table, plus `/resource`, `/lorenz` and `/chromk`, each with a description |
| 11.3 | U1 | `/addping character:Lucina` | Public `Ping for Lucina has been added`. Autocomplete suggested `Lucina` while typing `lu` (names and aliases) |
| 11.3a | U1 | Set `autocomplete_max_choices=2`, restart, type `/addping character:` with more than 2 characters, then type `l` | At most 2 suggestions, the first names alphabetically; `l` (and `L`) narrows them to names starting with L. Put it back to 20 |
| 11.4 | U1 | `/addping character:black knight` (with a space) | The name is `Black_Knight`: `Character Black_Knight doesn't exist` (or, if it exists, the ping is added) |
| 11.5 | U1 | `/addping character:marth` | Ephemeral `Character Marth doesn't exist` |
| 11.6 | U1 | `/addping character:Lucina` again | Ephemeral `Ping for Lucina already exists` |
| 11.7 | U1 | `/removeping character:Lucina`, then again | `Ping for Lucina has been removed`, then ephemeral `Ping for Lucina doesn't exist` |
| 11.8 | U1 | `/checkping` | `Lucina` / `You are not subscribed to any characters` |
| 11.9 | U1 | `/artping character:Lucina` | `Lucina: <@U1> <@U2>`, the subscribers are pinged |
| 11.10 | U1 | `/artping character:Lucina character2:Chrom character3:Luci` | One line per character, sorted, Lucina once; U1 mentioned once |
| 11.11 | U1 | `/artping character:Lucina character2:Marth` | The ping and the line `No character entry for Marth` |
| 11.12 | U1 | `/artping`, then `~checkping` or `/checkping` (cooldown 10 s) | The 2nd: `You used a command recently. Try again in N seconds` (ephemeral for the slash one): one cooldown for every command of both syntaxes. A failed attempt doesn't start it, and A is never held back |
| 11.13 | U1 | `/artping` | The options go up to `character10` (`slash_max_characters=10`), and there is no `character11`. Set it to 2 and restart: only `character` and `character2` |
| 11.14 | A | `/addcharacter character:black knight` | `Character Black_Knight has been added` (deferred, so the reply may take a moment) |
| 11.15 | A | `/addcharacter character:Black_Knight` | `Character Black_Knight already exists`. The deferred reply follows the defer, so it is public rather than ephemeral |
| 11.16 | U1 | `/addcharacter character:marth2` | A vote message as in 7.3, sent by the bot as a reply to the command. The votes work as in section 7 |
| 11.17 | U1 in **DM** | `/addcharacter character:x` | `Votes can only be started in a server` |
| 11.18 | A in **DM** | Type `/` | The admin commands aren't offered (they are server-only) |
| 11.19 | U1 | `/checkcharacter character:luci` | The header with `Lucina`, `Aliases: Luci` and the users |
| 11.20 | A | `/removecharacter character:luci` | `Character Lucina has been removed` |
| 11.21 | A | `/addalias character:Lucina alias:luci`, `/removealias …`, `/setprimaryname alias:luci` | The same replies as 6.5, 6.11 and 6.15 |
| 11.22 | U1 | Run any admin command by typing it out (an admin has hidden the permission in the server settings, to test the check: Server settings → Integrations → the bot → allow the command for everyone) | Ephemeral `This command is for admins only`. Restore the permission afterwards |
| 11.23 | A | `/addcurrency currency:orbs`, then again | `Currency orbs has been added`, then `Currency orbs already exists` |
| 11.24 | U1 | `/setcurrency currency:orbs amount:-1` | Discord refuses the option (minimum 0) |
| 11.25 | U1 | `/setcurrency currency:orbs amount:100` | `Your orbs has been set to 100` |
| 11.26 | U1 | `/setcurrency currency:orbs amount:9223372036854775808` | Ephemeral `… The amount is too large` (or Discord refuses the number) |
| 11.27 | U1 | `/setcurrency currency:gems amount:5` | Ephemeral `Currency gems doesn't exist` |
| 11.28 | U1 | `/clearcurrency currency:orbs`, then again | `Your orbs has been cleared`, then ephemeral `You don't have any orbs set` |
| 11.29 | U2 | `/checkwallet` (empty) | `Your wallet is empty. Use /setcurrency to add a currency` (the slash form) |
| 11.30 | U1 | `/checkwallet` with two currencies set | `User <display name>'s wallet:` and the sorted lines |
| 11.31 | U1 | `/scoreboard currency:orbs` | Scoreboard for orbs, with the usernames resolved |
| 11.32 | U1 | `/scoreboard currency:orbs page:0` | Discord refuses the option (minimum 1) |
| 11.33 | U1 | `/scoreboard currency:orbs page:5` | Ephemeral `Page 5 doesn't exist. The scoreboard for orbs has N pages` |
| 11.34 | U1 | `/scoreboard currency:orbs` with the 11 seeded users (8.26) | `(page 1/2)` and `Use /scoreboard currency:orbs page:2 for the next page`; `page:2` shows page 2 |
| 11.35 | A | `/removecurrency currency:orbs` | `Currency orbs has been removed` |
| 11.36 | A | `/setresource name:guide link:https://example.com/guide` | `Resource guide has been set` (deferred) |
| 11.37 | A | `/setresource name:help link:https://x.com`, `name:h@f …`, `name:my guide …` (space), `link:www.example.com` | The errors of 9.4 to 9.6 (`~help is a command, so it can't be a resource`, the letters-digits rule for the `@` and the space, and the link error). The command defers, so they follow the defer's visibility (public) |
| 11.38 | A | `/setresource` with a Discord message link, an unreadable link and an image-only message | `Resource … has been set`, `Couldn't read that message…`, `That message has no text`, as in 9.8 to 9.12 |
| 11.39 | U1 | `/resource name:guide` | Posts the stored text; autocomplete suggests `guide` |
| 11.40 | U1 | `/resource name:nope` | Ephemeral `Resource nope doesn't exist` (where `~nope` is silent) |
| 11.41 | A | A resource whose source message contains `@everyone` and `<@U2>`; U1 runs `/resource` | The text is shown, **nobody is pinged** |
| 11.42 | U1 | `/resources`, with none and with some | `No resources have been set yet` / `Resources: guide, HOF (post one with /resource)` |
| 11.43 | A | `/removeresource name:guide`, then again | `Resource guide has been removed`, then ephemeral `Resource guide doesn't exist` |
| 11.44 | U1 | `/lorenz`, wait out the cooldown, `/chromk` | The LorenzSmile emoji, the 3×4 chromk grid; public. Like every command they start the cooldown |
| 11.45 | A | Lock the DB as in 2.16, then `/addcurrency currency:Lock` | After about 5 s: ephemeral `Something went wrong while running /addcurrency`, with a traceback in the log. Then `ROLLBACK;` |
| 11.46 | U1 | `/resource` on a resource of over 2000 characters (9.16) | Posted as 2 or more messages |

## 12. Converting a ⭐ vote (the first start after the button was released)

Needs a database with an open reaction vote: use the previous release (or `git stash` the button code), start a
vote with `~addcharacter conv1`, have U1 react with ⭐ (the bot adds its own ⭐ too), then start this version. The
vote row has `USES_BUTTON = 0` (`sqlite3 test.db "select message_id, uses_button from character_vote"`).

| # | Setup | Expected |
|---|---|---|
| 12.1 | One ⭐ vote with U1's reaction, `votes_needed=2` | At startup the message is edited to `Vote to add Conv1. Votes needed: 2` with a `Vote (1/2)` button. `uses_button` is 1, and U1 is a stored voter: U1 clicking now takes the vote back (`… has been taken back`) |
| 12.2 | Restart the bot | Nothing changes and no voter is lost (a converted vote isn't converted twice) |
| 12.3 | A ⭐ vote with ⭐ from U1 and U2, `votes_needed=2` | Passes during the conversion: `Character … has been added`, U1 and U2 subscribed, no button |
| 12.4 | A ⭐ vote with an admin's ⭐ only | Passes during the conversion, and the admin is subscribed |
| 12.5 | A ⭐ vote with a 👍 only, and with the bot's own ⭐ only | Converted with `Vote (0/2)`: other emoji and the bot's reaction don't count |
| 12.6 | A ⭐ vote whose message was deleted while the bot was offline | Dropped with the log line of 7.14 |
| 12.7 | A ⭐ vote and Read Message History removed | Log warning `Can't read the message of vote …`, kept unconverted; restored and restarted, it converts |

## 13. Voting Gauntlet scores (hourly at 5 past, UTC, while a round runs)

The bot reads the official page (https://support.fire-emblem-heroes.com/voting_gauntlet/current). A live gauntlet
only runs a few days a month, so test with the saved pages instead: temporarily change `voting_gauntlet.py` so that

- `POSTING_TIMES` is every minute: `[time(hour=h, minute=m, tzinfo=timezone.utc) for h in range(24) for m in range(60)]`
- `fetch_page` returns `112, Path("tests/fjormcord/bot/artping/voting_gauntlet_112_round_3.html").read_text("utf-8")`
  (an absolute path if the bot isn't started from the repository root)
- `now` returns a fixed time: `datetime(2026, 10, 2, 12, tzinfo=timezone.utc)` is in round 1 (4 matchups),
  `datetime(2026, 10, 6, 12, …)` in the final round (1 matchup, Edelgard against Dimitri) and
  `datetime(2026, 10, 7, 5, …)` after the end

and restart after each change. Don't commit that change. 13.1 needs a real gauntlet.

| # | Setup | Expected |
|---|---|---|
| 13.1 | Unchanged code, during a real gauntlet round, at 5 past the hour | One message per matchup in the site's order, e.g. `Edelgard (Stronger)` / `123,456` / `Dimitri (Weaker)` / `98,765`, each with the buttons `Track Edelgard` and `Track Dimitri`. Outside a round: nothing |
| 13.2 | `now` in round 1 | 4 matchup messages, labelled Stronger and Weaker (or Same for both when neither is behind), with a `Track <name>` button per character |
| 13.3 | U1 clicks `Track Theodora` (Weaker) | Ephemeral `You now track Theodora. You'll be pinged every hour Theodora is Weaker`. The next minute's message for that matchup ends with `<@U1>`, and U1 is pinged |
| 13.4 | U1 clicks `Track Edelgard` under Theodora's matchup | Ephemeral `You now track Edelgard instead of Theodora`. The next messages no longer mention U1 there (Edelgard is Stronger) |
| 13.5 | U1 clicks `Track Edelgard` again | Ephemeral `You no longer track Edelgard` |
| 13.6 | U1 and U2 track the same Weaker character | The message mentions both, once each |
| 13.7 | U1 tracks a Weaker character, stop the bot, U1 clicks a button (`This interaction failed`), start it, clicks again | The click works after the restart (the buttons are rebuilt from their `custom_id`), and the tracking survived it |
| 13.8 | U1 tracks Dimitri, then `now` in the final round | The final round's single message mentions U1 under Dimitri (tracking lasts across rounds) |
| 13.9 | Then `now` after the end | No messages. `sqlite3 test.db "select * from voting_gauntlet_tracker"` is empty, and clicks on the old buttons answer `This Voting Gauntlet has ended` |
| 13.10 | `fetch_page` returns `113` with the same page, after U1 tracked something in 112 | The trackers of 112 are gone; old 112 buttons answer `This Voting Gauntlet has ended`, the new messages track in 113 |
| 13.11 | `fetch_page` raises `aiohttp.ClientError()`, or returns a page with the `tournaments-art` classes changed (`normal` → `ahead`) | Log `Voting Gauntlet scores could not be read. Task will be skipped` with a traceback, no messages; the next minute tries again (the loop keeps running) |
| 13.12 | `voting_gauntlet_channel_id` set to a channel the bot can't see | Log error `Channel … not found. Task will be skipped` |
| 13.13 | U1 runs `~artping …` straight after clicking a Track button | Works: clicks are not commands and start no cooldown |

## Not testable by hand

These branches are covered by the unit tests instead:

- A failing `vote_message.edit` (only logs a warning).
- Two button clicks racing to pass the same vote.
- A converted ⭐ vote that gains a reaction between its fetch and its conversion.
