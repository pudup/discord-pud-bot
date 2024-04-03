from random import randint


async def color():
    """Returns a random colour in hex format. Mainly for use with discord embeds"""
    random_number = randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)
