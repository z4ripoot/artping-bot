Discord community bot tailored to the Fjormcord community

Build with Discord.py and Python 3.x
Bot uses a sqlite database

# Description
A Discord bot that provides various features to your community:
 * Art pinging. See commands below for more details.
 * Notification when Coliseum in Fire Emblem Heroes is closing. Notification will occur 5 hours and 1 hour before closing.
 * Notification when Divine Games in Fire Emblem Heroes is closing (at 00:00 GMT+1 between Saturday and Sunday). Notification will occur 5 hours and 1 hour before closing.
 * Hourly Voting Gauntlet scores of Fire Emblem Heroes while a round runs: one message per matchup, each character labelled Stronger, Weaker or Same as in the game. Under every matchup are two buttons, "Track <name>": click one to track that character and be pinged every hour it is Weaker. You track one side of a matchup (clicking the other button switches), clicking again stops tracking, and tracking lasts across rounds until the gauntlet ends.

# Commands
You can type these commands in the channel chat to perform them. Every one of them is also a slash command (see below).
Arguments are separated by spaces, so character and currency names cannot contain spaces. Use underscores for multi-word names, e.g. `Black_Knight`.
A character can also have aliases, other names that work in every command that takes a character, e.g. `Focalors` for `Furina`. Replies always show the character's name.
Character names and aliases are stored with every part capitalized, whatever casing was typed: `black_knight` becomes `Black_Knight`, `m!robin` becomes `M!Robin` and `l'arachel` becomes `L'Arachel`.

| Command                           | Description                                                                                                                                                       |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ~artping <characters...>          | This will ping all users who are subscribed to the one or more provided characters. Multiple characters have to be separated with spaces                          |
| ~addping <character>              | This will subscribe the user to the provided character. The user will be pinged when the artping command is performed with the provided character                 |
| ~removeping <character>           | This will unsubscribe the user from the provided character. The user won't be pinged anymore when the artping command is performed with the provided character    |
| ~checkping                        | This will display all the characters that the user is subscribed to, 10 per page. `/checkping` shows them only to the user                                         |
| ~addcharacter <character>         | This will add the provided character to the pings. For a non-admin it starts a vote instead (see Configuration); once it passes, the voters are subscribed        |
| ~removecharacter <character>      | This will remove the provided character from the pings. All subscribed users will be unsubscribed from the provided character                                     |
| ~checkcharacter <character>       | This will display the aliases and all the subscribed users of the provided character, 10 per page                                                                 |
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
| ~closingtimes                     | This will display when Coliseum/Aether Raids and Divine Games close next, the soonest first                                                                       |
| ~sendreminders                    | Admin only, for debugging: this will send the Coliseum and Divine Games reminders to their channels now, whatever the day, and reply which were sent              |
| ~sendvotinggauntlet               | Admin only, for debugging: this will post the Voting Gauntlet scores now, as the hourly post does (only while a round runs), and reply what was posted          |

# Slash commands
Every command above is also available as a slash command with the same name, e.g. `/addping`; type `/` to see them. Discord shows the arguments and their descriptions, autocompletes character, currency and resource names, and hides the admin commands from users who aren't admins. The `~` commands keep working exactly as before, and both share the same cooldown.
 * Slash arguments can contain spaces, which become underscores: `/addping Black Knight` is `~addping Black_Knight`.
 * `/artping` has a `character` argument and optional `character2`, `character3`, ... arguments, up to the number in the property "art_ping.slash_max_characters" (default 10, at most 25; applied on restart). To ping more characters at once, use `~artping`.
 * `/resource <name>` posts a resource, as `~<resource>` does, and `/resources` lists them.
 * `/lorenz` and `/chromk` post the same emoji as the "thanks lorenz" and "chromk" messages.
 * Errors are only shown to the user who made them. Admin commands can only be used in a server, and for a non-admin they answer "This command is for admins only".
 * `/help` shows the overview of `~help` in slash syntax, only to the user who asked. `/lorenz` and `/chromk` aren't listed.

# Local setup
1. Create a bot of your own in the [Discord developer portal](https://discord.com/developers/applications), enable the "Message Content Intent" and invite it to a test server with the `bot` and `applications.commands` scopes. The slash commands need the second one: a bot that was invited before they existed (such as the production bot) has to be invited again, which keeps its settings.
2. Install the bot and its test dependencies: `python -m venv .venv`, then `.venv/Scripts/python -m pip install -e ".[dev]"` (use `.venv/bin/python` on Linux/macOS).
3. Copy `config.example.ini` to `config.ini` in the repository root, and fill in your bot's token and your test server's ID:
   ```ini
   [discord]
   token=<your bot token>
   guild_id=<your test server's ID>
   ```
   With `guild_id` set the slash commands are registered in that server only, and show up at once; without it they are registered globally, which can take a while to show up. Only use it for a bot of your own: starting the bot with a `guild_id` also clears the global slash commands of that application. To remove commands left in a server after you stop using `guild_id`, send an empty list to Discord: `curl -X PUT -H "Authorization: Bot <your bot token>" -H "Content-Type: application/json" -d "[]" https://discord.com/api/v10/applications/<application ID>/guilds/<server ID>/commands`.
4. Run the bot with `.venv/Scripts/python -m fjormcord.bot.artping`. The database (`test.db`) is created on the first start.

Run the tests with `.venv/Scripts/python -m pytest`. They need neither a token nor `config.ini`.

# Configuration
The bot reads only `config.ini`, which is not committed. It must hold every property: the bot doesn't start when the file or a property is missing, and says which. `config.example.ini`, which is committed, is a complete example to copy; the values below in brackets are the example's.
 * You have to provide your token of Discord bot to the property "discord.token". Only put it in config.ini
 * The database is stored at the path in the property "database.path". A database that doesn't exist yet is created on startup
 * The property "discord.guild_id" (example: empty) is for development, see Local setup. Leave it empty in production, which registers the slash commands globally
 * The property "commands.cooldown_seconds" (example: 1) is how many seconds a user has to wait after using a command, `~` or slash, before they can use another one. Only a command that worked starts it, admins don't have to wait, and 0 turns the cooldown off
 * The property "commands.autocomplete_max_choices" (example: 20, between 1 and 25) is how many names the autocomplete of a slash command argument offers at most
 * The property "art_ping.slash_max_characters" (example: 10, between 1 and 25) is how many characters /artping takes. Changing it takes effect after a restart
 * The properties "character_vote.votes_needed" (example: 5) and "character_vote.emoji" (example: ⭐) control voting: a non-admin's ~addcharacter or /addcharacter posts a vote message with a Vote button (showing the emoji and the count, e.g. "Vote (1/5)"), and the character is added once that many users have voted, or as soon as an admin clicks it. The user who started the vote has voted already, so the count starts at 1. Clicking again takes your vote back. With fewer than 2 votes needed there are no votes: non-admins add characters directly, like admins. A custom server emoji is written as `<:name:id>`. It must be a valid Unicode emoji or a custom emoji of a server the bot is in, or votes can't be started. Open votes and their voters are stored in the database, so they survive restarts and don't expire. Clicks made while the bot is offline fail and can be repeated. A changed "character_vote.votes_needed" shows on a vote message at its next click, which also passes the vote if it has enough votes now. The bot needs the "Read Message History" permission in the channels where votes are started, to update the other vote messages for a name once it is added
 * Resources copy the text of a Discord message when they are set, so the bot needs "Read Message History" in the channel of that message. Later edits of the message are not followed: set the resource again to refresh it
 * Optionally, you can provide the ID of a channel to property "tasks.coliseum_notification_channel_id" (example: empty). The FEH coliseum notifications are sent to this channel, otherwise no notifications will be sent. To copy a channel's ID, enable Developer Mode in Discord (User Settings > Advanced), then right-click the channel and choose "Copy Channel ID"
 * Optionally, you can provide the ID of a channel to property "tasks.divine_games_notification_channel_id" (example: empty). The FEH Divine Games notifications are sent to this channel, otherwise no notifications will be sent
 * Optionally, you can provide the ID of a channel to property "tasks.voting_gauntlet_channel_id" (example: empty). While a Voting Gauntlet round runs, the scores of every matchup are posted there every hour, at 5 minutes past, read from the official site (https://support.fire-emblem-heroes.com/voting_gauntlet/current). Between rounds and outside the event nothing is sent. Empty sends no scores. The site has no API, so a change to its page can break this; the bot then logs an error and skips the hour. The status comes from the site, which shows a character as behind or not: behind is Weaker, and the other side is Stronger, or both are Same when neither is behind. Trackers are stored in the database and removed once the final round has ended
