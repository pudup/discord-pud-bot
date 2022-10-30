import discord
from discord.ext import commands
import aiohttp
import random

async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)

async def cat_facts():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://catfact.ninja/fact") as response:
            json = await response.json()
            fact = json['fact']
            return fact

async def kittenthumb():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as response:
            text = await response.json()
            return text[0]['url']


class Facts(commands.Cog, name='Facts', description="catfact"):
    def __init__(self, client):
        self.client = client

    @commands.command(name='catfact', brief='Get a cat fact', description='This command gives you a random cat fact. Expect repetitions')
    async def catfact(self, ctx):
        embed = discord.Embed(title=await cat_facts(), color=await color())
        embed.set_author(name=f"Cat fact for {ctx.message.author}", icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=await kittenthumb())
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Facts(client))