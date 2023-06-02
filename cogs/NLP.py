import os
import discord
from discord import app_commands
from discord.ext import commands
import cohere
import aiohttp
from utils.utils import color

# Put your LLM API keys here
API_KEY = os.getenv("API_KEY")  # Cohere
GPT_KEY = os.getenv("GPT_KEY")  # Chatgpt (rapidapi)


class NLP(commands.Cog, name='NLP', description="chatgpt, chat, summer"):
    """A cog for natural language processing commands. Just LLM APIs for now"""

    def __init__(self, client):
        self.client = client

    @app_commands.command(name='chat', description='Chat language processing model (beta)')
    @app_commands.describe(text="Ask me a question")
    async def chat(self, interaction: discord.Interaction, text: str) -> None:
        """The cohere chat response command. Has pretty reasonable values set"""
        await interaction.response.send_message("Generating response...")
        # This response is here to avoid the discord slash command 3 second timeout.
        # It could prolly be replaced with defer()

        to_delete = await interaction.original_response()  # For deleting the message that was used to avoid timeout

        # Cohere settings and input
        co = cohere.Client(API_KEY)
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=text,
            max_tokens=300,
            temperature=0.9,
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE')

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"{interaction.user} said : {text}", icon_url=interaction.user.display_avatar)
        embed.description = f"{str(response.generations[0].text)}"

        # Sending the embed and deleting the original response
        await to_delete.delete()
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='summer', description='Summarise text (beta)')
    @app_commands.describe(text="Text to summarise", style="In what style?")
    async def summer(self, interaction: discord.Interaction, text: str, style: str = '') -> None:
        """Summarises text that the user inputs and responds with it. User input needs to be 250 characters or more"""
        if len(text) < 250:  # Checking if the user input is not large enough
            await interaction.response.send_message("Your text needs to be longer than 250 characters")
            return
        await interaction.response.send_message("Summarising text...")
        # This response is here to avoid the discord slash command 3 second timeout.
        # It could prolly be replaced with defer()

        to_delete = await interaction.original_response()  # For deleting the message that was used to avoid timeout

        # Cohere settings and input
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

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Summarising text for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.description = f"{str(response.summary)}"

        # Sending the embed and deleting the original response
        await to_delete.delete()
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='chatgpt', description='OpenAI\'s ChatGPT')
    @app_commands.describe(text="Say anything")
    async def chatgpt(self, interaction: discord.Interaction, text: str) -> None:
        """A command that basically accesses ChatGPT API and responds with it"""
        await interaction.response.send_message("Generating response...")
        # This response is here to avoid the discord slash command 3 second timeout.
        # It could prolly be replaced with defer()

        to_delete = await interaction.original_response()  # For deleting the message that was used to avoid timeout

        # Setting up the ChatGPT API
        url = "https://openai80.p.rapidapi.com/chat/completions"
        headers = {
            "Accept-Encoding": "gzip, deflate",
            "content-type": "application/json",
            "X-RapidAPI-Key": GPT_KEY,
            "X-RapidAPI-Host": "openai80.p.rapidapi.com"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": text,
                }
            ]
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url=url, json=payload) as response:
                if response.status == 200:
                    json = await response.json()
                    chat_response = json['choices'][0]['message']['content']
                else:
                    chat_response = "I encountered an error, prolly too many requests. Try again later or try /chat"

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"{interaction.user} said : {text}", icon_url=interaction.user.display_avatar)
        embed.description = f"{str(chat_response)}"

        # Sending the embed and deleting the original response
        await to_delete.delete()
        await interaction.followup.send(embed=embed)


async def setup(client):  # Required function to enable this cog
    await client.add_cog(NLP(client))
