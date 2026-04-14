import os, json, datetime, pathlib, base64
from typing import List, Dict

# Auto-load .env for keys
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import requests  # for Automatic1111 (local SD)

# TTS support
try:
    from tts import TTSEngine
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# Agent system
try:
    from agents import toolkit, parse_agent_request, execute_agent_action
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

ROOT = pathlib.Path(__file__).parent

# ---------- Helpers ----------
def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def read_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

def write_json(path: pathlib.Path, data: Dict):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

# ---------- Load Persona / Memory / Settings ----------
PERSONA = read_text(ROOT / "persona.txt")
MEMORY  = read_json(ROOT / "memory.json") or {"facts": [], "style_rules": [], "user_prefs": {}}
SETTINGS = read_json(ROOT / "settings.json") or {}

# Initialize TTS if available
tts_engine = None
if TTS_AVAILABLE and SETTINGS.get("tts", {}).get("enabled", False):
    try:
        tts_engine = TTSEngine()
        print("TTS engine initialized.")
    except Exception as e:
        print(f"Note: TTS failed to initialize: {e}")

# ---------- PDF knowledge (preload at boot) ----------
def load_pdfs_from_data(max_pages=40, max_chars=12000) -> str:
    data_dir = ROOT / "data"
    if not data_dir.exists():
        ensure_dir(data_dir)
        return ""

    try:
        import PyPDF2
    except ImportError:
        print("Note: PyPDF2 not installed. Run: pip install PyPDF2")
        return ""

    chunks, total = [], 0
    for name in sorted(os.listdir(data_dir)):
        if not name.lower().endswith(".pdf"): continue
        p = data_dir / name
        try:
            with open(p, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages[:max_pages]:
                    text = page.extract_text() or ""
                    if not text.strip(): continue
                    need = max_chars - total
                    if need <= 0: break
                    if len(text) > need: text = text[:need]
                    chunks.append(text)
                    total += len(text)
                if total >= max_chars: break
        except Exception as e:
            print(f"PDF read issue ({name}): {e}")

    combined = "\n".join(chunks).strip()
    if combined:
        print("Loaded PDF knowledge from /data folder.")
    return combined

PDF_KNOWLEDGE = load_pdfs_from_data()

# ---------- Tarot Card Library ----------
MAJORS = {
    "the fool":        {"num": 0,  "element": "Air",     "planet": "Uranus",  "colors": "sunlit yellow, spring green", "motifs": "cliff edge, white dog, knapsack, white rose"},
    "the magician":    {"num": 1,  "element": "Air",     "planet": "Mercury", "colors": "red, white, gold", "motifs": "wand cup sword pentacle on table, infinity lemniscate"},
    "the high priestess":{"num": 2,"element": "Water",   "moon": "Moon",      "colors": "indigo, silver, pearl", "motifs": "pomegranates veil, pillars B & J, crescent moon, scroll"},
    "the empress":     {"num": 3,  "element": "Earth",   "planet": "Venus",   "colors": "emerald, rose, cream", "motifs": "wheat field, 12 stars, scepter, lush forest"},
    "the emperor":     {"num": 4,  "element": "Fire",    "sign": "Aries",     "colors": "crimson, granite, gold", "motifs": "ram heads, armor, mountain throne, orb"},
    "the hierophant":  {"num": 5,  "element": "Earth",   "sign": "Taurus",    "colors": "scarlet, ivory, brass", "motifs": "keys crossed, triple crown, acolytes"},
    "the lovers":      {"num": 6,  "element": "Air",     "sign": "Gemini",    "colors": "soft rose, sky blue, gold", "motifs": "angel, two figures, fruit tree, serpent"},
    "the chariot":     {"num": 7,  "element": "Water",   "sign": "Cancer",    "colors": "teal, silver, black", "motifs": "sphinxes, star canopy, armor, city walls"},
    "strength":        {"num": 8,  "element": "Fire",    "sign": "Leo",       "colors": "gold, white, green", "motifs": "lion, infinity lemniscate, flower garland"},
    "the hermit":      {"num": 9,  "element": "Earth",   "sign": "Virgo",     "colors": "slate, bone, starlight", "motifs": "lantern, mountain peak, staff, night sky"},
    "wheel of fortune":{"num": 10, "element": "Fire",    "planet": "Jupiter", "colors": "cobalt, gold, white", "motifs": "T-A-R-O letters, sphinx, snake, wings, books"},
    "justice":         {"num": 11, "element": "Air",     "sign": "Libra",     "colors": "crimson, gray, gold", "motifs": "scales, sword, veils, pillars"},
    "the hanged man":  {"num": 12, "element": "Water",   "planet": "Neptune", "colors": "aqua, amber, ivy", "motifs": "halo, inverted figure, rope, living tree"},
    "death":           {"num": 13, "element": "Water",   "sign": "Scorpio",   "colors": "black, white, rose", "motifs": "flag with white rose, rising sun, river"},
    "temperance":      {"num": 14, "element": "Fire",    "sign": "Sagittarius","colors": "opal, white, gold", "motifs": "angel, two cups, rainbow, iris"},
    "the devil":       {"num": 15, "element": "Earth",   "sign": "Capricorn", "colors": "obsidian, ember, brass", "motifs": "horned figure, chains, inverted pentagram"},
    "the tower":       {"num": 16, "element": "Fire",    "planet": "Mars",    "colors": "charcoal, flame, electric gold", "motifs": "lightning, falling figures, crown"},
    "the star":        {"num": 17, "element": "Air",     "sign": "Aquarius",  "colors": "ultramarine, silver, lavender", "motifs": "eight-point star, jugs, pool"},
    "the moon":        {"num": 18, "element": "Water",   "sign": "Pisces",    "colors": "indigo, silver, midnight", "motifs": "moon phases, path, dog & wolf, crayfish"},
    "the sun":         {"num": 19, "element": "Fire",    "star": "Sun",       "colors": "gold, white, sunflower", "motifs": "sunflower wall, child on horse, banner"},
    "judgement":       {"num": 20, "element": "Fire",    "planet": "Pluto",   "colors": "pearl, scarlet, sky", "motifs": "trumpet, rising figures, crosses"},
    "the world":       {"num": 21, "element": "Earth",   "planet": "Saturn",  "colors": "emerald, violet, gold", "motifs": "laurel wreath, four living creatures"}
}

SUITS = {
    "wands":  {"element": "Fire",  "colors": "scarlet, amber, charcoal", "motifs": "sprouting staffs, salamanders, sparks"},
    "cups":   {"element": "Water", "colors": "teal, silver, pearl",      "motifs": "chalices, water, lotus, fish"},
    "swords": {"element": "Air",   "colors": "steel, indigo, white",     "motifs": "blades, clouds, birds, feathers"},
    "pentacles": {"element": "Earth","colors": "green, ochre, bronze",   "motifs": "coins, wheat, vines, stars"}
}

COURTS = ["page", "knight", "queen", "king"]

def build_tarot_prompt(card: str, style_hint: str) -> str:
    name = card.strip()
    lower = name.lower()

    # Major Arcana
    if lower in MAJORS:
        meta = MAJORS[lower]
        accents = ", ".join([v for k,v in meta.items() if k in ("colors","motifs")])
        astro = ", ".join([f"{k}: {v}" for k,v in meta.items() if k in ("element","planet","sign","moon","star")])
        title = name.title()
        base = f"""
Design a high-resolution tarot illustration of "{title}".
Symbolic accuracy first; luminous, print-ready composition with ornate border.
Astro/Elemental cues: {astro}.
Palette & motifs: {accents}.
Include classic emblems for recognizability; refine with tasteful modern-mystical aesthetics.
No text labels; portrait orientation; crisp edges.
"""
    else:
        # Minor Arcana parse: e.g., "Three of Cups", "Knight of Swords"
        parts = lower.split(" of ")
        if len(parts) == 2:
            rank, suit = parts[0], parts[1]
            suit_meta = SUITS.get(suit, {})
            suit_accents = f"Element: {suit_meta.get('element','')}; Palette: {suit_meta.get('colors','')}; Motifs: {suit_meta.get('motifs','')}"
            human = f"{rank.title()} of {suit.title()}"
            # Court flavor
            court_add = ""
            if rank in COURTS:
                court_traits = {
                    "page": "youthful messenger; curiosity; beginnings",
                    "knight": "motion, quest, focused drive",
                    "queen": "mature mastery with receptivity, inner authority",
                    "king": "structured mastery, command, outward authority"
                }
                court_add = f"Court tone: {court_traits.get(rank,'noble presence')}."
            base = f"""
Design a high-resolution tarot illustration of "{human}".
Symbolic accuracy first; harmonious composition for a printed card; ornate border.
Suit guidance → {suit_accents}. {court_add}
Show the correct number of suit emblems arranged with rhythm and balance.
No text labels; portrait orientation; crisp edges.
"""
        else:
            # Fallback generic
            base = f"""
Design a high-resolution tarot card illustration for "{name}".
Symbolic accuracy first; modern-mystical; ornate border; portrait orientation.
"""

    if style_hint:
        base += f"\nStyle hint: {style_hint.strip()}."
    base += "\nOutput: one PNG image, print-ready, no watermark."
    return base.strip()

# ---------- Image generation ----------
def _save_b64_image(b64_data: str, out_dir: pathlib.Path, stem: str) -> str:
    ensure_dir(out_dir)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{stem}_{ts}.png"
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64_data))
    return str(out_path)

def generate_image_openai(prompt: str) -> str:
    from openai import OpenAI
    out_dir = ROOT / (SETTINGS.get("image", {}).get("output_dir", "outputs"))
    model = SETTINGS.get("image", {}).get("openai_model", "gpt-image-1")

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "no-key"),
        base_url=os.environ.get("OPENAI_BASE_URL")  # leave None for real OpenAI
    )
    res = client.images.generate(model=model, prompt=prompt, size="1024x1024")
    b64 = res.data[0].b64_json
    return _save_b64_image(b64, out_dir, "openai")

def generate_image_a1111(prompt: str) -> str:
    out_dir = ROOT / (SETTINGS.get("image", {}).get("output_dir", "outputs"))
    url = SETTINGS.get("image", {}).get("a1111_url", "http://127.0.0.1:7860")
    payload = {
        "prompt": prompt,
        "steps": 28,
        "width": 768,
        "height": 1024,
        "sampler_name": "DPM++ 2M",
        "cfg_scale": 6.5
    }
    r = requests.post(f"{url}/sdapi/v1/txt2img", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    if not data.get("images"):
        raise RuntimeError("A1111 returned no images")
    b64 = data["images"][0]
    return _save_b64_image(b64, out_dir, "sd")

def generate_image(prompt: str) -> str:
    provider = SETTINGS.get("image", {}).get("provider", "openai").lower()
    if provider == "automatic1111":
        return generate_image_a1111(prompt)
    return generate_image_openai(prompt)

# ---------- System prompt ----------
def build_system_prompt(persona: str, memory: Dict, pdf_text: str) -> str:
    facts = "\n".join(f"- {x}" for x in memory.get("facts", []))
    rules = "\n".join(f"- {x}" for x in memory.get("style_rules", []))
    prefs = "\n".join(f"- {k}: {v}" for k, v in memory.get("user_prefs", {}).items())
    prompt = f"""{persona}

[Long-term memory — facts]
{facts}

[Style rules]
{rules}

[User preferences]
{prefs}

Be concise by default. If the user says "carnal", it's a friendly address — respond warmly.
Never claim you'll do work later; do what you can now.
"""
    if pdf_text:
        prompt += f"\n[Reference knowledge loaded from PDFs]\n{pdf_text}"
    return prompt

SYSTEM_PROMPT = build_system_prompt(PERSONA, MEMORY, PDF_KNOWLEDGE)

# ---------- LLM client ----------
from openai import OpenAI as ChatClient
chat_client = ChatClient(
    api_key=os.environ.get("OPENAI_API_KEY", "no-key"),
    base_url=os.environ.get("OPENAI_BASE_URL")  # set to local server for local LLMs if desired
)

MODEL = SETTINGS.get("model", "gpt-4o-mini")
TEMPERATURE = SETTINGS.get("temperature", 0.7)
MAX_TOKENS = SETTINGS.get("max_tokens", 800)

def chat_once(messages: List[Dict]) -> str:
    resp = chat_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return resp.choices[0].message.content

# ---------- Transcript / Memory ops ----------
def save_transcript(history: List[Dict]):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "transcripts"
    ensure_dir(out_dir)
    path = out_dir / f"carnal_chat_{ts}.txt"
    with open(path, "w", encoding="utf-8") as f:
        for m in history:
            f.write(f"[{m['role'].upper()}]\n{m['content']}\n\n")
    print(f"Saved transcript to {path}")

def append_memory_fact(fact: str):
    MEMORY.setdefault("facts", []).append(fact)
    write_json(ROOT / "memory.json", MEMORY)

# ---------- Main ----------
def main():
    global SYSTEM_PROMPT
    print("Carnal 2.0 — ready. Commands: ':quit', ':showmem', ':remember <fact>', ':img <prompt>', ':card <name> [style]', ':voice <text>', ':tts on/off'")
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    history.append({"role": "user", "content": "Greet me briefly and confirm you're Carnal 2.0."})
    try:
        greeting = chat_once(history)
        print(f"CAR2: {greeting}\n")
        if tts_engine:
            tts_engine.speak(greeting)
    except Exception as e:
        print("Boot greeting failed, continuing.", e)

    while True:
        try:
            user = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            save_transcript(history)
            break

        if not user: continue

        cmd = user.lower()
        if cmd in (":quit", ":q", "exit"):
            save_transcript(history); break

        if cmd == ":showmem":
            print(json.dumps(MEMORY, indent=2)); continue

        if cmd.startswith(":remember "):
            fact = user[len(":remember "):].strip()
            if fact:
                append_memory_fact(fact)
                SYSTEM_PROMPT = build_system_prompt(PERSONA, MEMORY, PDF_KNOWLEDGE)
                print("CAR2: Noted. Memory updated.")
            else:
                print("CAR2: Give me something to remember.")
            continue

        if cmd.startswith(":img "):
            raw = user[5:].strip()
            if not raw:
                print("CAR2: Use like  :img hecate at a crossroads, moonlit, gold ink")
                continue
            try:
                out_path = generate_image(raw)
                print(f"CAR2: Image saved → {out_path}")
            except Exception as e:
                print("CAR2: Image error:", e)
            continue

        if cmd.startswith(":card "):
            rest = user[6:].strip()
            if not rest:
                print('CAR2: Use like  :card The Moon art nouveau, silver foil, deep indigo')
                continue
            # split card name and style hint (first comma splits well)
            if "," in rest:
                first, style = rest.split(",", 1)
                card_name, style_hint = first.strip(), style.strip()
            else:
                card_name, style_hint = rest, ""
            prompt = build_tarot_prompt(card_name, style_hint)
            try:
                out_path = generate_image(prompt)
                print(f"CAR2: Card artwork saved → {out_path}")
            except Exception as e:
                print("CAR2: Card generation error:", e)
            continue

        if cmd.startswith(":voice "):
            text = user[7:].strip()
            if not text:
                print("CAR2: Use like  :voice Hey bro!")
                continue
            if tts_engine:
                try:
                    tts_engine.speak(text)
                    print("CAR2: Spoken.")
                except Exception as e:
                    print(f"CAR2: Voice error: {e}")
            else:
                print("CAR2: TTS not available. Enable in settings.json")
            continue

        if cmd == ":tts on":
            if tts_engine:
                SETTINGS.setdefault("tts", {})["enabled"] = True
                write_json(ROOT / "settings.json", SETTINGS)
                print("CAR2: TTS enabled. I'll speak my replies now.")
            else:
                print("CAR2: TTS not initialized. Install pyttsx3 first.")
            continue

        if cmd == ":tts off":
            if SETTINGS.get("tts", {}).get("enabled"):
                SETTINGS["tts"]["enabled"] = False
                write_json(ROOT / "settings.json", SETTINGS)
                print("CAR2: TTS disabled.")
            continue

        # normal chat
        history.append({"role": "user", "content": user})
        try:
            reply = chat_once(history)
        except Exception as e:
            print("CAR2 error:", e)
            continue
        history.append({"role": "assistant", "content": reply})
        print(f"CAR2: {reply}\n")
        
        # Speak reply if TTS is enabled
        if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
            try:
                tts_engine.speak(reply)
            except Exception as e:
                print(f"(TTS error: {e})")

if __name__ == "__main__":
    main()
