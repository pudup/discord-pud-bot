import random
import pytest
from cogs import Music


@pytest.mark.asyncio
async def test_search_youtube():
    query = "1 second video"
    try:
        await Music.search_youtube(query)
        assert True
    except:
        assert False


@pytest.mark.asyncio
async def test_is_link():
    try:
        await Music.is_link("https://www.google.com")
        assert True
    except:
        assert False


@pytest.mark.asyncio
async def test_get_lyrics():
    try:
        await Music.get_lyrics("a little more", "cody fry")
        assert True
    except:
        assert False
