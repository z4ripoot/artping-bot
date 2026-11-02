# Gacha currency: design

Describes the bot as built.

## Intent

Players keep track of how much gacha currency (orbs, primogems, ...) they've saved and compare it with each
other on a scoreboard. Admins decide which currencies exist; each user sets their own amounts.

## Commands

| Command | Who | Reply on success |
|---|---|---|
| `~setcurrency (currency name) (amount)` | everyone | `Your Orbs has been set to 500` |
| `~clearcurrency (currency name)` | everyone | `Your Orbs has been cleared` |
| `~checkwallet` | everyone | see below |
| `~scoreboard (currency name) (optional page number)` | everyone | see below |
| `~addcurrency (currency name)` | admins | `Currency Orbs has been added` |
| `~removecurrency (currency name)` | admins | `Currency Orbs has been removed` |

The user commands are listed in `~help` under `Gacha Currency Commands:`.

## Rules

- **Names:** matched ignoring case and replied with the stored name, but, unlike characters, **not
  normalized**: stored as typed when added. An unknown currency answers `Currency Orbs doesn't exist` (as
  typed). Adding an existing one answers `Currency Orbs already exists`.
- **Amounts:** a whole number from 0 up to 2^63 − 1 (SQLite's largest integer). Refusals:
  `Failed to set currency. Please enter a valid amount for your Orbs.`,
  `Failed to set currency. The amount can't be negative`, `Failed to set currency. The amount is too large`.
  The amount is checked before the currency, so a bad amount is reported even for an unknown currency.
- **Setting** replaces the previous amount.
- **Clearing** an amount that isn't set answers `You don't have any Orbs set`.
- **Removing a currency** clears it from every wallet.

## `~checkwallet`

```
User Alice's wallet:
Orbs: 500
Primogems: 12000
```

Currencies alphabetically; the display name is the caller's. An empty wallet answers
`Your wallet is empty. Use ~setcurrency to add a currency`.

## `~scoreboard`

- Highest amount first, 10 users per page; without a page number, page 1.
- Header `Scoreboard for Orbs:` for a single page, `Scoreboard for Orbs (page 2/3):` otherwise.
- Lines `1. Alice (500)`; ranks run on across pages and ties get consecutive ranks.
- Pages before the last end with `Use ~scoreboard Orbs 3 for the next page`.
- Only the users on the shown page are looked up by name (cache first, Discord request on a miss,
  `Unknown user (id)` when not found).
- Nobody has an amount: `Nobody has set their Orbs yet`.
- A page out of range: `Page 4 doesn't exist. The scoreboard for Orbs has 3 pages`.
- A second argument that isn't a number answers the one-name hint, since it's most likely a name with spaces.

## Data

`GACHA_CURRENCY (GACHA_CURRENCY_ID, NAME UNIQUE COLLATE NOCASE)` and
`GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT)`, primary key on currency and user, `ON DELETE CASCADE`
from the currency.

## Known quirks

- A one-page scoreboard asked for page 2 answers `... has 1 pages`.

## Tests

`tests/fjormcord/bot/artping/service/test_currency_service.py`.
