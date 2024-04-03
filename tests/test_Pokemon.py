import random
import pytest
from cogs import Pokemon


@pytest.mark.asyncio
async def test_pokemon_num():
    random_pokemon = random.randint(1, 150)
    try:
        await Pokemon.pokemon_num(str(random_pokemon))
        assert True
    except:
        assert False


@pytest.mark.asyncio
async def test_pokemon_name():
    random_pokemon = random.randint(1, 150)
    try:
        response = await Pokemon.pokemon_name(str(random_pokemon))
        assert int(response[7]) == random_pokemon
        assert response[1][0:5] == "https"
        assert response[5]["hp"] != "unknown"
    except:
        assert False
