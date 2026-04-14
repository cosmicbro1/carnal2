import os
from skills import load_skills
from utils.retrieval import search_notes

def load_persona():
    style_path = os.path.join("persona", "style.md")
    traits_path = os.path.join("persona", "traits.txt")

    try:
        with open(style_path, "r", encoding="utf-8") as f:
            style = f.read()
    except FileNotFoundError:
        style = "[Style file missing]"

    traits = []
    try:
        with open(traits_path, "r", encoding="utf-8") as f:
            traits = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        traits = ["[No traits found]"]

    return style, traits


def respond(user_msg):
    style, traits = load_persona()
    skills = load_skills()

    # Skill trigger example
    skill_out = None
    if "tarot" in user_msg.lower() and "draw_tarot" in skills:
        skill_out = skills["draw_tarot"]["fn"]("three")

    # Knowledge retrieval
    keywords = ["hecate", "moon", "astrology"]
    context = search_notes(user_msg) if any(k in user_msg.lower() for k in keywords) else []

    snippets = "\n".join(f"- {c['snippet']}" for c in context) if context else "Nada new from my grimoire right now."

    reply = f"""{style}

Traits: {" | ".join(traits)}

Carnal says:
I hear you. Based on my notes, here’s what I’ve got:
{snippets}

Skill output: {skill_out if skill_out else "No skill used this time."}

And from the heart: Whatever path you're on, stay firme. 🌙✨
"""
    return reply


if __name__ == "__main__":
    print("✨ Cosmic Bro Carnal 2.0 booting… ✨")
    while True:
        msg = input("\nYou: ")
        if msg.lower() in ["quit", "exit"]:
            print("Carnal: Órale, hasta la próxima. 🌌")
            break
        print(respond(msg))
