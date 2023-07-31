import discord
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
import aiohttp
from utils.utils import color


async def get_kittens():
    """Returns the URL to a random kitten image from randomkittengenerator.com as a string"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.randomkittengenerator.com/") as response:
            text = await response.read()
            soup = BeautifulSoup(text.decode('utf-8'), "html5lib")
            image_maybe = soup.find_all(class_="hot-random-image")
            return image_maybe[0]['src']


async def get_memes():
    """Returns the URL and title to a meme from the popcat API as strings"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://meme-api.com/gimme") as response:
            if response.status == 200:
                json = await response.json()
                meme = json["url"]
                title = json["title"]
            else:
                meme = None
                title = "I have failed you :< Try again later"
            return title, meme


class Images(commands.Cog, name='Images', description="kitten, meme"):
    """A cog for image/picture related commands"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='kitten', description="GITTEN KITTEN")
    async def get_kitten(self, interaction: discord.Interaction) -> None:
        """Responds to the user with a random kitten image"""
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Gitten a Kitten for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.set_image(url=await get_kittens())

        # Sending the embed
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='meme', description="Dankest of memes")
    async def get_meme(self, interaction: discord.Interaction) -> None:
        """Responds to the user with a random meme"""
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        title, meme = await get_memes()  # Get meme strings for embed

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Shitty meme for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.set_footer(text=title)
        embed.set_image(url=meme)

        # Sending the embed
        await interaction.followup.send(embed=embed)


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Images(client))
