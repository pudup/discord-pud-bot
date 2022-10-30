import discord
from discord.ext import commands
import random


async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)

class Utilities(commands.Cog, name='Utilities', description="ping"):
    def __init__(self, client):
        self.client = client


    @commands.command(name='ping', description='This command returns bot latency')
    async def ping(self, ctx):
        embed = discord.Embed(color=await color())
        embed.description = f"```Miau! \nLatency: {round(self.client.latency * 1000)}ms```"
        await ctx.send(embed=embed)

    # @cog_ext.cog_slash(name='ping', description='This command returns bot latency')
    # async def slash_ping(self, ctx):
    #     embed = discord.Embed(color=await color())
    #     embed.description = f"```Miau! \nLatency: {round(self.client.latency * 1000)}ms```"
    #     await ctx.send(embed=embed)



async def setup(client):
    await client.add_cog(Utilities(client))
