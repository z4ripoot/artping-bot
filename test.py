import discord
import sqlite3

con = sqlite3.connect("test.db")
cur = con.cursor()

class Client(discord.Client):
    async def on_ready(self):
        print(f'Welcome {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Add character to table of pings
        if message.content.startswith('~addcharacter'):
            character = message.content[14:]
            
            try:
                cur.execute('INSERT INTO "Artpings" ("character", "pings") VALUES(?,?)', [character, ''])
                con.commit()
                await message.channel.send(f'{message.content[14:]} added.')
            # In case character already exists in list
            except:
                await message.channel.send(f'{message.content[14:]} is already in the list.')



        # Add user to character ping string
        if message.content.startswith('~addping'):
            character = message.content[9:]
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
            character = message.content[12:]
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
            
            character = message.content[9:]
            try:
                cur.execute('SELECT Pings FROM "Artpings" WHERE Character = ?', [character])
                users = cur.fetchone()[0]
                check = 0
                output = ''
                # Add @ in front of all ids
                for i in range(len(users)):
                    if users[i] == ',':
                        output += ' <@' + users[check:i] + '>'
                        check = i + 1
                await message.channel.send(f'{character}:' + output)
            except:
                await message.channel.send(f'{character} ping does not exist.')

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run('')