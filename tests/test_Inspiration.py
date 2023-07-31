import pytest
from cogs import Inspiration


@pytest.mark.asyncio
async def test_pickup():
    response = await Inspiration.pickup()
    assert response != "I couldn't think of anything so just be yourself or something for once :>"


@pytest.mark.asyncio
async def test_get_meme():
    quote, author = await Inspiration.quotes()
    assert isinstance(quote, str) & isinstance(author, str)
