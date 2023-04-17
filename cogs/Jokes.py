import discord
from discord import app_commands
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
            if response.status == 200:
                json = await response.json()
                joke = json['joke']
            else:
                joke = "I couldn't think of anything funny :<"
            return joke


async def shower():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.popcat.xyz/showerthoughts") as response:
            if response.status == 200:
                json = await response.json()
                thought = json['result']
            else:
                thought = "I couldn't think of anything :<"
            return thought


class Jokes(commands.Cog, name='Jokes', description="dadjoke, think"):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='dadjoke', description="Get the bestest jokes :>")
    async def dadjoke(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("👨‍👧‍👦")
        to_delete = await interaction.original_response()
        embed = discord.Embed(title=await dad_jokes(), color=await color())
        embed.set_author(name=f"Free smiles for {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed)
        await to_delete.delete()

    @app_commands.command(name='think', description="I think therefore I am")
    async def showerthought(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Thinking...")
        to_delete = await interaction.original_response()
        embed = discord.Embed(title=await shower(), color=await color())
        embed.set_author(name=f"Shower thought for {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed)
        await to_delete.delete()


async def setup(client):
    await client.add_cog(Jokes(client))
