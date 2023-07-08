import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from utils.utils import color


async def dad_jokes():
    """Returns a random dad joke from the icanhazdadjoke API as a string"""
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
    """Returns a random shower thought from the popcat API as a string. The API pulls it from r/showerthoughts.
    This command might break after Reddit implements its ridiculous API pricing"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.popcat.xyz/showerthoughts") as response:
            if response.status == 200:
                json = await response.json()
                thought = json['result']
            else:
                thought = "I couldn't think of anything :< Try again later"
            return thought


class Jokes(commands.Cog, name='Jokes', description="dadjoke, think"):
    """A cog for humour related commands"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='dadjoke', description="Get the bestest jokes :>")
    async def dadjoke(self, interaction: discord.Interaction) -> None:
        """Responds to the user with a random dad joke"""
        await interaction.response.defer(ephemeral=True, thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        # Building the embed
        embed = discord.Embed(title=await dad_jokes(), color=await color())
        embed.set_author(name=f"Free smiles for {interaction.user}", icon_url=interaction.user.display_avatar)

        # Sending the embed
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='think', description="I think therefore I am")
    async def showerthought(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        # Building the embed
        embed = discord.Embed(title=await shower(), color=await color())
        embed.set_author(name=f"Shower thought for {interaction.user}", icon_url=interaction.user.display_avatar)

        # Sending the embed and deleting the original response
        await interaction.followup.send(embed=embed)


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Jokes(client))
