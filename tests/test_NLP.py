import pytest
import cohere
import os

COHERE_API_KEY = os.getenv("COHERE_API_KEY")  # Cohere


@pytest.mark.asyncio
async def test_cohere():
    co = cohere.Client(COHERE_API_KEY)
    response = co.chat(message="This is a test")
    assert response.text is not None
