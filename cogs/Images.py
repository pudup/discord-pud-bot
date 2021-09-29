import os
import aiofiles
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
import aiohttp
import random

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
        async with session.get("https://meme-api.herokuapp.com/gimme/1") as response:
            json = await response.json()
            meme = json['memes'][0]['url']
            return meme

class Images(commands.Cog, name='Images', description="kitten, meme"):
    def __init__(self, client):
        self.client = client

    @commands.command(name='kitten', brief='KITTEN', description="GITTEN KITTEN")
    async def getkitten(self, ctx):
        # server = ctx.message.guild
        message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + "Gitten Kitten...")
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Gitten a Kitten for {ctx.message.author}", icon_url=ctx.author.avatar_url)
        embed.set_image(url=await get_kittens())
        await ctx.send(embed=embed)
        await message.delete()

    @commands.command(name='meme', brief='Pure danks', description="Dankest of memes")
    async def get_meme(self, ctx):
        message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + "Fetching shitty meme...")
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Shitty meme for {ctx.message.author}", icon_url=ctx.author.avatar_url)
        embed.set_image(url=await get_memes())
        await ctx.send(embed=embed)
        await message.delete()




def setup(client):
    client.add_cog(Images(client))
