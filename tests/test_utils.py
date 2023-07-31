import pytest
from utils import utils


@pytest.mark.asyncio
async def test_color():
    response = await utils.color()
    assert isinstance(response, int)
