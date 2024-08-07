import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from utils.utils import color
from cogs.Images import get_cat


async def cat_facts():
    """Returns a random catfact from the 'catfact.ninja' API as a string"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://catfact.ninja/fact") as response:
            if response.status == 200:
                json = await response.json()
                fact = json['fact']
            else:
                fact = "I couldn't think up any new facts for some reason :<"
            return fact


class Facts(commands.Cog, name='Facts', description="catfact"):
    """A cog for fun-fact related commands"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='catfact', description='This command gives you a random cat fact. Expect repetitions')
    async def catfact(self, interaction: discord.Interaction) -> None:
        """The command for random cat facts"""
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        # Building the embed
        embed = discord.Embed(title=await cat_facts(), color=await color())
        embed.set_author(name=f"Cat fact for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.set_thumbnail(url=await get_cat())

        # Sending the embed
        await interaction.followup.send(embed=embed)


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Facts(client))
