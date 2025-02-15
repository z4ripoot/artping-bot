Discord community bot tailored to the Fjormcord community

Build with Discord.py and Python 3.x
Bot uses a sqlite database

# Description
A Discord bot that provides various features to your community:
 * Art pinging. See commands below for more details.
 * Notification when Coliseum in Fire Emblem Heroes is closing. Notification will occur 5 hours and 1 hour before closing.

# Commands
You have to type these commands in the channel chat to perform them.
| Command                           | Description                                                                                                                                                       |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ~artping <characters...>          | This will ping all users who are subscribed to the one or more provided characters. Multiple characters have to be separated with spaces                          |
| ~addping <character>              | This will subscribe the user to the provided character. The user will be pinged when the artping command is performed with the provided character                 |
| ~removeping <character>           | This will unsubscribe the user from the provided character. The user won't be pinged anymore when the artping command is performed with the provided character    |
| ~checkping                        | This will display all the characters that the user is subscribed to                                                                                               |
| ~addcharacter <character>         | This will add the provided character to the pings. Other users can now subscribe to the provided character with the ~addping command                              |
| ~removecharacter <character>      | This will remove the provided character from the pings. All subscribed users will be unsubscribed from the provided character                                     |
| ~checkcharacter <character>       | This will display all the subscribed users of the provided character                                                                                              |
| ~addcurrency <currency>           | This will add the provided currency. Other users can set this currency if they have it.                                                                           |
| ~removecurrency <currency>        | This will remove the provided currency. All users' wallets will be clear when the currency is removed                                                             |
| ~setcurrency <currency> <amount>  | This will set user's provided currency to provided amount                                                                                                         |
| ~clearcurrency <currency>         | This will clear user's provided currency from their wallet                                                                                                        |
| ~checkwallet                      | This will display all the user's currencies and their amount in their wallet                                                                                      |
| ~scoreboard <currency>            | This will display a leaderboard of the provided currency. It will display the ranking of users with their amount of the provided currency                         |
| ~help                             | This will display an overview of all the available commands                                                                                                       |

# Configuration
The bot is configurable by changing the properties in config.ini.
 * You have to provide your token of Discord bot to the property "discord.token"
 * You have to provide a path to your database to the property "database.path"
 * Optionally, you can provide the channel name to property "coliseum_notification_channel_name". The FEH coliseum notifications are send to this channel, otherwise no notifications will be sent