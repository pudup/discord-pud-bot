import discord
from discord.ext import commands
import aiohttp
import random

async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)


async def dad_jokes():
    headers = {
        'Accept': 'application/json',
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get("https://icanhazdadjoke.com/") as response:
            json = await response.json()
            joke = json['joke']
            return joke

async def shower():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.popcat.xyz/showerthoughts") as response:
            json = await response.json()
            thought = json['result']
            return thought


class Jokes(commands.Cog, name='Jokes', description="dadjoke, think"):
    def __init__(self, client):
        self.client = client

    @commands.command(name='dadjoke', brief='Get the bestest jokes :>', description="I will respond with the world's best jokes")
    async def dadjoke(self, ctx):
        embed = discord.Embed(title=await dad_jokes(), color=await color())
        embed.set_author(name=f"Free smiles for {ctx.message.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='think', brief='Shower thoughts from around the globe', description="I think therefore I am")
    async def showerthought(self, ctx):
        embed = discord.Embed(title=await shower(), color=await color())
        embed.set_author(name=f"Shower thought for {ctx.message.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Jokes(client))
