import os
import random
import aiohttp
import discord
from discord.ext import commands, tasks

presents = ["cat toy", "deadMau5", "slinky", "piece of string", "ball of aluminium foil", "pigeon feather",
            "bit of dust"]  # Random games being "played" by the bot in its status
PREFIX = os.getenv("PREFIX")
DEV_ID = os.getenv("DEV_ID")  # If you're making your own bot, use your ID account developer ID/Code here


async def mock(message):
    """Randomises the casing on input text"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.popcat.xyz/mock?text={message}") as response:
            json = await response.json()
            text = json["text"]

            return text


class Events(commands.Cog):
    """A cog that constantly listens for various events that are unrelated to commands"""

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """Is run when the bot starts/logs in"""
        self.change_status.start()
        print(f"Bot is logged in as {self.client.user}")
        try:
            synced_commands = await self.client.tree.sync()
            print(f"Synced {len(synced_commands)} command(s)")
        except Exception as error:
            print(f"Error syncing commands with: {error}")

    @tasks.loop(seconds=20)  # Change the seconds value to change how often it executes
    async def change_status(self):
        """Changes the bot status every X seconds. Uses the presents list from above"""
        await self.client.change_presence(activity=discord.Game(name="with a " + random.choice(presents)))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Executes whenever a new user joins a server that has this bot"""
        await member.send(f'Ello {member}. Welcome to {member.guild}. See what I can do for you with /help')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Executes whenever the bot encounters an error. Seems to only work with prefix commands and not with
        slash commands"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"All my commands are now slash commands.\nTry ```/help```")
        else:
            if "unable to rename file: [Errno 2]" not in str(error):
                await ctx.send("I've encountered an error. Please try again.")
                jaby = await self.client.fetch_user(DEV_ID)
                command = ctx.invoked_with
                await jaby.send("Got an error somewhere using the command: " + str(command) + " >>>> " + str(error))
            else:
                jaby = await self.client.fetch_user(DEV_ID)
                command = ctx.invoked_with
                await jaby.send("Got an error somewhere using the command: " + str(command) + " >>>> " + str(error))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """The bot sends a message to the first text channel when it joins a server"""
        try:
            joinchannel = guild.system_channel
            await joinchannel.send(f'Thanks for inviting me to your server! Use /help to find out how I work')
        except:
            await guild.text_channels[0].send(
                f'Thanks for inviting me to your server! Use /help to find out how I work')

    @commands.Cog.listener()
    async def on_message(self, message):
        """Reads all messages that it can and does things based on what it reads. If you're gon use this, keep it
        polite and privacy-friendly"""
        if message.author == self.client.user:  # This is required. Without this the bot will respond to its own messages
            return

        if "yay" in message.content.lower():
            await message.channel.send(
                f"Yay")


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Events(client))
