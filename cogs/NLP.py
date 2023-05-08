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


class NLP(commands.Cog, name='NLP', description="chat, summer"):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='chat', description='Chat language processing model (beta)')
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

    @app_commands.command(name='summer', description='Summarise text (beta)')
    @app_commands.describe(text="Text to summarise", style="In what style?")
    async def summer(self, interaction: discord.Interaction, text: str, style: str = '') -> None:
        if len(text) < 250:
            await interaction.response.send_message("Your text needs to be longer than 250 characters")
            return
        await interaction.response.send_message("Summarising text...")
        to_delete = await interaction.original_response()
        co = cohere.Client(API_KEY)
        response = co.summarize(
            model='summarize-xlarge',
            text=text,
            temperature=0.9,
            extractiveness='auto',
            length='auto',
            format='auto',
            additional_command=style,
        )
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Summarising text for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.description = f"{str(response.summary)}"
        await to_delete.delete()
        await interaction.followup.send(embed=embed)


async def setup(client):
    await client.add_cog(NLP(client))
