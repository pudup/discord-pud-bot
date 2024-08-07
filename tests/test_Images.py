import pytest
from cogs import Images


@pytest.mark.asyncio
async def test_get_cat():
    response = await Images.get_cat()
    assert response[0:5] == "https"


@pytest.mark.asyncio
async def test_get_meme():
    title, meme = await Images.get_memes()
    assert meme is not None
