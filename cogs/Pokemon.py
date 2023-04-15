import os
import random
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

PREFIX = os.getenv('PREFIX')


async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)


async def pokemon_num(index):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://pokeapi.co/api/v2/pokemon/{index}") as response:
            json = await response.json()
            pokename = json['forms'][0]['name'].title()
            return [pokename, f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{index}.png"]


async def pokemom_name(name):
    async with aiohttp.ClientSession() as session:
        colours = {
            "normal": 0xA8A77A,
            "fire": 0xEE8130,
            "water": 0x6390F0,
            "electric": 0xF7D02C,
            "grass": 0x7AC74C,
            "ice": 0x96D9D6,
            "fighting": 0xC22E28,
            "poison": 0xA33EA1,
            "ground": 0xE2BF65,
            "flying": 0xA98FF3,
            "psychic": 0xF95587,
            "bug": 0xA6B91A,
            "rock": 0xB6A136,
            "ghost": 0x735797,
            "dragon": 0x6F35FC,
            "dark": 0x705746,
            "steel": 0xB7B7CE,
            "fairy": 0xD685AD,
        }
        async with session.get(f"https://pokeapi.co/api/v2/pokemon/{name}") as response:
            try:
                json = await response.json()
            except:
                return False
            pokename = json['forms'][0]['name'].title()
            image_url = json['sprites']['front_default']
            try:
                first_appear = json['game_indices'][0]['version']['name']
            except:
                first_appear = "Gen 6+ I think"
            try:
                base_ability = json['abilities'][0]['ability']['name']
            except:
                print("Base ability failed")
            try:
                hidden_ability = json['abilities'][1]['ability']['name']
            except:
                hidden_ability = "None"
            try:
                type = [type['type']['name'] for type in json['types']]
            except:
                print("Type failed")
            colour = colours[type[0]]
            try:
                stats = {"hp": json['stats'][0]['base_stat'],
                         "atk": json['stats'][1]['base_stat'],
                         "spatk": json['stats'][2]['base_stat'],
                         "def": json['stats'][3]['base_stat'],
                         "spdef": json['stats'][4]['base_stat'],
                         "speed": json['stats'][5]['base_stat'], }
            except:
                print("stats failed")
            weight = json['weight']
            pokedexid = json['id']
            height = int(json['height']) * 10
            return [pokename, image_url, first_appear, base_ability, hidden_ability, stats, weight, pokedexid, type,
                    colour, height]


class Pokemon(commands.Cog, name='Pokémon', description='pokemon, pokedex'):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='pokedex', description=f'Get name of pokémon at pokédex number.')
    @app_commands.describe(index="Pokédex number")
    async def pokedex(self, interaction: discord.Interaction, index: str) -> None:
        # if not index:
        #     await interaction.response.send_message(
        #         f"{interaction.user.mention}\nThis command requires an additional argument\nTry:\n```/pokedex {random.randint(1, 898)}```")
        #     return
        try:
            arg = int(index)
        except:
            await interaction.response.send_message(f"{interaction.user}\nInvalid index")
            return
        if not 1 <= arg <= 1010:
            await interaction.response.send_message(f"{interaction.user}\nThe Pokédex ranges from 1 to 1010")
            return
        number = await pokemon_num(arg)
        embed = discord.Embed(color=0x45c6ee)
        embed.set_author(name=f'{interaction.user}', icon_url=interaction.user.display_avatar)
        embed.set_image(url=number[1])
        embed.set_footer(text=f"Use /pokemon {str(number[0])} for more info")
        embed.description = f"The Pokémon at number {arg} on the Pokédex is " + str(number[0])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='pokemon',
                          description=f'Get detailed information about a pokémon by name. \n Try /pokemon ditto')
    @app_commands.describe(name="Pokémon name")
    async def pokemon(self, interaction: discord.Interaction, name: str) -> None:
        # if not name:
        #     await interaction.response.send_message(
        #         f"{interaction.user}\nThis command requires an additional argument\nTry:\n```/pokemon ditto```")
        #     return

        out_list = await pokemom_name(name.lower())
        if not out_list:
            await interaction.response.send_message(
                "I couldn't find what you're looking for. Try a number from 1-898 if you don't know a name")
            return
        embed = discord.Embed(color=out_list[9])
        embed.set_author(name=out_list[0], icon_url=out_list[1])
        embed.set_thumbnail(url=out_list[1])
        embed.add_field(name='Pokédex Entry Number', value=out_list[7])
        embed.add_field(name='First Game Appearance', value=out_list[2].title())
        embed.add_field(name='Type(s)', value=', '.join(out_list[8]).title())
        embed.add_field(name='Base Ability', value=out_list[3].title())
        embed.add_field(name='Hidden Ability', value=out_list[4].title())
        embed.add_field(name='Weight', value=out_list[6])
        embed.add_field(name='Base Stats', value=f"HP: {out_list[5]['hp']}\n"
                                                 f"ATK: {out_list[5]['atk']}\n"
                                                 f"SP ATK: {out_list[5]['spatk']}\n"
                                                 f"DEF: {out_list[5]['def']}\n"
                                                 f"SP DEF: {out_list[5]['spdef']}\n"
                                                 f"SPEED: {out_list[5]['speed']}")
        embed.add_field(name='Height', value=f"{out_list[10]} cms")

        embed.set_footer(text="Now the colour matches the type :>\n-iPudup#2124")
        await interaction.response.send_message(embed=embed)


async def setup(client):
    await client.add_cog(Pokemon(client))
