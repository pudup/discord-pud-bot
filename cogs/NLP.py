import os
import discord
from discord import app_commands
from discord.ext import commands
import random
import cohere


async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)


API_KEY = os.getenv("API_KEY")


class NLP(commands.Cog, name='NLP', description="ping"):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='chat', description='NLP Model (IN TESTING)')
    @app_commands.describe(text="Ask me a question")
    async def chat(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message("Generating response...")
        to_delete = await interaction.original_response()
        co = cohere.Client(API_KEY)
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=text,
            max_tokens=300,
            temperature=0.9,
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE')
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"{interaction.user} said : {text}", icon_url=interaction.user.display_avatar)
        embed.description = f"{str(response.generations[0].text)}"
        await to_delete.delete()
        await interaction.followup.send(embed=embed)


async def setup(client):
    await client.add_cog(NLP(client))
