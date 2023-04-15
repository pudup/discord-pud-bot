import discord
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
import aiohttp
import random


async def kittenthumb():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as response:
            text = await response.json()
            return text[0]['url']


async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)


async def get_kittens():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://www.randomkittengenerator.com/") as response:
            text = await response.read()
            soup = BeautifulSoup(text.decode('utf-8'), "html5lib")
            image_maybe = soup.find_all(class_="hot-random-image")
            return image_maybe[0]['src']


async def get_memes():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.popcat.xyz/meme") as response:
            json = await response.json()
            meme = json["image"]
            title = json["title"]
            return title, meme


class Images(commands.Cog, name='Images', description="kitten, meme"):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='kitten', description="GITTEN KITTEN")
    async def getkitten(self, interaction: discord.Interaction) -> None:
        # server = ctx.message.guild
        # message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + "Gitten Kitten...")
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Gitten a Kitten for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.set_image(url=await get_kittens())
        # await ctx.send("The kittens are on strike :<. Here's a cat (maybe kitten :>) image instead")
        await interaction.response.send_message(embed=embed)
        # await message.delete()

    @app_commands.command(name='meme', description="Dankest of memes")
    async def get_meme(self, interaction: discord.Interaction) -> None:
        # message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + "Fetching shitty meme...")
        title, meme = await get_memes()
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Shitty meme for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.set_footer(text=title)
        embed.set_image(url=meme)
        await interaction.response.send_message(embed=embed)
        # await message.delete()


async def setup(client):
    await client.add_cog(Images(client))
