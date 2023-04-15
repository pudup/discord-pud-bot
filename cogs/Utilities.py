import discord
from discord import app_commands
from discord.ext import commands
import random


async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)


class Utilities(commands.Cog, name='Utilities', description="ping"):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='ping', description='This command returns bot latency')
    async def ping(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(color=await color())
        embed.description = f"```Miau! \nLatency: {round(self.client.latency * 1000)}ms```"
        await interaction.response.send_message(embed=embed)


async def setup(client):
    await client.add_cog(Utilities(client))
