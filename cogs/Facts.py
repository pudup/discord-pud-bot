import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from utils.utils import color


async def cat_facts():
    """Returns a random catfact from the catfact.ninja API as a string"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://catfact.ninja/fact") as response:
            if response.status == 200:
                json = await response.json()
                fact = json['fact']
            else:
                fact = "I couldn't find any new facts for some reason :<"
            return fact


async def kittenthumb():
    """Returns the URL to a random cat image from thecatapi API as a string"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as response:
            text = await response.json()
            return text[0]['url']


class Facts(commands.Cog, name='Facts', description="catfact"):
    """A cog for fun-fact related commands"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='catfact', description='This command gives you a random cat fact. Expect repetitions')
    async def catfact(self, interaction: discord.Interaction) -> None:
        """The command for random cat facts"""
        await interaction.response.send_message("Here comes a free cat fact")
        # This response is here to avoid the discord slash command 3 second timeout.
        # It could prolly be replaced with defer()

        to_delete = await interaction.original_response()  # For deleting the message that was used to avoid timeout

        # Building the embed
        embed = discord.Embed(title=await cat_facts(), color=await color())
        embed.set_author(name=f"Cat fact for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.set_thumbnail(url=await kittenthumb())

        # Sending the embed and deleting the original response
        await interaction.followup.send(embed=embed)
        await to_delete.delete()


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Facts(client))
