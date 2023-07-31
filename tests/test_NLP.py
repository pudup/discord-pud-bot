import pytest
import cohere
import os

API_KEY = os.getenv("API_KEY")  # Cohere
GPT_KEY = os.getenv("GPT_KEY")  # Chatgpt (rapidapi)


@pytest.mark.asyncio
async def test_cohere():
    co = cohere.Client(API_KEY)
    response = co.generate(
        model='command',
        prompt="This is a test",
        max_tokens=300,
        temperature=0.9,
        k=0,
        stop_sequences=[],
        return_likelihoods='NONE')
    try:
        text = str(response.generations[0].text)
    except:
        text = None
    assert text is not None
