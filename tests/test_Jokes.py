import pytest
from cogs import Jokes


@pytest.mark.asyncio
async def test_dad_jokes():
    response = await Jokes.dad_jokes()
    assert response != "I couldn't think of anything funny :<"


@pytest.mark.asyncio
async def test_shower():
    response = await Jokes.shower()
    assert response != "I couldn't think of anything :<\nTry again later"
