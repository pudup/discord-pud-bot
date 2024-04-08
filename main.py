import asyncio
import os
import discord
from discord.ext import commands
from pretty_help import PrettyHelp

TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")

client = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())
client.help_command = PrettyHelp(color=discord.Color.from_rgb(69, 198, 238), no_category='Help', dm_help=True)


async def load_extensions():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await client.load_extension(f"cogs.{file[:-3]}")  # cut off the .py from the file name


# @client.command(name='reload', hidden=True)
async def load(ctx):
    for files in os.listdir('cogs/'):
        if files.endswith('.py'):
            await client.reload_extension(f'cogs.{files[:-3]}')
    respond = await ctx.send("Reloaded all cogs")
    server = ctx.message.guild
    if server:
        await asyncio.sleep(1)
        await ctx.message.delete()
        await respond.delete()


# @client.command(name='announce', hidden=True)
async def announce(ctx):
    for guild in ctx.bot.guilds:
        await guild.text_channels[0].send("")


async def main():
    async with client:
        await load_extensions()
        await client.start(TOKEN)


asyncio.run(main())
