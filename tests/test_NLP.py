import pytest
import cohere
import os

API_KEY = os.getenv("API_KEY")  # Cohere


@pytest.mark.asyncio
async def test_cohere():
    co = cohere.Client(API_KEY)
    response = co.chat(message="This is a test")
    assert response.text is not None
