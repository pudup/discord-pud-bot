import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from utils.utils import color


async def pickup():
    """Returns a random pickup line from the popcat API as a string"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.popcat.xyz/pickuplines") as response:
            if response.status == 200:
                json = await response.json()
                pickup = json["pickupline"]
            else:
                pickup = "I couldn't think of anything so just be yourself or something for once :>"
            return pickup


async def quotes():
    """Returns a random inspirational quote from the zenquotes API as a string"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://zenquotes.io/api/random") as response:
            json = await response.json(content_type='application/json')
            quote = json[0]["q"]
            author = json[0]["a"]

            return [quote, author]


class Inspiration(commands.Cog, name='Inspiration', description="quote, pickup"):
    """A cog for self-help related commands"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='quote',
                          description='Get a random inspirational quote from some, possibly famous, person.')
    async def quotey(self, interaction: discord.Interaction) -> None:
        """Responds to the user with a random inspirational quote and its author"""
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        output = await quotes()  # Get quote

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=output[0])
        embed.description = "-" + output[1]

        # Sending the embed
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='pickup', description='Get a 100% success rate pickup line')
    async def pickuper(self, interaction: discord.Interaction) -> None:
        """Responds to the user with a random pickup line"""
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.


        output = await pickup()  # Get pickup line

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"EZ Tang for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.title = output

        # Sending the embed
        await interaction.followup.send(embed=embed)


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Inspiration(client))
