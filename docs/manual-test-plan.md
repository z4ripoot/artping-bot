# Manual test plan

Commands to test every branch of the bot by hand in Discord. Expected replies are in `code`; "silence" means the bot
sends nothing at all.

## Setup

- **Accounts:** **A** is a server admin, **U1** and **U2** are non-admins. A DM with the bot is used for the DM cases.
- **Test `config.ini`:**
  ```ini
  [discord]
  token=<test bot token>
  [art_ping]
  cooldown_seconds=10      ; long enough to test the cooldown by hand
  [character_vote]
  votes_needed=2           ; the smallest value that still has votes
  [tasks]
  coliseum_notification_channel_id=<test channel id>
  ```
- **Database:** start with a fresh one (delete `test.db`).

Some steps need the bot's log to check the result: 2.16, 7.11, 7.13, 7.14, 7.19 and 10.3.

## 1. Startup and config

| # | Action | Expected |
|---|---|---|
| 1.1 | Empty `token` in config.ini, then start | Exits with `No Discord token configured. Create config.ini …` |
| 1.2 | Delete `test.db`, then start from another directory (e.g. `cd ~`) | `test.db` is created in the repo root, migrations run, `Bot is running` |
| 1.3 | Remove a key (e.g. `votes_needed`) from **both** ini files, then start | Crashes at startup (`NoOptionError`). Put the key back afterwards |
| 1.4 | Start with `coliseum_notification_channel_id` empty | Log warning `No channel ID is configured for Coliseum notifications…` |

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
| 2.12 | U1 in server | `~help` | No **Admin Commands:** section, but has the "Gacha Currency Commands:" section and the underscore hint |
| 2.13 | A in server | `~help` | Includes **Admin Commands:** |
| 2.14 | A in **DM** | `~help`, then `~addcurrency X` | No admin section, and silence on `~addcurrency` (DMs have no permissions) |
| 2.15 | U1 | `~setcurrency @everyone 5` | Reply echoes `@everyone` but **nobody gets pinged** |
| 2.16 | A | Lock the DB: `sqlite3 test.db` → `BEGIN EXCLUSIVE;` (keep it open), then `~addcurrency Lock` | After about 5 s: `Something went wrong while running ~addcurrency`, with a traceback in the log. Then run `ROLLBACK;` |
| 2.17 | U1 | `~artping` followed by about 1900 characters of made-up names (`aaaaaaaaa bbbbbbbbb …`) | The reply (`No character entry for …`) arrives as **2 messages**, split under 2000 characters |

## 3. Cooldown (`~artping` only, cooldown 10 s)

Do these after creating the character `Lucina` (step 5.4).

| # | Who | Action | Expected |
|---|---|---|---|
| 3.1 | U1 | `~artping Lucina` twice quickly | 2nd: `You used ~artping recently. Try again in N seconds` |
| 3.2 | U1 | Wait about 9.5 s and retry | `… Try again in 1 second` (singular) |
| 3.3 | U2 | `~artping Lucina` during U1's cooldown | Works (the cooldown is per user) |
| 3.4 | U1 | `~artping Nobody`, then `~artping Lucina` straight away | The 2nd works (a failed command doesn't start the cooldown) |
| 3.5 | U1 | `~artping`, then `~artping Lucina` | The 2nd works (a missing argument doesn't start it either) |
| 3.6 | A | `~artping Lucina` twice quickly | Both work (admins are exempt) |
| 3.7 | U1 | `~artping Lucina`, restart the bot, repeat | Works (cooldowns are in memory) |
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

| # | Action | Expected |
|---|---|---|
| 7.1 | U1 in **DM**: `~addcharacter Marth` | `Votes can only be started in a server` |
| 7.2 | U1: `~addcharacter Lucina` (exists) | `Character Lucina already exists` (no vote) |
| 7.3 | U1: `~addcharacter marth` | Only the bot's message `Vote to add Marth: react with ⭐. Votes needed: 2`, with the bot's own ⭐. No other reply |
| 7.4 | Nobody reacts, or U1 reacts with 👍 | Nothing happens (the bot's ⭐ and other emoji don't count) |
| 7.5 | U1 reacts ⭐ | Nothing (1 of 2) |
| 7.6 | U2 reacts ⭐ | The message is edited to `Character Marth has been added`. U1 and U2 both have Marth in `~checkping` |
| 7.7 | U1: `~addcharacter ike` **twice** → two vote messages. U1 ⭐ on the 1st and U2 ⭐ on the 1st | The 1st becomes `…has been added`, the 2nd `Character Ike has already been added` |
| 7.8 | U1: `~addcharacter roy`. **A** reacts ⭐ | Passes at once (an admin's vote). A is subscribed to Roy |
| 7.9 | U1: `~addcharacter eliwood` (2 votes). A runs `~addcharacter eliwood` | A gets `Character Eliwood has been added`, and both vote messages are edited to `…has already been added` |
| 7.10 | U1: `~addcharacter hector`. A: `~addalias Lucina hector`. U2 reacts ⭐ on the vote | The vote is edited to `Hector is already an alias of Lucina` and dropped (a later ⭐ does nothing) |
| 7.11 | U1: `~addcharacter lyn`, then **delete** the vote message. A: `~addcharacter lyn` | Added, with no errors in the log about fetching the deleted vote (it was dropped on delete) |
| 7.12 | U1: `~addcharacter ephraim`. Stop the bot, have U1 and U2 react ⭐, start the bot | On startup the vote passes (`check_open_votes`) |
| 7.13 | U1: `~addcharacter eirika`. Stop the bot, delete the vote message, start | Log: `The message of vote … is gone, dropping the vote` |
| 7.14 | U1: `~addcharacter seliph`. Remove the bot's **Read Message History** in that channel. U2 reacts ⭐ | Log warning `Can't read the message of vote …`, no change. Restore the permission, U1 reacts ⭐ → passes |
| 7.15 | U1 reacts ⭐ on an ordinary (non-vote) message | Nothing |
| 7.16 | U1 reacts ⭐ and removes it again, then U2 reacts ⭐ | Doesn't pass (reactions are counted live, so U1's removed one doesn't count) |
| 7.17 | Set `votes_needed=1`, restart. U1: `~addcharacter alm` | `Character Alm has been added` straight away (no vote) |
| 7.18 | Set `emoji=<:yourEmoji:id>` (a custom emoji in the server), restart, start a vote | The vote message uses the custom emoji, and only that emoji counts |
| 7.19 | (Optional) A voter leaves the server before another reaction | That vote still counts toward the total, but not as an admin's (log `Failed to fetch member …`) |

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
| 10.4 | Disconnect the network briefly so `on_ready` fires again | No `RuntimeError` about the task already running, and no duplicate reminders |
| 10.5 | Channel empty | See 1.4. No reminders |

To test the reminder without waiting for Monday, temporarily change the time constants and the `weekday() == 0` check
in `coliseum.py`. Don't commit that change.

## Not testable by hand

These branches are covered by the unit tests instead:

- A failing `vote_message.edit` or `add_reaction` (both only log a warning).
- Two reaction events racing to pass the same vote.
