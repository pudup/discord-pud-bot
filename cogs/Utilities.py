import discord
from discord import app_commands
from discord.ext import commands
from utils.utils import color


class Utilities(commands.Cog, name='Utilities', description="ping"):
    """A cog for bot checkup utilities"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='ping', description='This command returns bot latency')
    async def ping(self, interaction: discord.Interaction) -> None:
        """Responds to the user with the bots ping in milliseconds"""
        await interaction.response.send_message("Pong!")
        # This response is here to avoid the discord slash command 3 second timeout.
        # It could prolly be replaced with defer()

        to_delete = await interaction.original_response()  # For deleting the message that was used to avoid timeout

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.description = f"```Miau! \nLatency: {round(self.client.latency * 1000)}ms```"

        # Sending the embed and deleting the original response
        await interaction.followup.send(embed=embed)
        await to_delete.delete()


async def setup(client):  # Required function to enable this cog
    await client.add_cog(Utilities(client))
