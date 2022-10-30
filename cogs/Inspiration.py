import discord
from discord.ext import commands
import aiohttp
import random





async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)

async def pickup():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.popcat.xyz/pickuplines") as response:
            json = await response.json()
            pickup = json["pickupline"]

            return pickup


async def quotes():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://zenquotes.io/api/random") as response:
            json = await response.json(content_type='application/json')
            quote = json[0]["q"]
            author = json[0]["a"]
            final = quote + " " + "\n-" + author

            return [quote, author]


class Inspiration(commands.Cog, name='Inspiration', description="quote, pickup"):
    def __init__(self, client):
        self.client = client

    @commands.command(name='quote', brief='Get an inspirational quote', description='This command gives you a random inspirational quote from some random, possibly famous, person. Expect repetitions')
    async def quotey(self, ctx):

        output = await quotes()
        embed = discord.Embed(color=await color())
        embed.set_author(name=output[0])
        embed.description = "-" + output[1]
        await ctx.send(embed=embed)

    @commands.command(name='pickup', brief='Get a 100% success rate pickup line',
                      description='Pick up line number 7 will surprise you')
    async def pickuper(self, ctx):
        output = await pickup()
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"EZ Tang for {ctx.message.author}", icon_url=ctx.author.avatar.url)
        embed.title = output
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Inspiration(client))
