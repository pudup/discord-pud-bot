import discord
from discord.ext import commands
import aiohttp
import random





async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)

async def quotes():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://zenquotes.io/api/random") as response:
            json = await response.json(content_type='application/json')
            quote = json[0]["q"]
            author = json[0]["a"]
            final = quote + " " + "\n-" + author

            return [quote, author]


class Inspiration(commands.Cog, name='Inspiration', description="quote"):
    def __init__(self, client):
        self.client = client

    @commands.command(name='quote', brief='Get an inspirational quote', description='This command gives you a random inspirational quote from some random, possibly famous, person. Expect repetitions')
    async def quotey(self, ctx):

        output = await quotes()
        embed = discord.Embed(color=await color())
        embed.set_author(name=output[0])
        embed.description = "-" + output[1]
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Inspiration(client))
