import random

# Simple Tarot Deck with meanings
tarot_deck = [
    {"name": "The Fool", "meaning": "New beginnings, spontaneity, free spirit."},
    {"name": "The Magician", "meaning": "Manifestation, resourcefulness, power."},
    {"name": "The High Priestess", "meaning": "Intuition, sacred knowledge, divine feminine."},
    {"name": "The Empress", "meaning": "Femininity, beauty, nature, nurturing."},
    {"name": "The Emperor", "meaning": "Authority, structure, father figure."},
    {"name": "The Hierophant", "meaning": "Spiritual wisdom, tradition, religious beliefs."},
    {"name": "The Lovers", "meaning": "Love, harmony, relationships, choices."},
    {"name": "The Chariot", "meaning": "Control, willpower, victory, determination."},
    # Add more cards as you like!
]

# Pull a random card
pulled_card = random.choice(tarot_deck)

# Display the result
print("✨ You have drawn:", pulled_card["name"])
print("🔮 Meaning:", pulled_card["meaning"])