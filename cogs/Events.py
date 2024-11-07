import os
import random
import aiohttp
import discord
from discord.ext import commands, tasks
from utils.utils import color
import aiofiles
from datetime import datetime

presents = ["cat toy", "deadMau5", "slinky", "piece of string", "ball of aluminium foil", "pigeon feather",
            "bit of dust"]  # Random games being "played" by the bot in its status
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
        async with aiofiles.open('debug.txt', mode='a') as log:
            time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            await log.write(f"Bot is logged in as {self.client.user}" + f"-> {time_now}")
            await log.write("\n")
        try:
            synced_commands = await self.client.tree.sync()
            async with aiofiles.open('debug.txt', mode='a') as log:
                await log.write(f"Synced {len(synced_commands)} command(s)")
                await log.write("\n")
        except Exception as error:
            async with aiofiles.open('debug.txt', mode='a') as log:
                await log.write(f"Error syncing commands with: {error}")
                await log.write("\n")
        dev = await self.client.fetch_user(DEV_ID)
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"PyTest results for {dev.name}", icon_url=dev.display_avatar)
        async with aiofiles.open("./tests/results.txt", "r") as results:
            lines = await results.readlines()
            success = True
            description = ""
            for line in lines:
                if "short test summary info" in line:
                    success = False
                    continue
                if not success:
                    if "====" in line:
                        description += line.replace('=', '') + "\n"
                    else:
                        description += line + "\n"
            if success:
                description = "All tests succeeded"
        embed.title = description
        await dev.send(embed=embed)
        async with aiofiles.open('debug.txt', mode='a') as log:
            await log.write("Sent test results")
            await log.write("\n")

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
            await ctx.send("I've encountered an error. Please try again.")
            dev_account = await self.client.fetch_user(DEV_ID)
            command = ctx.invoked_with
            await dev_account.send("Got an error somewhere using the command: " + str(command) + " >>>> " + str(error))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """The bot sends a message to the first text channel when it joins a server"""
        try:
            system_channel = guild.system_channel
            await system_channel.send('Thanks for inviting me to your server! Use /help to find out how I work')
        except (AttributeError, discord.Forbidden):
            for channel in guild.text_channels:
                try:
                    await channel.send('Thanks for inviting me to your server! Use /help to find out how I work')
                    return
                except (AttributeError, discord.Forbidden):
                    continue

    @commands.Cog.listener()
    async def on_message(self, message):
        """Reads all messages that it can and does things based on what it reads. If you're gon use this, keep it
        polite and privacy-friendly"""
        if message.author == self.client.user:
            return
            # This is required. Without this the bot will respond to its own messages

        if "yay" in message.content.lower():
            await message.channel.send(
                f"Yay")


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Events(client))
