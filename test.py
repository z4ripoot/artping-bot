import discord
import sqlite3
import datetime
from discord.ext import tasks

con = sqlite3.connect("test.db")
cur = con.cursor()

class Client(discord.Client):
    async def on_ready(self):
        print(f'Welcome {self.user}!')
        if not arena_ping_1_hour.is_running():
            arena_ping_1_hour.start()
        if not arena_ping_5_hour.is_running():
            arena_ping_5_hour.start()

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Add character to table of pings
        if message.content.startswith('~addcharacter'):
            character = message.content[14:].title()
            
            try:
                cur.execute('INSERT INTO "Artpings" ("character", "pings") VALUES(?,?)', [character, ''])
                con.commit()
                await message.channel.send(f'{message.content[14:]} added.')
            # In case character already exists in list
            except:
                await message.channel.send(f'{message.content[14:]} is already in the list.')



        # Add user to character ping string
        if message.content.startswith('~addping'):
            character = message.content[9:].title()
            try:
                cur.execute('SELECT Pings FROM "Artpings" WHERE Character = ?', [character])
                temp = cur.fetchone()[0]
                # Double check if user already added this ping
                if str(message.author.id) in temp:
                    await message.channel.send(f'You already have {character} ping added.')
                else:
                    users = temp + str(message.author.id)  + ','
                    cur.execute('UPDATE "Artpings" SET Pings = ? WHERE Character = ?', [users, character])
                    con.commit()
                    await message.channel.send(f'{character} ping added.')
            # In case character does not exist in list
            except:
                await message.channel.send(f'{character} ping does not exist.')



        # Remove this ping for this user
        if message.content.startswith('~removeping'):
            character = message.content[12:].title()
            try:
                cur.execute('SELECT Pings FROM "Artpings" WHERE Character = ?', [character])
                temp = cur.fetchone()[0]
                # Double check if user does not have this ping
                if str(message.author.id) not in temp:
                    await message.channel.send(f'You do not have {character} ping added.')
                else:
                    to_remove = str(message.author.id) + ','
                    users = temp.replace(to_remove, '')
                    cur.execute('UPDATE "Artpings" SET Pings = ? WHERE Character = ?', [users, character])
                    con.commit()
                    await message.channel.send(f'{character} ping removed.')
            # In case character does not exist in list
            except:
                await message.channel.send(f'{character} ping does not exist.')



        # Ping all users with this character ping
        if message.content.startswith('~artping'):

            # Account for multiple characters:
            char_list = []
            chars= message.content[9:]
            temp = ''
            # Add characters to list
            for i in range(len(chars)):
                if chars[i] != ' ' and i == len(chars) - 1:
                    temp += chars[i]
                    char_list.append(temp.title())
                    temp = ''
                elif chars[i] != ' ':
                    temp += chars[i]          
                else:
                    char_list.append(temp.title())
                    temp = ''
            output_characters = ', '.join(char_list)
            output_pings = ''
            # Iterate through multiple characters
            for character in char_list:
                try:
                    cur.execute('SELECT Pings FROM "Artpings" WHERE Character = ?', [character])
                    users = cur.fetchone()[0]
                    check = 0
                    # Add @ in front of all ids
                    for i in range(len(users)):
                        if users[i] == ',':
                            ping = ' <@' + users[check:i] + '>'
                            # Make sure we don't double ping
                            if ping not in output_pings:
                                output_pings += ' <@' + users[check:i] + '>'
                            else:
                                pass
                            check = i + 1
                except:
                    await message.channel.send(f'{character} ping does not exist.')
            print(output_pings)
            await message.channel.send(f'{output_characters}:' + output_pings)

        # Checkping function 
        if message.content.startswith("~checkping"):
            user = '%' + str(message.author.id) + '%'
            cur.execute('SELECT Character FROM "Artpings" WHERE Pings like ?', [user])
            characters = cur.fetchall()
            out = "{name}\'s pings:".format(name = message.author.global_name) + '\n'
            for row in characters:
                out += row[0] + '\n'
            await message.channel.send(out)

        # Help function to detail all the commands
        if message.content.startswith('~help'):
            out = 'Commands (content in brackets is what to add when using command):\n' \
            + '~addcharacter (character name): Add a character to the list of pingable characters \n'\
            + '~addping (character name): Call to add yourself to the pinglist when this character is pinged \n'\
            + '~removeping (character name): Remove yourself from the pinglist of this character \n'\
            + '~artping (character name): Ping users for art of this character \n'\
            + '~checkping: See which characters you are being pinged for \n'
            await message.channel.send(out)

intents = discord.Intents.default()
intents.message_content = True

# Time in UTC
# 1 hour ping
@tasks.loop(time = datetime.time(hour = 22, minute = 0)) 
async def arena_ping_1_hour():
    weekday = datetime.datetime.now().weekday()
    print(weekday)
    if weekday == 0:
        channel = client.get_channel()
        await channel.send("Colosseum/Aether Raids closes in 1 hour.")
    else:
        pass

# 5 hour ping
@tasks.loop(time = datetime.time(hour = 18, minute = 0)) 
async def arena_ping_5_hour():
    weekday = datetime.datetime.now().weekday()
    print(weekday)
    if weekday == 0:
        channel = client.get_channel()
        await channel.send("Colosseum/Aether Raids closes in 5 hour.")
    else:
        pass
     
client = Client(intents=intents)
client.run('')
