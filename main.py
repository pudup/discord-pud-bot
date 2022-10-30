import asyncio
import os
import random
import discord
from discord.ext import commands
from pretty_help import DefaultMenu, PrettyHelp


TOKEN = os.getenv("TOKEN")

def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)

prefix = os.getenv("PREFIX")
help_command = commands.DefaultHelpCommand(no_category=f'prefix -> {prefix}')


client = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())
menu = DefaultMenu('◀️', '▶️', '❌') # You can copy-paste any icons you want.
client.help_command = PrettyHelp(navigation=menu, color=0x45c6ee)

async def load_extensions():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await client.load_extension(f"cogs.{file[:-3]}") # cut off the .py from the file name


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

async def main():
    async with client:
        await load_extensions()
        await client.start(TOKEN)

asyncio.run(main())