import os
import random
import discord
from discord.ext import commands, tasks

presents = ["cat toy", "deadMau5", "slinky"]
prefix = os.getenv("PREFIX")



async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)

class Events(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_ready(self):
        self.change_status.start()
        print(f"Bot is logged in as {self.client.user}")



    @tasks.loop(seconds=20)
    async def change_status(self):
        await self.client.change_presence(activity=discord.Game(name="with a " + random.choice(presents)))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.send(f'Ello {member}. Welcome to {member.guild}. See what I can do for you with {os.getenv("PREFIX")}help')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"I don't know this command. See my list of commands with ```{os.getenv('PREFIX')}help```")
        else:
            await ctx.send("I've encountered an error. Please try again.")
            print(error)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            joinchannel = guild.system_channel
            await joinchannel.send(f'Thanks for inviting me to your server! Use {prefix}help to find out how I work')
        except:
            await guild.text_channels[0].send(
                "Thanks for inviting me to your server! Use ##help to find out how I work")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return

        server = message.guild

        if "scammar" in message.content.lower():
            await message.channel.send(
                f"{message.author.mention} " + random.choice(["IBS-D", "Borger", "2-13 Phoenix"]))

        if "yay" in message.content.lower():
            await message.channel.send(
                f"Yay")



def setup(client):
    client.add_cog(Events(client))
