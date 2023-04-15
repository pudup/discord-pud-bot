import discord
from discord import app_commands
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

    @app_commands.command(name='catfact', description='This command gives you a random cat fact. Expect repetitions')
    async def catfact(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title=await cat_facts(), color=await color())
        embed.set_author(name=f"Cat fact for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.set_thumbnail(url=await kittenthumb())
        await interaction.response.send_message(embed=embed)


async def setup(client):
    await client.add_cog(Facts(client))
