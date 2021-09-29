import discord
from discord.ext import commands
import aiohttp
import random
from discord_slash import cog_ext, SlashContext

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


class Jokes(commands.Cog, name='Jokes', description="dadjoke"):
    def __init__(self, client):
        self.client = client

    @commands.command(name='dadjoke', brief='Get the bestest jokes :>', description="I will respond with the world's best jokes")
    async def dadjoke(self, ctx):
        embed = discord.Embed(title=await dad_jokes(), color=await color())
        embed.set_author(name=f"Free smiles for {ctx.message.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)



def setup(client):
    client.add_cog(Jokes(client))
