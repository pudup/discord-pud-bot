import discord
from discord import app_commands
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

    @app_commands.command(name='quote',
                          description='Get a random inspirational quote from some, possibly famous, person.')
    async def quotey(self, interaction: discord.Interaction) -> None:
        output = await quotes()
        embed = discord.Embed(color=await color())
        embed.set_author(name=output[0])
        embed.description = "-" + output[1]
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='pickup', description='Get a 100% success rate pickup line')
    async def pickuper(self, interaction: discord.Interaction) -> None:
        output = await pickup()
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"EZ Tang for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.title = output
        await interaction.response.send_message(embed=embed)


async def setup(client):
    await client.add_cog(Inspiration(client))
