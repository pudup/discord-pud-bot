import os
import discord
from discord import app_commands
from discord.ext import commands
import cohere
from utils.utils import color

# Put your LLM API keys here
COHERE_API_KEY = os.getenv("COHERE_API_KEY")  # Cohere


class NLP(commands.Cog, name='NLP', description="chat, summer"):
    """A cog for natural language processing commands. Just LLM APIs for now"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='chat', description='Chat language processing model')
    @app_commands.describe(text="Say anything")
    async def chat(self, interaction: discord.Interaction, text: str) -> None:
        """The cohere chat response command. Has pretty reasonable values set"""
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        # Cohere settings and input
        co = cohere.Client(COHERE_API_KEY)
        response = co.chat(message=text)

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"{interaction.user} said : {text}", icon_url=interaction.user.display_avatar)
        embed.description = response.text

        # Sending the embed
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='summer', description='Summarise text')
    @app_commands.describe(text="Text to summarise", style="In what style?")
    async def summer(self, interaction: discord.Interaction, text: str, style: str = '') -> None:
        """Summarises text that the user inputs and responds with it."""
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        # Cohere settings and input
        co = cohere.Client(COHERE_API_KEY)
        if style:
            response = co.chat(message=f"Summarise the following text: '{text}' in the style of {style}")
        else:
            response = co.chat(message=f"Summarise the following text: {text}")

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Summarising text for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.description = response.text

        # Sending the embed
        await interaction.followup.send(embed=embed)


async def setup(client):  # Required function to enable this cog
    await client.add_cog(NLP(client))
