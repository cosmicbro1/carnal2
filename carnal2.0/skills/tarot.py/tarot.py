import random

def draw_tarot(spread: str = "one_card"):
    deck = ["El Sol", "La Luna", "La Muerte", "El Mago", "La Emperatriz"]
    if spread == "three":
        return random.sample(deck, 3)
    return [random.choice(deck)]

REGISTRY = {
    "draw_tarot": {
        "fn": draw_tarot,
        "desc": "Draw tarot cards; spread in {'one_card','three'}",
        "args": {"spread": "str"}
    }
}
