import pytest
from cogs import Facts


@pytest.mark.asyncio
async def test_cat_facts():
    response = await Facts.cat_facts()
    assert response != "I couldn't find any new facts for some reason :<"
