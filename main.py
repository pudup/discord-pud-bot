import asyncio
import os
import random
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from pretty_help import DefaultMenu, PrettyHelp
from discord_slash.utils.manage_commands import create_choice, create_option

def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)

prefix = os.getenv("PREFIX")
help_command = commands.DefaultHelpCommand(no_category=f'prefix -> {prefix}')


client = commands.Bot(command_prefix=prefix)
slash = SlashCommand(client=client, sync_commands=True)
menu = DefaultMenu('◀️', '▶️', '❌') # You can copy-paste any icons you want.
client.help_command = PrettyHelp(navigation=menu, color=0x45c6ee)

for file in os.listdir('cogs/'):
    if file.endswith('.py'):
        client.load_extension(f'cogs.{file[:-3]}')


# @client.command(name='reload', hidden=True)
async def load(ctx):
    for files in os.listdir('cogs/'):
        if files.endswith('.py'):
            client.reload_extension(f'cogs.{files[:-3]}')
    respond = await ctx.send("Reloaded all cogs")
    server = ctx.message.guild
    if server:
        await asyncio.sleep(1)
        await ctx.message.delete()
        await respond.delete()

client.run(os.getenv("TOKEN"))
