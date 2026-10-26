Discord community bot tailored to the Fjormcord community

Build with Discord.py and Python 3.x
Bot uses a sqlite database

# Description
A Discord bot that provides various features to your community:
 * Art pinging. See commands below for more details.
 * Notification when Coliseum in Fire Emblem Heroes is closing. Notification will occur 5 hours and 1 hour before closing.

# Commands
You have to type these commands in the channel chat to perform them.
Arguments are separated by spaces, so character and currency names cannot contain spaces. Use underscores for multi-word names, e.g. `Black_Knight`.
A character can also have aliases, other names that work in every command that takes a character, e.g. `Focalors` for `Furina`. Replies always show the character's name.
Character names and aliases are stored with every part capitalized, whatever casing was typed: `black_knight` becomes `Black_Knight`, `m!robin` becomes `M!Robin` and `l'arachel` becomes `L'Arachel`.

| Command                           | Description                                                                                                                                                       |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ~artping <characters...>          | This will ping all users who are subscribed to the one or more provided characters. Multiple characters have to be separated with spaces                          |
| ~addping <character>              | This will subscribe the user to the provided character. The user will be pinged when the artping command is performed with the provided character                 |
| ~removeping <character>           | This will unsubscribe the user from the provided character. The user won't be pinged anymore when the artping command is performed with the provided character    |
| ~checkping                        | This will display all the characters that the user is subscribed to                                                                                               |
| ~addcharacter <character>         | This will add the provided character to the pings. For a non-admin it starts a vote instead (see Configuration); once it passes, the voters are subscribed        |
| ~removecharacter <character>      | This will remove the provided character from the pings. All subscribed users will be unsubscribed from the provided character                                     |
| ~checkcharacter <character>       | This will display the aliases and all the subscribed users of the provided character                                                                              |
| ~addalias <character> <alias>     | This will add another name for the provided character. The alias can be used everywhere the character's name can                                                  |
| ~removealias <character> <alias>  | This will remove the provided alias from the provided character                                                                                                   |
| ~setprimaryname <alias>           | This will make the provided alias the character's name. The old name becomes an alias, and all subscriptions and other aliases are kept                           |
| ~addcurrency <currency>           | This will add the provided currency. Other users can set this currency if they have it.                                                                           |
| ~removecurrency <currency>        | This will remove the provided currency. All users' wallets will be clear when the currency is removed                                                             |
| ~setcurrency <currency> <amount>  | This will set user's provided currency to provided amount                                                                                                         |
| ~clearcurrency <currency>         | This will clear user's provided currency from their wallet                                                                                                        |
| ~checkwallet                      | This will display all the user's currencies and their amount in their wallet                                                                                      |
| ~scoreboard <currency> [page]     | This will display a leaderboard of the provided currency, 10 users per page. Without a page number the first page is shown                                        |
| ~resources                        | This will display the names of all resources                                                                                                                      |
| ~<resource>                       | This will post the provided resource, e.g. ~hof                                                                                                                   |
| ~setresource <resource> <link>    | This will save a resource. A Discord message link saves the text of that message, a website link saves the link                                                   |
| ~removeresource <resource>        | This will remove the provided resource                                                                                                                            |
| ~help                             | This will display an overview of all the available commands                                                                                                       |

# Local setup
1. Create a bot of your own in the [Discord developer portal](https://discord.com/developers/applications), enable the "Message Content Intent" and invite it to a test server.
2. Install the bot and its test dependencies: `python -m venv .venv`, then `.venv/Scripts/python -m pip install -e ".[dev]"` (use `.venv/bin/python` on Linux/macOS).
3. Create `config.ini` in the repository root with your bot's token:
   ```ini
   [discord]
   token=<your bot token>
   ```
4. Run the bot with `.venv/Scripts/python -m fjormcord.bot.artping`. The database (`test.db`) is created on the first start.

Run the tests with `.venv/Scripts/python -m pytest`. They need neither a token nor `config.ini`.

# Configuration
The defaults are in `config.example.ini`, which is committed. `config.ini` is not committed: any property you put there overrides the default.
 * You have to provide your token of Discord bot to the property "discord.token". Only put it in config.ini
 * The database is stored at the path in the property "database.path". A database that doesn't exist yet is created on startup
 * The property "art_ping.cooldown_seconds" (default 1) is how many seconds a user has to wait after using ~artping before they can use it again. Admins don't have to wait, and 0 turns the cooldown off
 * The properties "character_vote.votes_needed" (default 5) and "character_vote.emoji" (default ⭐) control voting: a non-admin's ~addcharacter posts a vote message, and the character is added once that many users (bots excluded) have reacted to it with that emoji, or as soon as an admin has. With fewer than 2 votes needed there are no votes: non-admins add characters directly, like admins. A custom server emoji is written as `<:name:id>`. Open votes are stored in the database, so they survive restarts and don't expire. The bot needs the "Add Reactions" and "Read Message History" permissions in the channels where votes are started
 * Resources copy the text of a Discord message when they are set, so the bot needs "Read Message History" in the channel of that message. Later edits of the message are not followed: set the resource again to refresh it
 * Optionally, you can provide the ID of a channel to property "coliseum_notification_channel_id". The FEH coliseum notifications are sent to this channel, otherwise no notifications will be sent. To copy a channel's ID, enable Developer Mode in Discord (User Settings > Advanced), then right-click the channel and choose "Copy Channel ID"
