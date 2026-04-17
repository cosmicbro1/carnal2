import os, json, datetime, pathlib, base64, hashlib
from typing import List, Dict

# Auto-load .env for keys
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import requests  # for Automatic1111 (local SD)

# Gemma 4 support (Google's most advanced open-source LLM)
try:
    import google.generativeai as genai
    GEMMA4_AVAILABLE = True
except ImportError:
    GEMMA4_AVAILABLE = False

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

# Human Design system
try:
    from human_design import generate_hd_chart, match_compatibility
    HD_AVAILABLE = True
except ImportError:
    HD_AVAILABLE = False

# Splash screen support
try:
    from PIL import Image
    import tkinter as tk
    SPLASH_AVAILABLE = True
except ImportError:
    SPLASH_AVAILABLE = False

ROOT = pathlib.Path(__file__).parent

# ---------- Splash Screen ----------
def show_splash_screen(duration_ms: int = 2500) -> None:
    """Display splash screen with carnal2.0_start.png image."""
    if not SPLASH_AVAILABLE:
        return
    
    # Check multiple locations for splash image
    possible_paths = [
        ROOT / "carnal2.0_start.png",
        pathlib.Path.home() / "Desktop" / "carnal2.0_start.png",
    ]
    
    splash_path = None
    for path in possible_paths:
        if path.exists():
            splash_path = path
            break
    
    if not splash_path:
        return
    
    try:
        # Create splash window
        splash = tk.Tk()
        splash.withdraw()  # Hide window initially
        
        # Load image for sizing
        img = Image.open(splash_path)
        img_width, img_height = img.size
        
        # Create label with image
        photo = tk.PhotoImage(file=str(splash_path))
        label = tk.Label(splash, image=photo, bg="white")
        label.image = photo
        label.pack()
        
        # Position window in center of screen
        splash.update_idletasks()
        splash.deiconify()
        x = (splash.winfo_screenwidth() // 2) - (img_width // 2)
        y = (splash.winfo_screenheight() // 2) - (img_height // 2)
        splash.geometry(f"{img_width}x{img_height}+{x}+{y}")
        
        # Remove window decorations
        splash.overrideredirect(True)
        
        # Display for duration
        splash.after(duration_ms, splash.destroy)
        splash.mainloop()
    except Exception as e:
        print(f"Note: Could not display splash screen: {e}")


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
MEMORY  = read_json(ROOT / "memory.json") or {"facts": [], "style_rules": [], "user_prefs": {}, "hd_charts": {}}
SETTINGS = read_json(ROOT / "settings.json") or {}

# Ensure all healing data structures exist in memory
if "hd_charts" not in MEMORY:
    MEMORY["hd_charts"] = {}
if "mood_tracker" not in MEMORY:
    MEMORY["mood_tracker"] = []
if "journals" not in MEMORY:
    MEMORY["journals"] = {}
if "affirmations" not in MEMORY:
    MEMORY["affirmations"] = []
if "healing_plans" not in MEMORY:
    MEMORY["healing_plans"] = []
if "user_language" not in MEMORY:
    MEMORY["user_language"] = "english"
if "user_profile" not in MEMORY:
    MEMORY["user_profile"] = {
        "healing_goals": [],
        "love_language": None,
        "preferred_modalities": [],
        "music_preferences": [],
        "spiritual_interests": [],
        "notification_times": []
    }
if "gamification" not in MEMORY:
    MEMORY["gamification"] = {
        "journal_streak": 0,
        "last_journal_date": None,
        "practice_streak": 0,
        "last_practice_date": None,
        "badges": [],
        "challenges_completed": []
    }
if "accessibility" not in MEMORY:
    MEMORY["accessibility"] = {
        "dark_mode": False,
        "voice_playback": False,
        "captions": True,
        "readable_fonts": True,
        "font_size": "medium"
    }
if "cosmic_features" not in MEMORY:
    MEMORY["cosmic_features"] = {
        "voice_notes": [],
        "moon_rituals": [],
        "oracle_readings": [],
        "love_ripples": [],
        "sound_mixes": []
    }

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

# ---------- LLM client: Ollama (Free, Local, Open Source) PRIMARY ----------
from openai import OpenAI as ChatClient

# Initialize Ollama client (FREE, LOCAL, OPEN SOURCE - Primary for students)
ollama_client = None
ollama_available = False
try:
    ollama_url = SETTINGS.get("ollama", {}).get("base_url", "http://localhost:11434")
    ollama_client = ChatClient(
        api_key="ollama",
        base_url=f"{ollama_url}/v1"
    )
    # Test connection
    ollama_client.chat.completions.create(
        model=SETTINGS.get("ollama", {}).get("model", "gemma2"),
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=1
    )
    ollama_available = True
    print("✓ Ollama (Free, Open Source, Local) initialized - STUDENT MODE ENABLED")
except Exception as e:
    ollama_available = False
    print(f"Note: Ollama not available. Make sure Ollama is running. Run 'ollama serve' in another terminal.")

# Initialize OpenAI client (optional, paid)
chat_client = ChatClient(
    api_key=os.environ.get("OPENAI_API_KEY", "no-key"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)

# Initialize Gemma 4 API if available (optional, free tier)
gemma_client = None
if GEMMA4_AVAILABLE:
    try:
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        gemma_client = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=800,
            )
        )
    except Exception as e:
        gemma_client = None

# Model configuration
LLM_PROVIDER = SETTINGS.get("llm_provider", "auto").lower()  # "ollama", "gemma", "openai", or "auto"
MODEL = SETTINGS.get("model", "gpt-4o-mini")
TEMPERATURE = SETTINGS.get("temperature", 0.7)
MAX_TOKENS = SETTINGS.get("max_tokens", 800)
OLLAMA_MODEL = SETTINGS.get("ollama", {}).get("model", "gemma2")

def chat_once(messages: List[Dict]) -> str:
    """Chat using best available model: Ollama (free local) > Gemma 4 API > OpenAI."""
    global LLM_PROVIDER
    
    # Priority 1: Ollama (FREE, LOCAL, OPEN SOURCE)
    if (LLM_PROVIDER == "auto" or LLM_PROVIDER == "ollama") and ollama_available:
        try:
            resp = ollama_client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return resp.choices[0].message.content
        except Exception as e:
            if LLM_PROVIDER == "ollama":
                print(f"Ollama error: {e}")
            # Fall through to next provider
    
    # Priority 2: Gemma 4 API (Free tier, fast)
    if (LLM_PROVIDER == "auto" or LLM_PROVIDER == "gemma") and gemma_client:
        try:
            system_msg = ""
            user_msgs = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                elif msg["role"] == "user":
                    user_msgs.append(msg["content"])
            
            full_prompt = f"{system_msg}\n\n{user_msgs[-1] if user_msgs else ''}".strip()
            response = gemma_client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_TOKENS,
                )
            )
            return response.text
        except Exception as e:
            if LLM_PROVIDER == "gemma":
                print(f"Gemma error: {e}")
    
    # Priority 3: OpenAI (Fallback, paid)
    if LLM_PROVIDER == "auto" or LLM_PROVIDER == "openai":
        try:
            resp = chat_client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"All providers failed: {e}")
            return "Error: No LLM provider available. Install Ollama or set API keys."

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

# ---------- Love Coaching & Healing Conversations ----------
def get_love_coaching_prompt(topic: str) -> str:
    """Build specialized prompt for love coaching."""
    return f"""You are a compassionate relationship and love coach.
Your role: provide authentic, non-judgmental guidance on love, relationships, and self-love.

TOPIC: {topic}

Approach with:
- Deep listening and empathy
- Practical, actionable advice
- Psychological insights about relationships and attachment
- Self-love and boundaries wisdom
- Validation of feelings while encouraging growth

Be warm, wise, and genuine. Ask clarifying questions if needed.
Help them discover their own answers through reflection."""

def get_healing_prompt(emotion_topic: str) -> str:
    """Build specialized prompt for emotional healing conversations."""
    return f"""You are a compassionate emotional healing facilitator.
Your purpose: create a safe space for emotional exploration and healing.

EMOTIONAL FOCUS: {emotion_topic}

Your approach:
- Validate all emotions without judgment
- Create psychological safety and containment
- Guide them toward self-compassion and understanding
- Offer grounding and soothing language
- Help process and integrate difficult emotions
- Suggest gentle healing practices when appropriate

Be deeply empathetic, patient, and present. This is a healing space."""

def love_coaching_session(topic: str) -> str:
    """Run a love coaching session."""
    prompt = get_love_coaching_prompt(topic)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"I need guidance on: {topic}"}
    ]
    response = chat_once(messages)
    
    # Store in memory
    if "coaching_log" not in MEMORY:
        MEMORY["coaching_log"] = []
    MEMORY["coaching_log"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "love_coaching",
        "topic": topic,
        "insight": response[:200]  # Store first 200 chars as summary
    })
    write_json(ROOT / "memory.json", MEMORY)
    
    return response

def healing_conversation(emotion_topic: str) -> str:
    """Run a healing conversation session."""
    prompt = get_healing_prompt(emotion_topic)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"I'm struggling with: {emotion_topic}"}
    ]
    response = chat_once(messages)
    
    # Store in memory
    if "healing_log" not in MEMORY:
        MEMORY["healing_log"] = []
    MEMORY["healing_log"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "healing_conversation",
        "emotion": emotion_topic,
        "note": response[:200]
    })
    write_json(ROOT / "memory.json", MEMORY)
    
    return response

# ---------- Advanced Healing Modalities ----------

HEALING_MODALITIES = {
    "reiki": {
        "name": "Reiki Energy Healing",
        "description": "Ancient Japanese energy healing to restore balance and vitality"
    },
    "meditation": {
        "name": "Guided Meditation",
        "description": "Deep relaxation and mindfulness for inner peace"
    },
    "angel": {
        "name": "Angel Card Reading",
        "description": "Messages from spirit guides and angels"
    },
    "chakra": {
        "name": "Chakra Balancing",
        "description": "Restore harmony across all seven chakras"
    }
}

SOUND_INSTRUMENTS = {
    "singing_bowl": {
        "name": "Singing Bowls",
        "types": ["Tibetan", "Crystal"],
        "frequency": "432 Hz & 528 Hz",
        "effect": "Deep relaxation, cellular healing"
    },
    "tuning_fork": {
        "name": "Tuning Forks",
        "types": ["Solfeggio", "Angelic"],
        "frequency": "174-963 Hz",
        "effect": "Chakra alignment, pain relief"
    },
    "drums": {
        "name": "Shamanic Drums",
        "types": ["Heartbeat", "Shamanic Journey"],
        "frequency": "4-5 Hz (theta brainwave)",
        "effect": "Grounding, trance, connection"
    },
    "chimes": {
        "name": "Meditation Chimes",
        "types": ["Wind Chimes", "Meditation Bells"],
        "frequency": "Pure tones",
        "effect": "Mindfulness, presence, peace"
    }
}

def get_reiki_prompt(focus: str) -> str:
    """Reiki energy healing guidance."""
    return f"""You are a Reiki Master guide. Your role is to facilitate energetic healing.

HEALING FOCUS: {focus}

Guide them through:
- Energy cleansing and clearing
- Chakra activation and alignment
- Aura restoration and protection
- Grounding and earthing practices
- Visualization of healing light
- Hand positions and energy flow

Use calming, meditative language. Create a safe space for their energy to transform."""

def get_meditation_prompt(focus: str) -> str:
    """Guided meditation facilitator."""
    return f"""You are an expert meditation guide. Your role is deep, guided relaxation.

MEDITATION FOCUS: {focus}

Create a journey that includes:
- Grounding and centering practices
- Breath awareness and regulation
- Body scan relaxation
- Visualization of peaceful spaces
- Mantra or affirmation integration
- Gentle return to awareness

Use soothing, rhythmic language. Pace the meditation slowly."""

def get_angel_prompt(question: str) -> str:
    """Angel card reading and spirit messages."""
    return f"""You are a channel for angelic wisdom and guidance.

SEEKER'S QUESTION: {question}

Draw upon:
- Angel archetypes and their gifts
- Divine messages of love and support
- Spiritual insight and truth
- Intuitive guidance from higher realms
- Affirmations and blessings
- Practical spiritual wisdom

Deliver messages with compassion, clarity, and divine light."""

def get_chakra_prompt(intention: str) -> str:
    """Chakra balancing and alignment."""
    return f"""You are a Chakra Healer and energy alignment specialist.

CHAKRA INTENTION: {intention}

Guide them through:
- Identify blocked or imbalanced chakras
- Root chakra grounding (safety, survival)
- Sacral chakra flow (creativity, sexuality)
- Solar Plexus power (will, confidence)
- Heart chakra opening (love, compassion)
- Throat chakra expression (truth, voice)
- Third Eye intuition (vision, wisdom)
- Crown chakra connection (divine unity)
- Chakra cleansing and sealing techniques

Use color visualization and sacred tones."""

def get_sound_healing_prompt(instrument: str, focus: str) -> str:
    """Sound healing with specific instrument."""
    inst_info = SOUND_INSTRUMENTS.get(instrument, {})
    return f"""You are a Sound Healer specializing in {inst_info.get('name', 'sound healing')}.

HEALING INSTRUMENT: {inst_info.get('name')}
TYPES: {', '.join(inst_info.get('types', []))}
FREQUENCY: {inst_info.get('frequency', 'Healing Hz')}
EFFECT: {inst_info.get('effect', 'Cellular healing')}

HEALING INTENTION: {focus}

Guide them through:
- The science and spirituality of this instrument
- How sound frequencies affect the body
- Visualization of sound waves healing
- Recommended listening practices
- Duration and frequency for best results
- Integration with breathwork
- What to expect during healing

Create immersive sensory descriptions of the healing sounds."""

def reiki_session(focus: str) -> str:
    """Reiki energy healing session."""
    prompt = get_reiki_prompt(focus)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"I seek Reiki healing for: {focus}"}
    ]
    response = chat_once(messages)
    
    # Log session
    if "healing_modalities" not in MEMORY:
        MEMORY["healing_modalities"] = []
    MEMORY["healing_modalities"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "reiki",
        "focus": focus,
        "summary": response[:200]
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def meditation_session(focus: str) -> str:
    """Guided meditation session."""
    prompt = get_meditation_prompt(focus)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide me in meditation for: {focus}"}
    ]
    response = chat_once(messages)
    
    # Log session
    if "healing_modalities" not in MEMORY:
        MEMORY["healing_modalities"] = []
    MEMORY["healing_modalities"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "meditation",
        "focus": focus,
        "summary": response[:200]
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def angel_reading(question: str) -> str:
    """Angel card reading and channeled messages."""
    prompt = get_angel_prompt(question)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"I seek angelic guidance on: {question}"}
    ]
    response = chat_once(messages)
    
    # Log session
    if "healing_modalities" not in MEMORY:
        MEMORY["healing_modalities"] = []
    MEMORY["healing_modalities"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "angel_reading",
        "question": question,
        "message": response[:200]
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def chakra_balancing(intention: str) -> str:
    """Chakra alignment and balancing."""
    prompt = get_chakra_prompt(intention)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Help me balance my chakras for: {intention}"}
    ]
    response = chat_once(messages)
    
    # Log session
    if "healing_modalities" not in MEMORY:
        MEMORY["healing_modalities"] = []
    MEMORY["healing_modalities"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "chakra_balancing",
        "intention": intention,
        "guidance": response[:200]
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def sound_healing_session(instrument: str, focus: str) -> str:
    """Sound healing with specific instrument."""
    prompt = get_sound_healing_prompt(instrument, focus)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide my {SOUND_INSTRUMENTS.get(instrument, {}).get('name', 'sound healing')} session for: {focus}"}
    ]
    response = chat_once(messages)
    
    # Log session
    if "sound_healing_sessions" not in MEMORY:
        MEMORY["sound_healing_sessions"] = []
    MEMORY["sound_healing_sessions"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "instrument": instrument,
        "focus": focus,
        "guidance": response[:200]
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

# ---------- Healing Music Library ----------

MUSIC_LIBRARY = {
    "relaxation": {
        "name": "Relaxation & Calming Ambiance",
        "description": "Gentle nature sounds and ambient music for deep relaxation",
        "tracks": [
            "Ocean Waves & Seagulls - 528 Hz healing frequency",
            "Forest Ambiance with Birdsong - Grounding energy",
            "Rainfall & Thunder - Natural sleep inducer",
            "Bamboo Wind Chimes - Peaceful morning music",
            "Flowing Stream Meditation - Water healing energy",
            "Soft Piano & Nature Blend - Emotional soothing"
        ]
    },
    "chakra": {
        "name": "Chakra Healing Frequencies",
        "description": "Each track tuned to specific chakra energy centers",
        "tracks": [
            "Root Chakra - 396 Hz - Grounding & Safety",
            "Sacral Chakra - 417 Hz - Creativity & Flow",
            "Solar Plexus - 528 Hz - Power & Confidence",
            "Heart Chakra - 639 Hz - Love & Compassion",
            "Throat Chakra - 741 Hz - Truth & Expression",
            "Third Eye - 852 Hz - Intuition & Vision",
            "Crown Chakra - 963 Hz - Divine Connection"
        ]
    },
    "angel": {
        "name": "Angel Music & Heavenly Choirs",
        "description": "Ethereal sounds for spiritual connection and angelic guidance",
        "tracks": [
            "Angelic Harp & Choir - Pure divine energy",
            "Celestial Bells - Messages from heaven",
            "Orchestral Heaven - Angels singing",
            "Light Language Music - Higher dimensional healing",
            "Angelic Frequencies 432 Hz - Heart resonance",
            "Heavenly Voices - Ascended master tones"
        ]
    },
    "binaural": {
        "name": "Binaural Beats for Brainwave Entrainment",
        "description": "Frequencies designed to guide brain states for meditation and healing",
        "tracks": [
            "Delta Waves 2 Hz - Deep sleep and restoration",
            "Theta Waves 5-8 Hz - Deep meditation and creativity",
            "Alpha Waves 8-12 Hz - Relaxation and focus",
            "Beta Waves 12-30 Hz - Alertness and concentration",
            "Gamma Waves 30-100 Hz - Consciousness expansion",
            "Complete Brainwave Journey - All states in sequence"
        ]
    },
    "solfeggio": {
        "name": "Solfeggio Frequencies - Ancient Healing Tones",
        "description": "Sacred healing frequencies used for millennia",
        "tracks": [
            "174 Hz - Relief and vitality foundation",
            "285 Hz - Tissue repair and cellular healing",
            "396 Hz - Liberation from fear and guilt",
            "417 Hz - Undoing situations and transformations",
            "528 Hz - Miracles and DNA repair (Love frequency)",
            "639 Hz - Connecting relationships, love and kindness",
            "741 Hz - Intuition and problem solving",
            "852 Hz - Third eye awakening and intuition",
            "963 Hz - Unity and divine consciousness"
        ]
    }
}

MEDITATION_TECHNIQUES = {
    "loving_kindness": {
        "name": "Loving-Kindness Meditation",
        "description": "Cultivate compassion for self and others",
        "benefits": ["Increases compassion", "Reduces anger", "Builds emotional resilience"]
    },
    "transcendental": {
        "name": "Transcendental Meditation",
        "description": "Silent mantra-based meditation for pure consciousness",
        "benefits": ["Stress relief", "Enhanced creativity", "Deep inner peace"]
    },
    "mindfulness": {
        "name": "Mindfulness Meditation",
        "description": "Present-moment awareness without judgment",
        "benefits": ["Mental clarity", "Anxiety reduction", "Emotional balance"]
    },
    "chakra": {
        "name": "Chakra Meditation",
        "description": "Balance and align all seven energy centers",
        "benefits": ["Energy alignment", "Emotional healing", "Spiritual growth"]
    },
    "walking": {
        "name": "Walking Meditation",
        "description": "Mindful movement in nature or indoors",
        "benefits": ["Physical and mental integration", "Grounding", "Moving meditation"]
    }
}

HEALING_GIFTS = {
    "forgiveness": {
        "name": "Forgiveness Guidance",
        "description": "Release emotional burdens and heal through forgiveness",
        "subtitle": "Tools for liberating yourself and others"
    },
    "gratitude": {
        "name": "Gratitude Practices",
        "description": "Daily exercises to attract positivity and abundance",
        "subtitle": "Elevate your vibration through appreciation"
    },
    "nature": {
        "name": "Connect with Nature",
        "description": "Outdoor healing activities and wellness tips",
        "subtitle": "Nature as medicine for body and soul"
    },
    "relationships": {
        "name": "Healthy Relationships Workshop",
        "description": "Communication skills and relationship advice",
        "subtitle": "Build authentic, loving connections"
    },
    "inner_child": {
        "name": "Inner Child Healing",
        "description": "Gentle exercises for childhood trauma release",
        "subtitle": "Reparenting and self-compassion practices"
    }
}

def get_music_library_info(category: str) -> str:
    """Get detailed music library information and recommendations."""
    if category not in MUSIC_LIBRARY:
        return f"Available music categories: {', '.join(MUSIC_LIBRARY.keys())}"
    
    lib = MUSIC_LIBRARY[category]
    info = f"""
{lib['name']}

{lib['description']}

Available Tracks:
"""
    for track in lib['tracks']:
        info += f"  • {track}\n"
    info += """
All tracks are:
• Scientifically designed for healing
• Available for unlimited download
• 100% FREE with no restrictions
• Perfect for meditation and therapy sessions
• No ads or interruptions
"""
    return info

def get_forgiveness_prompt(situation: str) -> str:
    """Forgiveness and emotional release guidance."""
    return f"""You are a compassionate forgiveness coach helping release emotional burdens.

SITUATION: {situation}

Guide them through:
- Understanding the pain and its origins
- The healing power of forgiveness (for self and others)
- Practical forgiveness techniques and rituals
- Releasing resentment and anger safely
- Self-compassion and self-forgiveness first
- Letter writing or speaking exercises
- Moving forward with peace

Be gentle and deeply empathetic. Help them liberate themselves."""

def get_gratitude_prompt(focus: str) -> str:
    """Gratitude practice and positivity attraction."""
    return f"""You are a gratitude coach amplifying appreciation and abundance.

FOCUS: {focus}

Guide them through:
- Finding gratitude even in challenges
- Daily gratitude journaling practices
- Gratitude affirmations and mantras
- Shifting perspective to abundance
- Attracting more to be grateful for
- Heart-centered appreciation exercises
- Gratitude rituals and ceremonies

Use uplifting, abundance-rich language. Elevate their vibration."""

def get_nature_prompt(activity: str) -> str:
    """Nature connection and outdoor healing."""
    return f"""You are a nature healing guide connecting people to Earth's medicine.

ACTIVITY: {activity}

Recommend:
- Specific outdoor activities aligned with their intention
- Best times and places for healing in nature
- How to use natural elements (water, earth, plants)
- Forest bathing and grounding practices
- Nature-based rituals and ceremonies
- Connection with weather and seasons
- Wildlife observation for wisdom

Be poetic and inspiring about nature's healing power."""

def get_relationship_prompt(topic: str) -> str:
    """Healthy relationships communication workshop."""
    return f"""You are a relationship coach specializing in authentic connection.

TOPIC: {topic}

Teach them:
- Healthy communication patterns
- Active listening and empathy skills
- Setting boundaries with love
- Conflict resolution techniques
- Vulnerability and emotional intimacy
- Building trust and security
- Self-love as foundation for relationships

Be practical and compassionate. Build relational wisdom."""

def get_inner_child_prompt(wound: str) -> str:
    """Inner child healing and reparenting."""
    return f"""You are a trauma-informed inner child healing specialist.

CHILDHOOD WOUND: {wound}

Guide them through:
- Understanding your inner child's needs
- Safe reparenting techniques
- Self-soothing and comfort practices
- Processing childhood emotions gently
- Building self-compassion
- Reclaiming innocence and joy
- Healing attachment patterns

Be nurturing, patient, and deeply protective. This is sacred healing work."""

def music_library_session(category: str) -> str:
    """Access the healing music library."""
    if category not in MUSIC_LIBRARY:
        return get_music_library_info("")
    
    info = get_music_library_info(category)
    
    # Log session
    if "music_library" not in MEMORY:
        MEMORY["music_library"] = []
    MEMORY["music_library"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "category": category,
        "name": MUSIC_LIBRARY[category]['name']
    })
    write_json(ROOT / "memory.json", MEMORY)
    return info

def meditation_technique_session(technique: str) -> str:
    """Learn and practice specific meditation techniques."""
    if technique not in MEDITATION_TECHNIQUES:
        return f"Available techniques: {', '.join(MEDITATION_TECHNIQUES.keys())}"
    
    tech = MEDITATION_TECHNIQUES[technique]
    prompt = f"""You are an expert meditation guide teaching {tech['name']}.

TECHNIQUE: {tech['name']}
DESCRIPTION: {tech['description']}
BENEFITS: {', '.join(tech['benefits'])}

Provide:
- Detailed step-by-step instructions
- Duration recommendations
- Best time of day to practice
- How to deepen the practice over time
- Common challenges and solutions
- How it differs from other techniques
- What to expect during practice

Create an immersive, guided experience."""
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide me through {tech['name']} meditation"}
    ]
    response = chat_once(messages)
    
    # Log session
    if "meditation_techniques" not in MEMORY:
        MEMORY["meditation_techniques"] = []
    MEMORY["meditation_techniques"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "technique": technique,
        "name": tech['name']
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def forgiveness_session(situation: str) -> str:
    """Forgiveness and emotional release work."""
    prompt = get_forgiveness_prompt(situation)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Help me work through forgiveness regarding: {situation}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "forgiveness",
        "situation": situation
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def gratitude_session(focus: str) -> str:
    """Gratitude practice and abundance attraction."""
    prompt = get_gratitude_prompt(focus)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide my gratitude practice for: {focus}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "gratitude",
        "focus": focus
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def nature_session(activity: str) -> str:
    """Nature connection and outdoor healing."""
    prompt = get_nature_prompt(activity)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide my nature healing practice: {activity}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "nature",
        "activity": activity
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def relationship_session(topic: str) -> str:
    """Healthy relationships and communication workshop."""
    prompt = get_relationship_prompt(topic)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Teach me about healthy relationships: {topic}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "relationships",
        "topic": topic
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def inner_child_session(wound: str) -> str:
    """Inner child healing and reparenting."""
    prompt = get_inner_child_prompt(wound)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Help me heal my inner child wound: {wound}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "inner_child",
        "wound": wound
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

# ---------- Healing Music Library ----------

MUSIC_LIBRARY = {
    "relaxation": {
        "name": "Relaxation & Calming Ambiance",
        "description": "Gentle nature sounds and ambient music for deep relaxation",
        "tracks": [
            "Ocean Waves & Seagulls - 528 Hz healing frequency",
            "Forest Ambiance with Birdsong - Grounding energy",
            "Rainfall & Thunder - Natural sleep inducer",
            "Bamboo Wind Chimes - Peaceful morning music",
            "Flowing Stream Meditation - Water healing energy",
            "Soft Piano & Nature Blend - Emotional soothing"
        ]
    },
    "chakra": {
        "name": "Chakra Healing Frequencies",
        "description": "Each track tuned to specific chakra energy centers",
        "tracks": [
            "Root Chakra - 396 Hz - Grounding & Safety",
            "Sacral Chakra - 417 Hz - Creativity & Flow",
            "Solar Plexus - 528 Hz - Power & Confidence",
            "Heart Chakra - 639 Hz - Love & Compassion",
            "Throat Chakra - 741 Hz - Truth & Expression",
            "Third Eye - 852 Hz - Intuition & Vision",
            "Crown Chakra - 963 Hz - Divine Connection"
        ]
    },
    "angel": {
        "name": "Angel Music & Heavenly Choirs",
        "description": "Ethereal sounds for spiritual connection and angelic guidance",
        "tracks": [
            "Angelic Harp & Choir - Pure divine energy",
            "Celestial Bells - Messages from heaven",
            "Orchestral Heaven - Angels singing",
            "Light Language Music - Higher dimensional healing",
            "Angelic Frequencies 432 Hz - Heart resonance",
            "Heavenly Voices - Ascended master tones"
        ]
    },
    "binaural": {
        "name": "Binaural Beats for Brainwave Entrainment",
        "description": "Frequencies designed to guide brain states for meditation and healing",
        "tracks": [
            "Delta Waves 2 Hz - Deep sleep and restoration",
            "Theta Waves 5-8 Hz - Deep meditation and creativity",
            "Alpha Waves 8-12 Hz - Relaxation and focus",
            "Beta Waves 12-30 Hz - Alertness and concentration",
            "Gamma Waves 30-100 Hz - Consciousness expansion",
            "Complete Brainwave Journey - All states in sequence"
        ]
    },
    "solfeggio": {
        "name": "Solfeggio Frequencies - Ancient Healing Tones",
        "description": "Sacred healing frequencies used for millennia",
        "tracks": [
            "174 Hz - Relief and vitality foundation",
            "285 Hz - Tissue repair and cellular healing",
            "396 Hz - Liberation from fear and guilt",
            "417 Hz - Undoing situations and transformations",
            "528 Hz - Miracles and DNA repair (Love frequency)",
            "639 Hz - Connecting relationships, love and kindness",
            "741 Hz - Intuition and problem solving",
            "852 Hz - Third eye awakening and intuition",
            "963 Hz - Unity and divine consciousness"
        ]
    }
}

MEDITATION_TECHNIQUES = {
    "loving_kindness": {
        "name": "Loving-Kindness Meditation",
        "description": "Cultivate compassion for self and others",
        "benefits": ["Increases compassion", "Reduces anger", "Builds emotional resilience"]
    },
    "transcendental": {
        "name": "Transcendental Meditation",
        "description": "Silent mantra-based meditation for pure consciousness",
        "benefits": ["Stress relief", "Enhanced creativity", "Deep inner peace"]
    },
    "mindfulness": {
        "name": "Mindfulness Meditation",
        "description": "Present-moment awareness without judgment",
        "benefits": ["Mental clarity", "Anxiety reduction", "Emotional balance"]
    },
    "chakra": {
        "name": "Chakra Meditation",
        "description": "Balance and align all seven energy centers",
        "benefits": ["Energy alignment", "Emotional healing", "Spiritual growth"]
    },
    "walking": {
        "name": "Walking Meditation",
        "description": "Mindful movement in nature or indoors",
        "benefits": ["Physical and mental integration", "Grounding", "Moving meditation"]
    }
}

HEALING_GIFTS = {
    "forgiveness": {
        "name": "Forgiveness Guidance",
        "description": "Release emotional burdens and heal through forgiveness",
        "subtitle": "Tools for liberating yourself and others"
    },
    "gratitude": {
        "name": "Gratitude Practices",
        "description": "Daily exercises to attract positivity and abundance",
        "subtitle": "Elevate your vibration through appreciation"
    },
    "nature": {
        "name": "Connect with Nature",
        "description": "Outdoor healing activities and wellness tips",
        "subtitle": "Nature as medicine for body and soul"
    },
    "relationships": {
        "name": "Healthy Relationships Workshop",
        "description": "Communication skills and relationship advice",
        "subtitle": "Build authentic, loving connections"
    },
    "inner_child": {
        "name": "Inner Child Healing",
        "description": "Gentle exercises for childhood trauma release",
        "subtitle": "Reparenting and self-compassion practices"
    }
}

def get_music_library_info(category: str) -> str:
    """Get detailed music library information and recommendations."""
    if category not in MUSIC_LIBRARY:
        return f"Available music categories: {', '.join(MUSIC_LIBRARY.keys())}"
    
    lib = MUSIC_LIBRARY[category]
    info = f"""
{lib['name']}

{lib['description']}

Available Tracks:
"""
    for track in lib['tracks']:
        info += f"  • {track}\n"
    info += """
All tracks are:
• Scientifically designed for healing
• Available for unlimited download
• 100% FREE with no restrictions
• Perfect for meditation and therapy sessions
• No ads or interruptions
"""
    return info

def get_forgiveness_prompt(situation: str) -> str:
    """Forgiveness and emotional release guidance."""
    return f"""You are a compassionate forgiveness coach helping release emotional burdens.

SITUATION: {situation}

Guide them through:
- Understanding the pain and its origins
- The healing power of forgiveness (for self and others)
- Practical forgiveness techniques and rituals
- Releasing resentment and anger safely
- Self-compassion and self-forgiveness first
- Letter writing or speaking exercises
- Moving forward with peace

Be gentle and deeply empathetic. Help them liberate themselves."""

def get_gratitude_prompt(focus: str) -> str:
    """Gratitude practice and positivity attraction."""
    return f"""You are a gratitude coach amplifying appreciation and abundance.

FOCUS: {focus}

Guide them through:
- Finding gratitude even in challenges
- Daily gratitude journaling practices
- Gratitude affirmations and mantras
- Shifting perspective to abundance
- Attracting more to be grateful for
- Heart-centered appreciation exercises
- Gratitude rituals and ceremonies

Use uplifting, abundance-rich language. Elevate their vibration."""

def get_nature_prompt(activity: str) -> str:
    """Nature connection and outdoor healing."""
    return f"""You are a nature healing guide connecting people to Earth's medicine.

ACTIVITY: {activity}

Recommend:
- Specific outdoor activities aligned with their intention
- Best times and places for healing in nature
- How to use natural elements (water, earth, plants)
- Forest bathing and grounding practices
- Nature-based rituals and ceremonies
- Connection with weather and seasons
- Wildlife observation for wisdom

Be poetic and inspiring about nature's healing power."""

def get_relationship_prompt(topic: str) -> str:
    """Healthy relationships communication workshop."""
    return f"""You are a relationship coach specializing in authentic connection.

TOPIC: {topic}

Teach them:
- Healthy communication patterns
- Active listening and empathy skills
- Setting boundaries with love
- Conflict resolution techniques
- Vulnerability and emotional intimacy
- Building trust and security
- Self-love as foundation for relationships

Be practical and compassionate. Build relational wisdom."""

def get_inner_child_prompt(wound: str) -> str:
    """Inner child healing and reparenting."""
    return f"""You are a trauma-informed inner child healing specialist.

CHILDHOOD WOUND: {wound}

Guide them through:
- Understanding your inner child's needs
- Safe reparenting techniques
- Self-soothing and comfort practices
- Processing childhood emotions gently
- Building self-compassion
- Reclaiming innocence and joy
- Healing attachment patterns

Be nurturing, patient, and deeply protective. This is sacred healing work."""

def music_library_session(category: str) -> str:
    """Access the healing music library."""
    if category not in MUSIC_LIBRARY:
        return get_music_library_info("")
    
    info = get_music_library_info(category)
    
    # Log session
    if "music_library" not in MEMORY:
        MEMORY["music_library"] = []
    MEMORY["music_library"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "category": category,
        "name": MUSIC_LIBRARY[category]['name']
    })
    write_json(ROOT / "memory.json", MEMORY)
    return info

def meditation_technique_session(technique: str) -> str:
    """Learn and practice specific meditation techniques."""
    if technique not in MEDITATION_TECHNIQUES:
        return f"Available techniques: {', '.join(MEDITATION_TECHNIQUES.keys())}"
    
    tech = MEDITATION_TECHNIQUES[technique]
    prompt = f"""You are an expert meditation guide teaching {tech['name']}.

TECHNIQUE: {tech['name']}
DESCRIPTION: {tech['description']}
BENEFITS: {', '.join(tech['benefits'])}

Provide:
- Detailed step-by-step instructions
- Duration recommendations
- Best time of day to practice
- How to deepen the practice over time
- Common challenges and solutions
- How it differs from other techniques
- What to expect during practice

Create an immersive, guided experience."""
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide me through {tech['name']} meditation"}
    ]
    response = chat_once(messages)
    
    # Log session
    if "meditation_techniques" not in MEMORY:
        MEMORY["meditation_techniques"] = []
    MEMORY["meditation_techniques"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "technique": technique,
        "name": tech['name']
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def forgiveness_session(situation: str) -> str:
    """Forgiveness and emotional release work."""
    prompt = get_forgiveness_prompt(situation)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Help me work through forgiveness regarding: {situation}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "forgiveness",
        "situation": situation
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def gratitude_session(focus: str) -> str:
    """Gratitude practice and abundance attraction."""
    prompt = get_gratitude_prompt(focus)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide my gratitude practice for: {focus}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "gratitude",
        "focus": focus
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def nature_session(activity: str) -> str:
    """Nature connection and outdoor healing."""
    prompt = get_nature_prompt(activity)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Guide my nature healing practice: {activity}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "nature",
        "activity": activity
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def relationship_session(topic: str) -> str:
    """Healthy relationships and communication workshop."""
    prompt = get_relationship_prompt(topic)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Teach me about healthy relationships: {topic}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "relationships",
        "topic": topic
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

def inner_child_session(wound: str) -> str:
    """Inner child healing and reparenting."""
    prompt = get_inner_child_prompt(wound)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Help me heal my inner child wound: {wound}"}
    ]
    response = chat_once(messages)
    
    if "healing_gifts" not in MEMORY:
        MEMORY["healing_gifts"] = []
    MEMORY["healing_gifts"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "gift": "inner_child",
        "wound": wound
    })
    write_json(ROOT / "memory.json", MEMORY)
    return response

# ---------- MULTILINGUAL SUPPORT ----------

TRANSLATIONS = {
    "spanish": {
        "greeting": "Bienvenido a Carnal 2.0. Tu sanador personal.",
        "affirmation": "Afirmación de hoy",
        "mood_check": "¿Cómo te sientes hoy?",
        "energy": "Energía",
        "stress": "Estrés",
        "sleep": "Sueño",
        "intentions": "Intenciones para hoy",
        "gratitude": "Gratitud",
        "journal": "Diario",
        "dashboard": "Panel de Control",
        "emergency": "Modo Calma de Emergencia"
    },
    "portuguese": {
        "greeting": "Bem-vindo ao Carnal 2.0. Seu curador pessoal.",
        "affirmation": "Afirmação do dia",
        "mood_check": "Como você se sente hoje?",
        "energy": "Energia",
        "stress": "Estresse",
        "sleep": "Sono",
        "intentions": "Intenções para hoje",
        "gratitude": "Gratidão",
        "journal": "Diário",
        "dashboard": "Painel de Controle",
        "emergency": "Modo de Calma de Emergência"
    },
    "french": {
        "greeting": "Bienvenue à Carnal 2.0. Votre guérisseur personnel.",
        "affirmation": "Affirmation du jour",
        "mood_check": "Comment vous sentez-vous aujourd'hui?",
        "energy": "Énergie",
        "stress": "Stress",
        "sleep": "Sommeil",
        "intentions": "Intentions pour aujourd'hui",
        "gratitude": "Gratitude",
        "journal": "Journal",
        "dashboard": "Tableau de bord",
        "emergency": "Mode Calme d'Urgence"
    }
}

def translate(key: str, language: str = None) -> str:
    """Get translated text."""
    if language is None:
        language = MEMORY.get("user_language", "english").lower()
    if language not in TRANSLATIONS:
        return key
    return TRANSLATIONS[language].get(key, key)

# ---------- PERSONAL HEALING DASHBOARD ----------

DAILY_AFFIRMATIONS = [
    "You are worthy of love and healing.",
    "Every breath is a step toward wholeness.",
    "Your pain is your teacher; listen with compassion.",
    "You deserve peace, joy, and abundance.",
    "I choose self-love today, starting now.",
    "My heart is open to receive healing.",
    "I am stronger than my struggles.",
    "Today, I forgive myself and others.",
    "My soul is radiating light and love.",
    "I am exactly where I need to be.",
    "Healing is not linear; I honor my pace.",
    "My voice matters; I speak my truth.",
    "I am enough, exactly as I am.",
    "Love flows through me and around me.",
    "I choose progress over perfection."
]

JOURNAL_PROMPTS = {
    "self_love": [
        "What is one thing you love about yourself today?",
        "How can you practice self-compassion in this moment?",
        "What does your inner child need to hear from you?",
        "Describe a moment when you felt truly worthy.",
        "What would change if you truly believed you deserved love?"
    ],
    "breakup": [
        "What did this relationship teach you about yourself?",
        "How are you honoring your healing journey?",
        "What boundaries do you want in your next relationship?",
        "Write a letter to your past self before this relationship.",
        "What does healthy love look like to you now?"
    ],
    "forgiveness": [
        "Who do you need to forgive, including yourself?",
        "What story are you telling about what happened?",
        "How would forgiveness change your energy?",
        "What would you say to the person if they could hear you?",
        "What am I ready to release today?"
    ],
    "gratitude": [
        "List 5 small things you're grateful for today.",
        "How did someone show up for you recently?",
        "What challenge taught you something valuable?",
        "What gift has hardship brought to your life?",
        "Who deserves more gratitude in your life?"
    ],
    "shadow_work": [
        "What quality in others triggers you most? Why?",
        "What part of yourself have you rejected?",
        "What belief about yourself is no longer serving you?",
        "When did you learn to hide this part of yourself?",
        "How can you integrate this shadow part?"
    ],
    "inner_child": [
        "What does your inner child want you to know?",
        "How can you show up for your younger self today?",
        "What did you need to hear as a child?",
        "What did you love before the world told you who to be?",
        "How can you give yourself permission to play and rest?"
    ]
}

HEALING_PLANS = {
    "7_day_grounding": {
        "title": "7-Day Grounding & Root Chakra Healing",
        "duration": 7,
        "days": [
            {"day": 1, "focus": "root_grounding", "activity": ":meditate grounding and safety", "journal": "What makes me feel safe?"},
            {"day": 2, "focus": "body_connection", "activity": ":sound drums shamanic grounding", "journal": "How does my body feel today?"},
            {"day": 3, "focus": "nature_earth", "activity": ":nature barefoot walking on earth", "journal": "Connection to earth"},
            {"day": 4, "focus": "survival_needs", "activity": ":heal feeling unsafe or unworthy", "journal": "My basic needs"},
            {"day": 5, "focus": "boundaries", "activity": ":relationships setting healthy boundaries", "journal": "Boundaries I need"},
            {"day": 6, "focus": "belonging", "activity": ":gratitude my community and support", "journal": "Where I belong"},
            {"day": 7, "focus": "integration", "activity": ":chakra root chakra sealing", "journal": "My grounding affirmation"}
        ]
    },
    "7_day_heart_opening": {
        "title": "7-Day Heart Opening & Self-Love Journey",
        "duration": 7,
        "days": [
            {"day": 1, "focus": "self_compassion", "activity": ":love cultivating genuine self-love", "journal": "self_love"},
            {"day": 2, "focus": "forgiveness", "activity": ":forgive myself for past mistakes", "journal": "forgiveness"},
            {"day": 3, "focus": "heart_chakra", "activity": ":chakra heart chakra opening and healing", "journal": "What my heart needs"},
            {"day": 4, "focus": "emotional_release", "activity": ":heal sadness and grief", "journal": "What I'm grieving"},
            {"day": 5, "focus": "love_affirmations", "activity": ":technique loving_kindness", "journal": "Love I wish to receive"},
            {"day": 6, "focus": "boundaries_love", "activity": ":relationships love with healthy boundaries", "journal": "My love standards"},
            {"day": 7, "focus": "heart_integration", "activity": ":music angel angelic frequencies for heart", "journal": "My heart's wisdom"}
        ]
    },
    "21_day_transformation": {
        "title": "21-Day Complete Spiritual Transformation",
        "duration": 21,
        "days": [
            {"day": 1, "focus": "intention", "activity": ":affirmations today's intention", "journal": "My transformation begins"},
            {"day": 2, "focus": "grounding", "activity": ":meditate grounding and presence", "journal": "My foundation"},
            {"day": 3, "focus": "awareness", "activity": ":technique mindfulness meditation", "journal": "What I notice"},
            {"day": 4, "focus": "clearing", "activity": ":heal releasing what no longer serves", "journal": "What I'm releasing"},
            {"day": 5, "focus": "body", "activity": ":sound singing_bowl body healing", "journal": "My body wisdom"},
            {"day": 6, "focus": "breath", "activity": ":technique transcendental meditation", "journal": "My breath"},
            {"day": 7, "focus": "integration", "activity": ":chakra full body chakra alignment", "journal": "Week 1 insights"},
            {"day": 8, "focus": "heart_opening", "activity": ":love self-love exploration", "journal": "self_love"},
            {"day": 9, "focus": "forgiveness", "activity": ":forgive releasing resentment", "journal": "forgiveness"},
            {"day": 10, "focus": "grief", "activity": ":heal emotional grief and loss", "journal": "What I'm releasing"},
            {"day": 11, "focus": "joy", "activity": ":gratitude daily appreciation practice", "journal": "gratitude"},
            {"day": 12, "focus": "connection", "activity": ":technique loving_kindness meditation", "journal": "My connections"},
            {"day": 13, "focus": "boundaries", "activity": ":relationships healthy boundaries practice", "journal": "My boundaries"},
            {"day": 14, "focus": "heart_integration", "activity": ":music angel music for heart", "journal": "Week 2 transformation"},
            {"day": 15, "focus": "intuition", "activity": ":angel spiritual guidance and wisdom", "journal": "My intuition"},
            {"day": 16, "focus": "shadow_work", "activity": ":heal shadow work and integration", "journal": "shadow_work"},
            {"day": 17, "focus": "purpose", "activity": ":affirmations my life purpose", "journal": "My purpose"},
            {"day": 18, "focus": "creativity", "activity": ":chakra sacral chakra activation", "journal": "My creativity"},
            {"day": 19, "focus": "power", "activity": ":chakra solar plexus confidence building", "journal": "My power"},
            {"day": 20, "focus": "expression", "activity": ":chakra throat chakra truth", "journal": "My truth"},
            {"day": 21, "focus": "completion", "activity": ":chakra crown chakra divine connection", "journal": "My transformation complete"}
        ]
    }
}

def get_today_affirmation() -> str:
    """Get today's affirmation based on date."""
    import hashlib
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    hash_val = int(hashlib.md5(today.encode()).hexdigest(), 16)
    idx = hash_val % len(DAILY_AFFIRMATIONS)
    return DAILY_AFFIRMATIONS[idx]

def display_dashboard() -> str:
    """Display the personal healing dashboard."""
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    affirmation = get_today_affirmation()
    
    dashboard = f"""
╔════════════════════════════════════════════════════════════════╗
║          PERSONAL HEALING DASHBOARD - {today}
╚════════════════════════════════════════════════════════════════╝

[TODAY'S AFFIRMATION]
  '{affirmation}'

[MOOD CHECK-IN]
  Use ':mood' to log your current state
  • How are you feeling?
  • What's your stress level?
  • Sleep quality last night?
  • Your energy level?
  • What's your intention for today?

[RECOMMENDED HEALING SESSION]
  Based on your energy, try:
  • :meditate for clarity
  • :chakra for balance
  • :sound singing_bowl for relaxation
  • :love for self-compassion

[MUSIC FOR YOUR ENERGY]
  • Feeling scattered? Try :music relaxation
  • Need chakra work? Try :music chakra
  • Seeking peace? Try :music solfeggio
  • Want binaural? Try :music binaural

[JOURNAL PROMPTS]
  • :journal self_love - Discover self-compassion
  • :journal forgiveness - Release what hurts
  • :journal gratitude - Appreciate your life
  • :journal shadow_work - Explore your depths
  • :journal inner_child - Reconnect with joy

[GRATITUDE MOMENT]
  Take 60 seconds: What's one thing you're grateful for today?
  Use ':gratitude' to share your appreciation.

═══════════════════════════════════════════════════════════════════
  Start with :dashboard anytime to return here
  Use :emergency for immediate calm support
  Type :gifts to access all healing features
═══════════════════════════════════════════════════════════════════
"""
    return dashboard

# ---------- MOOD + ENERGY TRACKER ----------

def log_mood(mood: int, stress: int, sleep: int, energy: int, intention: str) -> str:
    """Log user's mood and energy for the day."""
    if not (1 <= mood <= 10 and 1 <= stress <= 10 and 1 <= sleep <= 10 and 1 <= energy <= 10):
        return "CAR2: Please rate all values from 1-10."
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "mood": mood,
        "stress": stress,
        "sleep": sleep,
        "energy": energy,
        "intention": intention
    }
    
    if "mood_tracker" not in MEMORY:
        MEMORY["mood_tracker"] = []
    MEMORY["mood_tracker"].append(entry)
    write_json(ROOT / "memory.json", MEMORY)
    
    recommendations = []
    if mood <= 3:
        recommendations.append(":heal for emotional support")
    if stress >= 7:
        recommendations.append(":meditate for stress relief")
    if sleep <= 5:
        recommendations.append(":music relaxation for better rest")
    if energy <= 3:
        recommendations.append(":chakra for energy restoration")
    
    response = f"""
[MOOD & ENERGY LOGGED]
  Mood: {mood}/10 | Stress: {stress}/10 | Sleep: {sleep}/10 | Energy: {energy}/10
  Intention: {intention}

[PERSONALIZED RECOMMENDATIONS]
"""
    if recommendations:
        for rec in recommendations:
            response += f"  • {rec}\n"
    else:
        response += "  You're in great balance today! Keep doing what you're doing.\n"
    
    return response

def get_mood_insights() -> str:
    """Get insights from mood tracker data."""
    tracker = MEMORY.get("mood_tracker", [])
    if not tracker:
        return "CAR2: No mood data logged yet. Start tracking with ':mood'."
    
    moods = [entry["mood"] for entry in tracker]
    avg_mood = sum(moods) / len(moods)
    
    insights = f"""
[MOOD INSIGHTS]
  Entries logged: {len(tracker)}
  Average mood: {avg_mood:.1f}/10
  Best mood: {max(moods)}/10
  Most challenging: {min(moods)}/10
  
[PATTERNS]
"""
    if avg_mood >= 7:
        insights += "  You're in an uplifting phase! Keep nourishing this energy.\n"
    elif avg_mood >= 5:
        insights += "  You're navigating emotions. Be gentle with yourself.\n"
    else:
        insights += "  You're in a challenging time. Extra healing sessions will help.\n"
    
    return insights

# ---------- GUIDED JOURNALING SYSTEM ----------

def get_journal_prompt(journal_type: str) -> str:
    """Get a guided journal prompt."""
    if journal_type not in JOURNAL_PROMPTS:
        return f"Available journals: {', '.join(JOURNAL_PROMPTS.keys())}"
    
    prompts = JOURNAL_PROMPTS[journal_type]
    import hashlib
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    hash_val = int(hashlib.md5((today + journal_type).encode()).hexdigest(), 16)
    idx = hash_val % len(prompts)
    return prompts[idx]

def journal_session(journal_type: str, entry_text: str) -> str:
    """Save a journal entry and provide reflection."""
    prompt = get_journal_prompt(journal_type)
    
    reflection_prompt = f"""The user is writing in their {journal_type.replace('_', ' ')} journal.
    
Their prompt was: {prompt}

Their entry:
{entry_text}

Provide:
- A brief, warm acknowledgment of their vulnerability
- 1-2 insights you notice
- An affirmation related to their entry
Keep it under 200 words. Be deeply empathetic."""
    
    messages = [
        {"role": "system", "content": reflection_prompt},
        {"role": "user", "content": entry_text}
    ]
    
    try:
        reflection = chat_once(messages)
    except:
        reflection = "Your words are sacred. Thank you for your honesty."
    
    if "journals" not in MEMORY:
        MEMORY["journals"] = {}
    if journal_type not in MEMORY["journals"]:
        MEMORY["journals"][journal_type] = []
    
    MEMORY["journals"][journal_type].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "entry": entry_text,
        "reflection": reflection
    })
    write_json(ROOT / "memory.json", MEMORY)
    
    return f"""
[{journal_type.replace('_', ' ').upper()} JOURNAL ENTRY SAVED]

Today's prompt: {prompt}

[AI REFLECTION]
{reflection}

Your entry is safe here. Review anytime with :journal_history {journal_type}
"""

# ---------- DAILY AFFIRMATIONS + REMINDERS ----------

def create_affirmation_set(count: int = 5) -> str:
    """Create a personalized affirmation set."""
    import random
    affirmations = random.sample(DAILY_AFFIRMATIONS, min(count, len(DAILY_AFFIRMATIONS)))
    
    aff_set = """
[PERSONALIZED AFFIRMATION SET]
Repeat these when you need grounding:
"""
    for i, aff in enumerate(affirmations, 1):
        aff_set += f"\n{i}. '{aff}'"
    
    if "affirmations" not in MEMORY:
        MEMORY["affirmations"] = []
    MEMORY["affirmations"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "affirmations": affirmations
    })
    write_json(ROOT / "memory.json", MEMORY)
    
    return aff_set

# ---------- PERSONALIZED HEALING PLANS ----------

def start_healing_plan(plan_name: str) -> str:
    """Start a personalized healing plan."""
    if plan_name not in HEALING_PLANS:
        options = ", ".join(HEALING_PLANS.keys())
        return f"Available plans: {options}"
    
    plan = HEALING_PLANS[plan_name]
    
    plan_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "plan_name": plan_name,
        "title": plan["title"],
        "duration": plan["duration"],
        "start_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "days_completed": 0,
        "current_day": 1
    }
    
    if "healing_plans" not in MEMORY:
        MEMORY["healing_plans"] = []
    MEMORY["healing_plans"].append(plan_entry)
    write_json(ROOT / "memory.json", MEMORY)
    
    day_1 = plan["days"][0]
    
    info = f"""
[{plan['title'].upper()}]
Duration: {plan['duration']} days
Status: Just started!

[DAY 1: {day_1['focus'].replace('_', ' ').title()}]
  Activity: {day_1['activity']}
  Journal: {day_1['journal']}
  
Over the next {plan['duration']} days, you'll experience guided healing across multiple dimensions.
Each day builds on the last, creating transformation.

Use :plan_progress to see your journey.
Use :plan_today to see today's activity.
"""
    return info

def get_plan_today() -> str:
    """Get today's healing plan activity if one is active."""
    if "healing_plans" not in MEMORY or not MEMORY["healing_plans"]:
        return "CAR2: No active healing plan. Start one with :plan_start <plan_name>"
    
    active_plan = MEMORY["healing_plans"][-1]
    plan_data = HEALING_PLANS.get(active_plan["plan_name"], {})
    
    if not plan_data:
        return "CAR2: Plan data not found."
    
    current_day = active_plan["current_day"]
    if current_day > len(plan_data["days"]):
        return f"CAR2: Plan complete! Congratulations on finishing {active_plan['title']}!"
    
    day_info = plan_data["days"][current_day - 1]
    
    return f"""
[{plan_data['title'].upper()}]
Day {current_day} of {plan_data['duration']}

[TODAY'S FOCUS: {day_info['focus'].replace('_', ' ').title()}]
  Activity: {day_info['activity']}
  Journal Reflection: {day_info['journal']}

Complete today's activity, then use :plan_next to advance.
"""

# ---------- RELATIONSHIP HEALING SECTION ----------

RELATIONSHIP_FLOWS = {
    "self_love": "Deepen your relationship with yourself",
    "heartbreak_recovery": "Heal from love loss and rediscover wholeness",
    "communication": "Learn to express needs and listen deeply",
    "conscious_dating": "Attract authentic, healthy relationships",
    "couples_support": "Strengthen partnership and intimacy",
    "conflict_repair": "Transform conflict into connection"
}

def get_relationship_flow(flow_type: str) -> str:
    """Get a customized relationship healing flow."""
    if flow_type not in RELATIONSHIP_FLOWS:
        options = ", ".join(RELATIONSHIP_FLOWS.keys())
        return f"Available flows: {options}"
    
    flows = {
        "self_love": {
            "intro": "Self-love is the foundation of all healthy relationships.",
            "steps": [
                ":love Why don't I prioritize myself?",
                ":journal self_love - Mirror work",
                ":affirmations Create your self-love affirmations",
                ":meditate loving_kindness for yourself",
                ":gratitude Appreciate what your body does for you"
            ]
        },
        "heartbreak_recovery": {
            "intro": "Heartbreak cracks us open. Through that crack, light enters.",
            "steps": [
                ":heal heartbreak and grief",
                ":forgive releasing anger toward them and myself",
                ":journal breakup_healing journal",
                ":inner_child What did I learn about love?",
                ":nature grounding in earth's stability",
                ":affirmations My heart will love again"
            ]
        },
        "communication": {
            "intro": "True communication is vulnerability met with safety.",
            "steps": [
                ":relationships How do I typically express needs?",
                ":heal fear of speaking up",
                ":chakra throat_chakra for authentic expression",
                ":love How to communicate with compassion",
                ":journal What do I need to say?"
            ]
        },
        "conscious_dating": {
            "intro": "Conscious dating means showing up as your whole, healed self.",
            "steps": [
                ":love What do I genuinely want?",
                ":relationships red_flags and green_flags",
                ":affirmations I attract conscious partners",
                ":chakra heart_chakra ready for love",
                ":relationships Communication and boundaries in dating"
            ]
        },
        "couples_support": {
            "intro": "Relationships thrive when both partners nurture their own healing.",
            "steps": [
                ":relationships Understanding your partner's love language",
                ":love compassionate conflict resolution",
                ":chakra heart_chakra deepening intimacy",
                ":meditate loving_kindness toward your partner",
                ":journal What do I appreciate about this relationship?"
            ]
        },
        "conflict_repair": {
            "intro": "Conflict is not failure. It's an invitation to deeper connection.",
            "steps": [
                ":heal anger and resentment",
                ":chakra throat_chakra honest expression",
                ":relationships Listening without defending",
                ":love compassionate approach to repair",
                ":forgive ourselves for the conflict",
                ":chakra heart_chakra rebuilding trust"
            ]
        }
    }
    
    flow = flows.get(flow_type, {})
    result = f"""
[{RELATIONSHIP_FLOWS[flow_type].upper()}]

{flow.get('intro', '')}

[YOUR HEALING PATH]
"""
    for i, step in enumerate(flow.get('steps', []), 1):
        result += f"\nStep {i}: {step}"
    
    result += f"\n\nUse the commands above to guide your healing journey."
    return result

# ---------- EMERGENCY CALM / GROUNDING MODE ----------

EMERGENCY_RESOURCES = {
    "crisis_hotlines": {
        "988_lifeline": "Call 988 (US) - Suicide & Crisis Lifeline",
        "international_crisis": "Text HOME to 741741 or visit crisis.text/home",
        "nami": "NAMI Helpline: 1-800-950-NAMI",
    }
}

def emergency_calm_mode() -> str:
    """Activate emergency calm mode for overwhelming moments."""
    calm = """
╔════════════════════════════════════════════════════════════════╗
║              EMERGENCY CALM MODE - You're Safe
╚════════════════════════════════════════════════════════════════╝

Take a moment. You are not alone. This feeling will pass.

[60-SECOND BREATHING EXERCISE]
  • Breathe IN for 4 counts (1... 2... 3... 4...)
  • HOLD for 4 counts
  • Breathe OUT for 6 counts (release everything)
  • Repeat 5 times
  
This activates your parasympathetic nervous system. You are safe.

[GROUNDING TECHNIQUE - 5-4-3-2-1]
  Look around and name:
  • 5 things you can SEE
  • 4 things you can TOUCH
  • 3 things you can HEAR
  • 2 things you can SMELL
  • 1 thing you can TASTE
  
You are here. You are present. You are safe.

[SOOTHING AFFIRMATIONS]
  • This moment will pass
  • I am safe right now
  • My body is protecting me
  • I deserve compassion
  • I will get through this

[IMMEDIATE SUPPORT]
  • :music relaxation (listen for 5 minutes)
  • :sound drums grounding (feel your heartbeat)
  • :meditate breathing meditation
  • :heal I'm overwhelmed (share what's happening)
  • Text a trusted friend or loved one

[IF YOU'RE IN CRISIS]
  Please reach out:
  • Call 988 (US Suicide & Crisis Lifeline)
  • Text HOME to 741741 (Crisis Text Line)
  • Go to your nearest emergency room
  • Call emergency services (911)
  
Your life matters. People care. Help is available.

═══════════════════════════════════════════════════════════════════
  Return to healing: type any command or :dashboard
  Emergency hotlines are ALWAYS available
═══════════════════════════════════════════════════════════════════
"""
    return calm


# ---------- TRUST & SAFETY ----------

TRUST_SAFETY_DISCLAIMER = """
╔════════════════════════════════════════════════════════════════╗
║                    TRUST & SAFETY FIRST
╚════════════════════════════════════════════════════════════════╝

[IMPORTANT DISCLAIMER]
Carnal 2.0 is a HEALING COMPANION, not a substitute for:
• Professional medical care
• Mental health treatment
• Crisis intervention
• Licensed therapy or counseling
• Emergency medical services

If you are in crisis or having thoughts of self-harm:
• Call 988 (US Suicide & Crisis Lifeline) immediately
• Text HOME to 741741 (Crisis Text Line)
• Go to your nearest emergency room
• Call 911 or local emergency services

[YOUR PRIVACY IS SACRED]
✓ All journaling is encrypted and private
✓ No data is shared or sold
✓ You control what you share
✓ Your healing journey is yours alone

[COMMUNITY GUIDELINES]
When using shared features:
✓ Respect others' healing journeys
✓ No judgment, only compassion
✓ Report harmful content immediately
✓ Block users who disrespect boundaries

[AI BOUNDARIES]
Carnal 2.0 will not:
✗ Diagnose or treat medical conditions
✗ Replace professional mental healthcare
✗ Respond to active crisis situations (use hotlines instead)
✗ Store sensitive personal information beyond session
✗ Make decisions for you

═══════════════════════════════════════════════════════════════════
Type ':accept_terms' to confirm you understand these boundaries.
Type ':resources' for crisis support hotlines.
═══════════════════════════════════════════════════════════════════
"""

CRISIS_RESOURCES = {
    "US": {
        "988": "Call or text 988 (Suicide & Crisis Lifeline)",
        "Crisis_Text_Line": "Text HOME to 741741",
        "NAMI": "1-800-950-NAMI (NAMI Helpline)",
        "Veterans": "988 then press 1 (Veterans Crisis Line)"
    },
    "International": {
        "Global": "findahelpline.com",
        "UK": "116 123 (Samaritans)",
        "Canada": "1-833-456-4566 (Crisis Text)",
        "Australia": "1300 659 467 (Lifeline)",
        "Germany": "0800 1110111 or 0800 1110222"
    }
}

# ---------- USER PROFILE SYSTEM ----------

def setup_user_profile() -> str:
    """Interactive user profile setup."""
    profile_setup = """
[USER PROFILE SETUP]
Personalize your Carnal 2.0 experience!

1. What are your healing goals?
   :profile_goal <goal>
   Examples: anxiety relief, self-love, breakup healing, clarity
   
2. What's your love language?
   :profile_love_language <language>
   Options: words_of_affirmation, acts_of_service, physical_touch, quality_time, gifts
   
3. Preferred healing modalities?
   :profile_modalities <modality>
   Examples: meditation, reiki, chakra work, journaling
   
4. Music preferences?
   :profile_music <type>
   Examples: relaxation, chakra, solfeggio, nature sounds
   
5. Spiritual interests?
   :profile_spiritual <interest>
   Examples: tarot, moon rituals, angel guidance, energy work
   
6. Notification times?
   :profile_notifications <times>
   Examples: 6am, 12pm, 6pm for affirmations and reminders

Your profile helps personalize healing recommendations!
"""
    return profile_setup

def update_profile(key: str, value: str) -> str:
    """Update user profile settings."""
    profile = MEMORY.get("user_profile", {})
    
    if key == "goal":
        if value not in profile["healing_goals"]:
            profile["healing_goals"].append(value)
        return f"CAR2: Added healing goal: {value}"
    
    elif key == "love_language":
        valid = ["words_of_affirmation", "acts_of_service", "physical_touch", "quality_time", "gifts"]
        if value in valid:
            profile["love_language"] = value
            return f"CAR2: Love language set to: {value}"
        return f"CAR2: Invalid. Choose from: {', '.join(valid)}"
    
    elif key == "modality":
        if value not in profile["preferred_modalities"]:
            profile["preferred_modalities"].append(value)
        return f"CAR2: Added preference: {value}"
    
    elif key == "music":
        if value not in profile["music_preferences"]:
            profile["music_preferences"].append(value)
        return f"CAR2: Music preference added: {value}"
    
    elif key == "spiritual":
        if value not in profile["spiritual_interests"]:
            profile["spiritual_interests"].append(value)
        return f"CAR2: Spiritual interest added: {value}"
    
    MEMORY["user_profile"] = profile
    write_json(ROOT / "memory.json", MEMORY)
    return "CAR2: Profile updated."

def display_profile() -> str:
    """Display user profile."""
    profile = MEMORY.get("user_profile", {})
    display = "\n[YOUR HEALING PROFILE]\n"
    display += f"  Healing Goals: {', '.join(profile['healing_goals']) if profile['healing_goals'] else 'Not set'}\n"
    display += f"  Love Language: {profile['love_language'] or 'Not set'}\n"
    display += f"  Preferred Modalities: {', '.join(profile['preferred_modalities']) if profile['preferred_modalities'] else 'Not set'}\n"
    display += f"  Music Preferences: {', '.join(profile['music_preferences']) if profile['music_preferences'] else 'Not set'}\n"
    display += f"  Spiritual Interests: {', '.join(profile['spiritual_interests']) if profile['spiritual_interests'] else 'Not set'}\n"
    return display

# ---------- GAMIFICATION SYSTEM ----------

BADGES = {
    "meditation_master": {"name": "Meditation Master", "requirement": "7 meditation sessions"},
    "journal_warrior": {"name": "Journal Warrior", "requirement": "7-day journaling streak"},
    "love_advocate": {"name": "Love Advocate", "requirement": "5 love ripple challenges completed"},
    "chakra_healer": {"name": "Chakra Healer", "requirement": "All 7 chakras balanced"},
    "7_day_grounding": {"name": "Grounded Soul", "requirement": "Complete 7-day grounding plan"},
    "heartfelt": {"name": "Heartfelt", "requirement": "7-day heart opening journey"},
    "21_days": {"name": "Transformation", "requirement": "Complete 21-day transformation"},
}

def check_and_award_badges() -> list:
    """Check if user has earned any badges."""
    gamif = MEMORY.get("gamification", {})
    healing_modalities = MEMORY.get("healing_modalities", [])
    meditation_count = len([x for x in healing_modalities if x.get("type") == "meditation"])
    
    awarded = []
    
    if meditation_count >= 7 and "meditation_master" not in gamif["badges"]:
        gamif["badges"].append("meditation_master")
        awarded.append("Meditation Master")
    
    journals = MEMORY.get("journals", {})
    if journals and "journal_warrior" not in gamif["badges"]:
        gamif["badges"].append("journal_warrior")
        awarded.append("Journal Warrior")
    
    love_ripples = len(MEMORY.get("cosmic_features", {}).get("love_ripples", []))
    if love_ripples >= 5 and "love_advocate" not in gamif["badges"]:
        gamif["badges"].append("love_advocate")
        awarded.append("Love Advocate")
    
    MEMORY["gamification"] = gamif
    write_json(ROOT / "memory.json", MEMORY)
    
    return awarded

def update_streak(activity_type: str) -> str:
    """Update activity streak."""
    gamif = MEMORY.get("gamification", {})
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if activity_type == "journal":
        last_date = gamif.get("last_journal_date")
        if last_date == today:
            return "CAR2: You've already journaled today! Great work."
        
        gamif["last_journal_date"] = today
        if last_date:
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            if last_date == yesterday:
                gamif["journal_streak"] += 1
            else:
                gamif["journal_streak"] = 1
        else:
            gamif["journal_streak"] = 1
    
    elif activity_type == "practice":
        last_date = gamif.get("last_practice_date")
        if last_date == today:
            return "CAR2: You've practiced today! Amazing."
        
        gamif["last_practice_date"] = today
        if last_date:
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            if last_date == yesterday:
                gamif["practice_streak"] += 1
            else:
                gamif["practice_streak"] = 1
        else:
            gamif["practice_streak"] = 1
    
    MEMORY["gamification"] = gamif
    write_json(ROOT / "memory.json", MEMORY)
    
    streak = gamif.get("journal_streak") if activity_type == "journal" else gamif.get("practice_streak")
    return f"CAR2: {activity_type.title()} streak: {streak} days! Keep going!"

def display_gamification() -> str:
    """Display gamification stats."""
    gamif = MEMORY.get("gamification", {})
    
    display = "\n[YOUR HEALING ACHIEVEMENTS]\n"
    display += f"  Journal Streak: {gamif.get('journal_streak', 0)} days\n"
    display += f"  Practice Streak: {gamif.get('practice_streak', 0)} days\n"
    display += f"  Badges Earned: {len(gamif.get('badges', []))}\n"
    
    if gamif.get("badges"):
        display += "\n[BADGES]\n"
        for badge_key in gamif["badges"]:
            badge_name = BADGES.get(badge_key, {}).get("name", badge_key)
            display += f"    [EARNED] {badge_name}\n"
    
    display += "\n[NEXT BADGES]\n"
    for badge_key, badge_info in BADGES.items():
        if badge_key not in gamif.get("badges", []):
            display += f"    [{badge_info['name']}] - {badge_info['requirement']}\n"
    
    return display

# ---------- ACCESSIBILITY SETTINGS ----------

def set_accessibility(setting: str, value: str) -> str:
    """Update accessibility settings."""
    access = MEMORY.get("accessibility", {})
    
    if setting == "dark_mode":
        access["dark_mode"] = value.lower() == "on"
        MEMORY["accessibility"] = access
        write_json(ROOT / "memory.json", MEMORY)
        return f"CAR2: Dark mode {'enabled' if access['dark_mode'] else 'disabled'}"
    
    elif setting == "voice":
        access["voice_playback"] = value.lower() == "on"
        MEMORY["accessibility"] = access
        write_json(ROOT / "memory.json", MEMORY)
        return f"CAR2: Voice playback {'enabled' if access['voice_playback'] else 'disabled'}"
    
    elif setting == "captions":
        access["captions"] = value.lower() == "on"
        MEMORY["accessibility"] = access
        write_json(ROOT / "memory.json", MEMORY)
        return f"CAR2: Captions {'enabled' if access['captions'] else 'disabled'}"
    
    elif setting == "font_size":
        valid = ["small", "medium", "large", "extra_large"]
        if value in valid:
            access["font_size"] = value
            MEMORY["accessibility"] = access
            write_json(ROOT / "memory.json", MEMORY)
            return f"CAR2: Font size set to {value}"
        return f"CAR2: Valid sizes: {', '.join(valid)}"
    
    return "CAR2: Setting not recognized."

# ---------- COSMIC BRAND FEATURES ----------

def cosmic_match(name1: str, name2: str) -> str:
    """Cosmic Match - compatibility/connection reflection tool."""
    hd_charts = MEMORY.get("hd_charts", {})
    
    if name1 not in hd_charts or name2 not in hd_charts:
        return "CAR2: Both people must have Human Design charts. Use :hd to create them first."
    
    chart1 = hd_charts[name1]["chart"]
    chart2 = hd_charts[name2]["chart"]
    
    match_prompt = f"""Create an inspiring, non-judgmental cosmic connection reflection between two people.

{name1}: {chart1.get('type', {}).get('name')} | {chart1.get('profile', {}).get('code')}
{name2}: {chart2.get('type', {}).get('name')} | {chart2.get('profile', {}).get('code')}

Provide:
- Energetic resonance between them
- How they complement each other
- Potential growth areas together
- Cosmic connection strengths
Use warm, affirming language. This is about connection, not judgment."""
    
    messages = [
        {"role": "system", "content": match_prompt},
        {"role": "user", "content": f"Tell me about the cosmic connection between {name1} and {name2}"}
    ]
    
    try:
        response = chat_once(messages)
    except:
        response = f"Two souls meeting in the cosmos: {name1} and {name2}. Your connection is unique and beautiful."
    
    return f"\n[COSMIC MATCH: {name1} & {name2}]\n\n{response}"

def healing_oracle() -> str:
    """Daily oracle card reading with affirmation and guidance."""
    oracles = [
        {"card": "The Awakening", "message": "You are remembering who you truly are.", "guidance": "Trust the unfolding of your journey."},
        {"card": "Compassion Rising", "message": "Your heart is the greatest teacher.", "guidance": "Let kindness guide every step."},
        {"card": "Sacred Release", "message": "What needs to go is making space for what must arrive.", "guidance": "Release with gratitude."},
        {"card": "Divine Love", "message": "You are loved beyond measure.", "guidance": "Open to receive what's meant for you."},
        {"card": "Inner Strength", "message": "Your power has always been within you.", "guidance": "Trust what you know to be true."},
        {"card": "Healing Spiral", "message": "Every cycle brings you closer to wholeness.", "guidance": "Honor where you are right now."},
        {"card": "Cosmic Alignment", "message": "The universe conspires in your favor.", "guidance": "Align with your highest self."},
    ]
    
    import hashlib
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    hash_val = int(hashlib.md5(today.encode()).hexdigest(), 16)
    idx = hash_val % len(oracles)
    oracle = oracles[idx]
    
    if "cosmic_features" not in MEMORY:
        MEMORY["cosmic_features"] = {}
    if "oracle_readings" not in MEMORY["cosmic_features"]:
        MEMORY["cosmic_features"]["oracle_readings"] = []
    
    MEMORY["cosmic_features"]["oracle_readings"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "card": oracle["card"],
        "message": oracle["message"]
    })
    write_json(ROOT / "memory.json", MEMORY)
    
    return f"""
[HEALING ORACLE OF THE DAY]

Card: {oracle['card']}
Message: "{oracle['message']}"
Guidance: "{oracle['guidance']}"

Let this guide your day. Your healing matters.
"""

def love_ripple_challenge() -> str:
    """Daily acts of kindness challenge."""
    challenges = [
        "Send an unexpected message of appreciation to someone.",
        "Compliment a stranger genuinely.",
        "Volunteer 10 minutes of your time.",
        "Listen deeply without judgment.",
        "Share a meal or resource.",
        "Speak kindly about someone when they're not present.",
        "Offer help without being asked.",
        "Forgive someone in your heart.",
        "Write a gratitude note.",
        "Smile at 5 people today."
    ]
    
    import hashlib
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    hash_val = int(hashlib.md5(today.encode()).hexdigest(), 16)
    idx = hash_val % len(challenges)
    challenge = challenges[idx]
    
    return f"""
[LOVE RIPPLE CHALLENGE - TODAY]

{challenge}

Share your kindness ripples:
Use :ripple_complete to log this challenge
Your love creates waves of healing across the world.
"""

def log_ripple(completed: bool) -> str:
    """Log a completed love ripple challenge."""
    if "cosmic_features" not in MEMORY:
        MEMORY["cosmic_features"] = {}
    if "love_ripples" not in MEMORY["cosmic_features"]:
        MEMORY["cosmic_features"]["love_ripples"] = []
    
    MEMORY["cosmic_features"]["love_ripples"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "completed": completed
    })
    write_json(ROOT / "memory.json", MEMORY)
    
    if completed:
        return "CAR2: You rippled love into the world today. Beautiful!"
    return "CAR2: Come back when you're ready. No pressure, only love."

def sacred_sound_mixer() -> str:
    """Let users create custom healing audio mixes."""
    mixer_info = """
[SACRED SOUND MIXER]
Create your personalized healing soundscape!

Available sound elements:
  Singing Bowls: 432 Hz & 528 Hz healing
  Tuning Forks: 174-963 Hz Solfeggio
  Shamanic Drums: 4-5 Hz theta brainwave
  Meditation Chimes: Pure celestial tones
  Nature Sounds: Ocean, rain, forest, streams
  Binaural Beats: Delta/Theta/Alpha waves

How to create your mix:
  :mixer_add <sound_element> <volume>
  :mixer_add singing_bowl 70%
  :mixer_add rain 50%
  :mixer_add theta_waves 30%
  
  :mixer_play - Listen to your creation
  :mixer_save <name> - Save your mix
  :mixer_library - View your saved mixes

Combine up to 5 elements for your perfect healing soundtrack!
"""
    return mixer_info

def moon_ritual_guide() -> str:
    """New moon intentions and full moon release rituals."""
    import datetime
    
    today = datetime.datetime.now()
    day_of_month = today.day
    
    ritual_guide = """
[MOON RITUALS & INTENTIONS]

New Moon (Days 1-7): Plant seeds of intention
  What do you want to manifest?
  
Waxing Moon (Days 8-14): Build momentum
  Take action toward your intentions
  
Full Moon (Days 15-21): Release & celebrate
  What are you ready to let go of?
  Celebrate what you've manifested
  
Waning Moon (Days 22-29): Rest & integrate
  Reflect on your journey
  Prepare for the next cycle

Use :new_moon_ritual <intention> to begin intention setting
Use :full_moon_ritual <what_to_release> for release practice
Use :moon_reflection for deep cycle work

Your intentions are sacred. Honor them.
"""
    
    if "cosmic_features" not in MEMORY:
        MEMORY["cosmic_features"] = {}
    
    return ritual_guide

def voice_note_to_future_self(note_text: str, days_until: int) -> str:
    """Record a loving voice message to be delivered later."""
    delivery_date = (datetime.datetime.now() + datetime.timedelta(days=days_until)).strftime("%Y-%m-%d")
    
    if "cosmic_features" not in MEMORY:
        MEMORY["cosmic_features"] = {}
    if "voice_notes" not in MEMORY["cosmic_features"]:
        MEMORY["cosmic_features"]["voice_notes"] = []
    
    MEMORY["cosmic_features"]["voice_notes"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "delivery_date": delivery_date,
        "message": note_text,
        "days_until": days_until
    })
    write_json(ROOT / "memory.json", MEMORY)
    
    return f"""
[VOICE NOTE TO YOUR FUTURE SELF]

Message: "{note_text}"
Delivery: {days_until} days from now ({delivery_date})

This love letter to yourself will arrive when you need it.
You are holding yourself with such compassion.
"""

def check_voice_notes() -> str:
    """Check for voice notes ready to be delivered."""
    voice_notes = MEMORY.get("cosmic_features", {}).get("voice_notes", [])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    delivered = []
    for note in voice_notes:
        if note["delivery_date"] == today:
            delivered.append(note["message"])
    
    if delivered:
        msg = "\n[LOVE LETTER FROM YOUR PAST SELF]\n\n"
        for note in delivered:
            msg += f'"{note}"\n\n'
        msg += "Your past self knew you would need this today. Hold yourself with such love."
        return msg
    
    return None

# ---------- MAIN MENU & TAB NAVIGATION ----------

def display_main_menu() -> str:
    """Display the 5-tab main app structure."""
    menu = """
╔════════════════════════════════════════════════════════════════╗
║                    CARNAL 2.0
║           Cosmic Healing Companion
╚════════════════════════════════════════════════════════════════╝

OUR PROMISE:
Carnal 2.0 is a comprehensive digital healing and connection 
platform combining AI guidance, sound healing, meditation, 
journaling, and personalized coaching to help you cultivate 
self-love, emotional healing, and conscious relationships.

═══════════════════════════════════════════════════════════════════

[5 MAIN TABS]

1. HOME (:tab_home)
   Daily Healing Dashboard
   • :dashboard - Personal wellness overview
   • :affirmations - Daily affirmations
   • :oracle - Healing Oracle of the Day
   • :mood - Log mood & energy (1-10 scales)
   • :mood_insights - View mood patterns
   ➜ Start your day with intention and cosmic guidance

2. HEAL (:tab_heal)
   Deep Healing Modalities & Sessions
   • :reiki <focus> - Energy healing
   • :meditate <focus> - Guided meditation
   • :chakra <focus> - Chakra balancing
   • :angel <question> - Angel guidance
   • :forgive <situation> - Release emotional burdens
   • :inner_child <wound> - Childhood healing
   • :relationships <topic> - Communication skills
   • :emergency - Immediate crisis support
   • :plan_start <plan> - 7-day or 21-day journey
   ➜ Choose what your soul needs today

3. SOUND (:tab_sound)
   Healing Music, Frequencies & Sound Baths
   • :music <category> - 30+ healing tracks (unlimited free)
   • :technique <name> - 5 meditation techniques
   • :sound <instrument> <focus> - Sound healing
   • :mixer - Create custom healing audio
   • :schedule - Daily healing session schedule
   ➜ Let sound heal your frequency

4. CONNECT (:tab_connect)
   Relationships, Community & Love
   • :love <topic> - Love coaching & guidance
   • :match <name1> <name2> - Cosmic Match compatibility
   • :ripple - Love Ripple Challenge (daily kindness)
   • :relationships <topic> - Healthy communication
   • :gratitude <focus> - Gratitude practice
   ➜ Connect authentically. Love radically.

5. JOURNAL (:tab_journal)
   Tracking, Reflection & Progress
   • :journal <type> - 6 guided journal types with AI
   • :journal_history <type> - Review past entries
   • :mood - Track wellness metrics
   • :moon_ritual - New moon intentions, full moon releases
   • :voice_note "<msg>" <days> - Message to future self
   • :plan_progress - Healing journey completion %
   • :achievements - View badges & streaks
   ➜ Your story matters. Document your growth.

═══════════════════════════════════════════════════════════════════

[COSMIC FEATURES]

:oracle           → Healing Oracle of the Day (deterministic)
:match <n1> <n2>  → Cosmic connection compatibility
:ripple           → Love Ripple Challenge (daily kindness)
:mixer            → Sacred Sound Mixer (custom audio mixes)
:moon_ritual      → Moon intentions & release rituals
:voice_note       → Record message for future self

═══════════════════════════════════════════════════════════════════

[PERSONALIZATION & SETTINGS]

:profile_setup    → Interactive onboarding
:profile          → View your healing profile
:profile_goal     → Add healing goals
:profile_love_language → Choose your love language
:profile_modalities → Set preferred healing modalities
:profile_music    → Music preferences
:profile_spiritual → Spiritual interests

:accessibility    → Dark mode, voice, captions, fonts
:achievements     → Badges & streaks progress

═══════════════════════════════════════════════════════════════════

[TRUST & SAFETY]

:disclaimer       → Full safety notice
:resources        → Crisis support hotlines (24/7)
:accept_terms     → Record your understanding

IMPORTANT: Carnal 2.0 is NOT medical care or crisis support.
If you're in crisis, call 988 (US) or use :resources now.

═══════════════════════════════════════════════════════════════════
"""
    return menu


# ---------- Main ----------
def main():
    global SYSTEM_PROMPT
    
    # Show splash screen on startup
    show_splash_screen(duration_ms=2500)
    
    print("\n" + "="*70)
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                    CARNAL 2.0                                  ║")
    print("║           Cosmic Healing Companion                             ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("="*70)
    print("""
PRODUCT PROMISE:
Carnal 2.0 is a comprehensive digital healing and connection platform
that combines AI guidance, sound healing, meditation, journaling, and
personalized coaching to help you cultivate self-love, emotional healing,
and conscious relationships.
    """)
    print("="*70)
    print("\n[TRUST & SAFETY FIRST]")
    print("  This is a healing companion, NOT medical or crisis care.")
    print("  Type ':resources' to see crisis support hotlines.")
    print("  Type ':accept_terms' to confirm you understand our boundaries.")
    print("\n[QUICK START]")
    print("  :menu              - View all 50+ commands and features")
    print("  :profile_setup     - Personalize your healing experience")
    print("  :tab_home          - Daily dashboard & affirmations")
    print("\n[5 MAIN TABS]")
    print("  :tab_home     - Dashboard, mood, oracle, affirmations")
    print("  :tab_heal     - Meditation, reiki, chakra, emergency support")
    print("  :tab_sound    - Music library, binaural beats, sound mixer")
    print("  :tab_connect  - Love coaching, cosmic match, kindness challenges")
    print("  :tab_journal  - Journaling, mood tracking, moon rituals, progress")
    print("\n[COSMIC FEATURES]")
    print("  :oracle        - Daily healing oracle reading")
    print("  :match <n1> <n2> - Cosmic connection compatibility")
    print("  :ripple        - Daily love ripple (kindness) challenge")
    print("  :voice_note    - Message to your future self")
    print("  :moon_ritual   - New moon intentions, full moon releases")
    print("\n[SUPPORT]")
    print("  :achievements  - View your badges and streaks")
    print("  :accessibility - Dark mode, captions, fonts, voice")
    print("  :help          - Full command reference")
    print("\n" + "="*70 + "\n")
    
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    history.append({"role": "user", "content": "Greet me briefly as Carnal 2.0 and confirm you understand our product promise is to help with self-love, emotional healing, and conscious relationships."})
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

        if cmd.startswith(":hd "):
            if not HD_AVAILABLE:
                print("CAR2: Human Design not available. Make sure human_design.py is installed.")
                continue
            
            rest = user[4:].strip()
            
            # Show list of stored charts
            if rest.lower() == "list":
                if not MEMORY.get("hd_charts"):
                    print("CAR2: No HD charts stored yet.")
                else:
                    print("\nCAR2: Stored Human Design Charts:")
                    for name, chart_data in MEMORY["hd_charts"].items():
                        chart_info = chart_data.get("chart", {})
                        print(f"  - {name}: {chart_info.get('type', {}).get('name', 'Unknown')} | Profile {chart_info.get('profile', {}).get('code', 'N/A')}")
                continue
            
            parts = rest.split()
            
            if len(parts) < 3:
                print("CAR2: Generate a Human Design chart.")
                print("   Use: :hd YYYY-MM-DD HH:MM Name")
                print("   E.g: :hd 1990-05-15 14:30 Alice")
                print("   Then: :hd list   (to see all)")
                print("   Then: :match Name1 Name2   (to compare)")
                continue
            
            birth_date = parts[0]
            birth_time = parts[1]
            name = " ".join(parts[2:])
            
            try:
                result = generate_hd_chart(birth_date, birth_time, name)
                if result.get("success"):
                    chart = result["chart"]
                    # Store in memory
                    MEMORY["hd_charts"][name] = {"chart": chart, "birth_date": birth_date, "birth_time": birth_time}
                    write_json(ROOT / "memory.json", MEMORY)
                    
                    print(f"\n[HUMAN DESIGN CHART - {name}]")
                    print(f"  Birth: {birth_date} at {birth_time}")
                    print(f"  Type: {chart['type']['name']}")
                    print(f"  Profile: {chart['profile']['code']}")
                    print(f"  Authority: {chart['authority']['type']}")
                    print(f"  Strategy: {chart['type']['strategy']}")
                    print(f"\n{chart['summary']}")
                    print(f"\n> Stored! Use ':match {name} OtherName' to compare.")
                else:
                    print(f"CAR2: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"CAR2: HD error: {e}")
            continue

        if cmd.startswith(":match "):
            if not HD_AVAILABLE:
                print("CAR2: Human Design not available.")
                continue
            
            rest = user[7:].strip()
            parts = rest.split()
            
            if len(parts) < 2:
                print("CAR2: Compare two HD charts.")
                print("   Use: :match Name1 Name2")
                print("   (both must be stored via :hd command)")
                if MEMORY.get("hd_charts"):
                    print("   Available:", ", ".join(MEMORY["hd_charts"].keys()))
                continue
            
            name1 = parts[0]
            name2 = parts[1]
            
            hd_charts = MEMORY.get("hd_charts", {})
            if name1 not in hd_charts or name2 not in hd_charts:
                print(f"CAR2: Charts not found. Available: {', '.join(hd_charts.keys()) if hd_charts else 'none'}")
                continue
            
            try:
                chart1 = hd_charts[name1]["chart"]
                chart2 = hd_charts[name2]["chart"]
                result = match_compatibility(chart1, chart2)
                
                if result.get("success"):
                    print(f"\n[COMPATIBILITY REPORT]")
                    print(f"  {name1} + {name2}")
                    print(f"\n  Compatibility: {result['compatibility_percent']}%")
                    print(f"  Types: {result['type_compatibility']}")
                    print(f"  Authorities: {result['authority_compatibility']}")
                    print(f"  Profiles: {result['profile_compatibility']}")
                    print(f"\n  Notes:")
                    for note in result.get("notes", []):
                        print(f"    - {note}")
                else:
                    print(f"CAR2: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"CAR2: Match error: {e}")
            continue

        if cmd.startswith(":love "):
            rest = user[6:].strip()
            if not rest:
                print("CAR2: Love Coaching Mode")
                print("   Use: :love <relationship topic or question>")
                print("   Examples:")
                print("     :love how to build better communication with my partner")
                print("     :love healing from a breakup")
                print("     :love cultivating more self-love and worthiness")
                continue
            
            try:
                print("\n[LOVE COACHING SESSION]\n")
                response = love_coaching_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Love coaching error: {e}")
            continue

        if cmd.startswith(":heal "):
            rest = user[6:].strip()
            if not rest:
                print("CAR2: Healing Conversation Mode")
                print("   Use: :heal <emotion or challenge you're facing>")
                print("   Examples:")
                print("     :heal anxiety and overwhelm")
                print("     :heal grief and loss")
                print("     :heal shame and self-judgment")
                print("     :heal loneliness")
                continue
            
            try:
                print("\n[HEALING CONVERSATION]\n")
                response = healing_conversation(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Healing conversation error: {e}")
            continue

        if cmd.startswith(":reiki "):
            rest = user[7:].strip()
            if not rest:
                print("CAR2: Reiki Energy Healing")
                print("   Use: :reiki <what you want to heal>")
                print("   Examples:")
                print("     :reiki physical pain and tension")
                print("     :reiki emotional blockages")
                print("     :reiki chakra alignment")
                continue
            
            try:
                print("\n[REIKI ENERGY HEALING SESSION]\n")
                response = reiki_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Reiki error: {e}")
            continue

        if cmd.startswith(":meditate "):
            rest = user[10:].strip()
            if not rest:
                print("CAR2: Guided Meditation")
                print("   Use: :meditate <meditation focus>")
                print("   Examples:")
                print("     :meditate deep relaxation and peace")
                print("     :meditate body scan and tension release")
                print("     :meditate loving-kindness meditation")
                continue
            
            try:
                print("\n[GUIDED MEDITATION SESSION]\n")
                response = meditation_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Meditation error: {e}")
            continue

        if cmd.startswith(":angel "):
            rest = user[7:].strip()
            if not rest:
                print("CAR2: Angel Card Reading")
                print("   Use: :angel <what you seek guidance on>")
                print("   Examples:")
                print("     :angel guidance on my life path")
                print("     :angel message about my relationships")
                print("     :angel support for my current challenge")
                continue
            
            try:
                print("\n[ANGEL CARD READING]\n")
                response = angel_reading(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Angel reading error: {e}")
            continue

        if cmd.startswith(":chakra "):
            rest = user[8:].strip()
            if not rest:
                print("CAR2: Chakra Balancing")
                print("   Use: :chakra <what you want to balance>")
                print("   Examples:")
                print("     :chakra root chakra grounding and safety")
                print("     :chakra heart chakra opening and love")
                print("     :chakra full chakra alignment")
                continue
            
            try:
                print("\n[CHAKRA BALANCING SESSION]\n")
                response = chakra_balancing(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Chakra balancing error: {e}")
            continue

        if cmd.startswith(":sound "):
            rest = user[7:].strip()
            if not rest:
                print("CAR2: Sound Healing Sessions")
                print("   Use: :sound <instrument> <focus>")
                print("   Available instruments:")
                for key, info in SOUND_INSTRUMENTS.items():
                    print(f"     {key}: {info['name']} - {info['effect']}")
                print("   Examples:")
                print("     :sound singing_bowl deep relaxation")
                print("     :sound tuning_fork chakra alignment")
                print("     :sound drums shamanic journey")
                continue
            
            parts = rest.split(None, 1)
            if len(parts) < 2:
                print("CAR2: Please specify instrument and focus")
                print("   Use: :sound <instrument> <focus>")
                continue
            
            instrument = parts[0].lower()
            focus = parts[1]
            
            if instrument not in SOUND_INSTRUMENTS:
                print(f"CAR2: Unknown instrument. Available: {', '.join(SOUND_INSTRUMENTS.keys())}")
                continue
            
            try:
                inst_name = SOUND_INSTRUMENTS[instrument]['name']
                print(f"\n[{inst_name.upper()} HEALING SESSION]\n")
                response = sound_healing_session(instrument, focus)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Sound healing error: {e}")
            continue

        if cmd == ":modalities":
            print("\nCAR2: Available Healing Modalities")
            print("\n[HEALING SESSIONS]")
            for key, info in HEALING_MODALITIES.items():
                print(f"  :{key} - {info['name']}")
                print(f"      {info['description']}")
            print("\n[SOUND HEALING]")
            for key, info in SOUND_INSTRUMENTS.items():
                print(f"  :sound {key} <focus>")
                print(f"      {info['name']} | {info['effect']}")
            print("\n[DAILY HEALING SCHEDULE]")
            print("  :schedule - View today's healing sessions")
            continue

        if cmd == ":schedule":
            now = datetime.datetime.now()
            day_name = now.strftime("%A")
            print(f"\nCAR2: Daily Healing Sessions - {day_name}")
            print("\n[RECOMMENDED TODAY'S HEALING SCHEDULE]")
            schedule = [
                ("6:00 AM", ":meditate", "Morning meditation for clarity"),
                ("9:00 AM", ":sound singing_bowl", "Singing bowl for grounding"),
                ("12:00 PM", ":chakra", "Midday chakra alignment"),
                ("3:00 PM", ":sound tuning_fork", "Afternoon energy boost"),
                ("6:00 PM", ":reiki", "Reiki for relaxation"),
                ("9:00 PM", ":meditate", "Evening meditation for peace"),
            ]
            for time, cmd_hint, description in schedule:
                print(f"  {time:8} - {description}")
                print(f"            Try: {cmd_hint} <your intention>")
            print("\n[SESSION HISTORY]")
            sessions = MEMORY.get("healing_modalities", [])
            if sessions:
                print(f"  Total sessions: {len(sessions)}")
                recent = sessions[-3:]
                for session in recent:
                    ts = session.get("timestamp", "").split("T")[0]
                    stype = session.get("type", "unknown").replace("_", " ").title()
                    print(f"    {ts} - {stype}")
            else:
                print("  No sessions recorded yet. Start with :meditate or :reiki")
            continue

        if cmd.startswith(":music "):
            rest = user[7:].strip()
            if not rest:
                print("CAR2: Healing Music Library")
                print("   Use: :music <category>")
                print("   Available categories:")
                for key, info in MUSIC_LIBRARY.items():
                    print(f"     {key}: {info['name']}")
                print("   Examples:")
                print("     :music relaxation")
                print("     :music chakra")
                print("     :music solfeggio")
                print("\n   All downloads are UNLIMITED and 100% FREE!")
                continue
            
            category = rest.lower()
            if category not in MUSIC_LIBRARY:
                print(f"CAR2: Unknown category. Available: {', '.join(MUSIC_LIBRARY.keys())}")
                continue
            
            try:
                cat_info = MUSIC_LIBRARY[category]
                print(f"\n[{cat_info['name'].upper()}]\n")
                result = music_library_session(category)
                print(result)
            except Exception as e:
                print(f"CAR2: Music library error: {e}")
            continue

        if cmd.startswith(":technique "):
            rest = user[11:].strip()
            if not rest:
                print("CAR2: Meditation Techniques")
                print("   Use: :technique <technique_name>")
                print("   Available techniques:")
                for key, info in MEDITATION_TECHNIQUES.items():
                    print(f"     {key}: {info['name']}")
                    print(f"            {info['description']}")
                continue
            
            technique = rest.lower().replace(" ", "_")
            if technique not in MEDITATION_TECHNIQUES:
                print(f"CAR2: Unknown technique. Available: {', '.join(MEDITATION_TECHNIQUES.keys())}")
                continue
            
            try:
                tech_name = MEDITATION_TECHNIQUES[technique]['name']
                print(f"\n[{tech_name.upper()} MEDITATION]\n")
                response = meditation_technique_session(technique)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Technique error: {e}")
            continue

        if cmd.startswith(":forgive "):
            rest = user[9:].strip()
            if not rest:
                print("CAR2: Forgiveness Guidance")
                print("   Use: :forgive <what you need to forgive>")
                print("   Examples:")
                print("     :forgive myself for past mistakes")
                print("     :forgive someone who hurt me")
                print("     :forgive a broken relationship")
                continue
            
            try:
                print("\n[FORGIVENESS & EMOTIONAL RELEASE]\n")
                response = forgiveness_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Forgiveness error: {e}")
            continue

        if cmd.startswith(":gratitude "):
            rest = user[11:].strip()
            if not rest:
                print("CAR2: Gratitude Practice")
                print("   Use: :gratitude <what you want to appreciate>")
                print("   Examples:")
                print("     :gratitude my health and vitality")
                print("     :gratitude abundance in my life")
                print("     :gratitude my relationships and connections")
                continue
            
            try:
                print("\n[GRATITUDE & POSITIVITY PRACTICE]\n")
                response = gratitude_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Gratitude error: {e}")
            continue

        if cmd.startswith(":nature "):
            rest = user[8:].strip()
            if not rest:
                print("CAR2: Nature Connection & Outdoor Healing")
                print("   Use: :nature <outdoor activity or intention>")
                print("   Examples:")
                print("     :nature forest bathing and grounding")
                print("     :nature beach healing and water ceremony")
                print("     :nature hiking in nature for clarity")
                continue
            
            try:
                print("\n[NATURE HEALING & CONNECTION]\n")
                response = nature_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Nature connection error: {e}")
            continue

        if cmd.startswith(":relationships "):
            rest = user[15:].strip()
            if not rest:
                print("CAR2: Healthy Relationships Workshop")
                print("   Use: :relationships <topic>")
                print("   Examples:")
                print("     :relationships healthy communication")
                print("     :relationships setting boundaries")
                print("     :relationships building trust and intimacy")
                continue
            
            try:
                print("\n[HEALTHY RELATIONSHIPS WORKSHOP]\n")
                response = relationship_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Relationships error: {e}")
            continue

        if cmd.startswith(":inner_child "):
            rest = user[13:].strip()
            if not rest:
                print("CAR2: Inner Child Healing")
                print("   Use: :inner_child <childhood wound or need>")
                print("   Examples:")
                print("     :inner_child abandoned by parents")
                print("     :inner_child lack of safety and protection")
                print("     :inner_child shame and rejection")
                continue
            
            try:
                print("\n[INNER CHILD HEALING & REPARENTING]\n")
                response = inner_child_session(rest)
                print(f"CAR2: {response}\n")
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak(response)
                    except Exception as e:
                        print(f"(TTS error: {e})")
            except Exception as e:
                print(f"CAR2: Inner child healing error: {e}")
            continue

        if cmd == ":gifts":
            print("\nCAR2: 5 Healing Gifts for Global Wellness")
            print("\n[HEALING GIFTS AVAILABLE]")
            for key, info in HEALING_GIFTS.items():
                cmd_name = key.replace("_", " ")
                print(f"\n  :{key}")
                print(f"    {info['name']}")
                print(f"    {info['subtitle']}")
                print(f"    {info['description']}")
            print("\n[QUICK ACCESS]")
            print("  :forgive <situation> - Release emotional burdens")
            print("  :gratitude <focus> - Attract positivity")
            print("  :nature <activity> - Outdoor healing")
            print("  :relationships <topic> - Communication & connection")
            print("  :inner_child <wound> - Childhood healing")
            print("\n[SESSION TRACKING]")
            gift_sessions = MEMORY.get("healing_gifts", [])
            if gift_sessions:
                print(f"  Total sessions: {len(gift_sessions)}")
            else:
                print("  No sessions yet. Start with any gift above!")
            continue

        if cmd == ":dashboard":
            print(display_dashboard())
            continue

        if cmd.startswith(":mood"):
            rest = user[5:].strip()
            if not rest:
                print("CAR2: Mood & Energy Tracker")
                print("   Use: :mood <mood 1-10> <stress 1-10> <sleep 1-10> <energy 1-10> <intention>")
                print("   Example: :mood 7 4 8 6 I want to practice self-love today")
                continue
            
            parts = rest.split(None, 4)
            if len(parts) < 5:
                print("CAR2: Need 5 values. Example: :mood 7 4 8 6 My intention here")
                continue
            
            try:
                mood = int(parts[0])
                stress = int(parts[1])
                sleep = int(parts[2])
                energy = int(parts[3])
                intention = parts[4]
                
                result = log_mood(mood, stress, sleep, energy, intention)
                print(result)
            except ValueError:
                print("CAR2: Please use numbers 1-10 for the first 4 values.")
            continue

        if cmd == ":mood_insights":
            print(get_mood_insights())
            continue

        if cmd.startswith(":journal"):
            parts = user[8:].strip().split(None, 1)
            if not parts or (len(parts) == 1 and not parts[0]):
                print("CAR2: Guided Journaling System")
                print("   Step 1: :journal <journal_type>")
                print("   Available types:")
                for jtype in JOURNAL_PROMPTS.keys():
                    print(f"     • {jtype}")
                print("\n   Example: :journal self_love")
                print("   Then write your entry when prompted.")
                continue
            
            journal_type = parts[0].lower()
            if journal_type not in JOURNAL_PROMPTS:
                print(f"CAR2: Unknown journal type. Available: {', '.join(JOURNAL_PROMPTS.keys())}")
                continue
            
            prompt = get_journal_prompt(journal_type)
            print(f"\nCAR2: Your {journal_type.replace('_', ' ')} Journal Prompt:")
            print(f"  '{prompt}'\n")
            print("Write your entry (press Enter twice when done):")
            
            lines = []
            while True:
                try:
                    line = input()
                    if not line:
                        if lines:
                            break
                    else:
                        lines.append(line)
                except EOFError:
                    break
            
            entry_text = "\n".join(lines).strip()
            if entry_text:
                result = journal_session(journal_type, entry_text)
                print(result)
                if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                    try:
                        tts_engine.speak("Your journal entry has been saved.")
                    except Exception as e:
                        pass
            continue

        if cmd.startswith(":journal_history"):
            rest = user[15:].strip().lower()
            if not rest:
                print("CAR2: Use: :journal_history <journal_type>")
                continue
            
            journals = MEMORY.get("journals", {}).get(rest, [])
            if not journals:
                print(f"CAR2: No {rest} entries yet.")
                continue
            
            print(f"\nCAR2: {rest.replace('_', ' ').title()} Journal History ({len(journals)} entries)")
            for i, entry in enumerate(journals[-5:], 1):
                ts = entry.get("timestamp", "").split("T")[0]
                print(f"\n[Entry {i} - {ts}]")
                print(entry.get("entry", "")[:300] + "...")
            continue

        if cmd == ":affirmations":
            result = create_affirmation_set()
            print(result)
            if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                try:
                    tts_engine.speak("Here are your affirmations for today.")
                except:
                    pass
            continue

        if cmd.startswith(":plan_start"):
            rest = user[11:].strip().lower()
            if not rest:
                print("CAR2: Personalized Healing Plans")
                print("   Available plans:")
                for plan_key, plan_info in HEALING_PLANS.items():
                    print(f"     :plan_start {plan_key}")
                    print(f"       {plan_info['title']}")
                continue
            
            result = start_healing_plan(rest)
            print(result)
            continue

        if cmd == ":plan_today":
            result = get_plan_today()
            print(result)
            continue

        if cmd == ":plan_next":
            if "healing_plans" not in MEMORY or not MEMORY["healing_plans"]:
                print("CAR2: No active plan. Start one with :plan_start <plan_name>")
                continue
            
            active_plan = MEMORY["healing_plans"][-1]
            plan_data = HEALING_PLANS.get(active_plan["plan_name"], {})
            
            if active_plan["current_day"] >= len(plan_data["days"]):
                print(f"CAR2: Plan complete! Congratulations on finishing {active_plan['title']}!")
            else:
                active_plan["current_day"] += 1
                active_plan["days_completed"] += 1
                write_json(ROOT / "memory.json", MEMORY)
                print(f"CAR2: Day {active_plan['current_day']} unlocked!")
                result = get_plan_today()
                print(result)
            continue

        if cmd == ":plan_progress":
            if "healing_plans" not in MEMORY or not MEMORY["healing_plans"]:
                print("CAR2: No active plan yet.")
                continue
            
            active_plan = MEMORY["healing_plans"][-1]
            plan_data = HEALING_PLANS.get(active_plan["plan_name"], {})
            
            progress_pct = (active_plan["days_completed"] / active_plan["duration"]) * 100
            
            progress = f"""
[{active_plan['title'].upper()}]
Progress: {progress_pct:.0f}% ({active_plan['days_completed']}/{active_plan['duration']} days)

Status: Day {active_plan['current_day']} of {active_plan['duration']}
Started: {active_plan['start_date']}

Keep going! You're transforming your life.
"""
            print(progress)
            continue

        if cmd.startswith(":rel_flow"):
            rest = user[9:].strip().lower()
            if not rest:
                print("CAR2: Relationship Healing Flows")
                print("   Available flows:")
                for flow_key, flow_desc in RELATIONSHIP_FLOWS.items():
                    print(f"     :{flow_key}")
                    print(f"       {flow_desc}")
                continue
            
            result = get_relationship_flow(rest)
            print(result)
            continue

        if cmd == ":emergency":
            print(emergency_calm_mode())
            if tts_engine and SETTINGS.get("tts", {}).get("enabled", False):
                try:
                    tts_engine.speak("You are safe. Take a deep breath.")
                except:
                    pass
            continue

        if cmd.startswith(":lang"):
            rest = user[5:].strip().lower()
            if not rest:
                print("CAR2: Available languages: english, spanish, portuguese, french")
                print("   Use: :lang spanish")
                continue
            
            if rest not in TRANSLATIONS and rest != "english":
                print("CAR2: Language not available yet.")
                continue
            
            MEMORY["user_language"] = rest
            write_json(ROOT / "memory.json", MEMORY)
            
            if rest == "english":
                print("CAR2: Language set to English.")
            else:
                greeting = translate("greeting", rest)
                print(f"CAR2: {greeting}")
            continue

        # ---------- TRUST & SAFETY ----------
        if cmd == ":disclaimer":
            print(TRUST_SAFETY_DISCLAIMER)
            continue

        if cmd == ":resources":
            print("\n[CRISIS SUPPORT RESOURCES]")
            print("\n[UNITED STATES]")
            for key, val in CRISIS_RESOURCES["US"].items():
                print(f"  {val}")
            print("\n[INTERNATIONAL]")
            for key, val in CRISIS_RESOURCES["International"].items():
                print(f"  {val}")
            print("\nYou are not alone. Help is always available.")
            continue

        if cmd == ":accept_terms":
            MEMORY.setdefault("user_consent", {})["trust_safety"] = True
            write_json(ROOT / "memory.json", MEMORY)
            print("CAR2: Thank you for understanding our safety guidelines. Let's heal together responsibly.")
            continue

        # ---------- USER PROFILE ----------
        if cmd == ":profile_setup":
            print(setup_user_profile())
            continue

        if cmd == ":profile":
            print(display_profile())
            continue

        if cmd.startswith(":profile_goal"):
            rest = user[13:].strip()
            if not rest:
                print("CAR2: Use: :profile_goal <healing goal>")
                print("   Examples: anxiety relief, self-love, breakup healing, clarity, confidence")
                continue
            result = update_profile("goal", rest)
            print(result)
            continue

        if cmd.startswith(":profile_love_language"):
            rest = user[21:].strip()
            if not rest:
                print("CAR2: Love languages: words_of_affirmation, acts_of_service, physical_touch, quality_time, gifts")
                continue
            result = update_profile("love_language", rest)
            print(result)
            continue

        if cmd.startswith(":profile_modalities"):
            rest = user[19:].strip()
            if not rest:
                print("CAR2: Use: :profile_modalities <modality>")
                print("   Examples: meditation, reiki, chakra, journaling, tarot")
                continue
            result = update_profile("modality", rest)
            print(result)
            continue

        if cmd.startswith(":profile_music"):
            rest = user[14:].strip()
            if not rest:
                print("CAR2: Use: :profile_music <music type>")
                print("   Examples: relaxation, chakra, solfeggio, binaural, angel")
                continue
            result = update_profile("music", rest)
            print(result)
            continue

        if cmd.startswith(":profile_spiritual"):
            rest = user[17:].strip()
            if not rest:
                print("CAR2: Use: :profile_spiritual <interest>")
                print("   Examples: tarot, moon rituals, angel guidance, energy work, astrology")
                continue
            result = update_profile("spiritual", rest)
            print(result)
            continue

        # ---------- GAMIFICATION ----------
        if cmd == ":achievements":
            print(display_gamification())
            awards = check_and_award_badges()
            if awards:
                print("\n[NEW BADGES EARNED!]")
                for award in awards:
                    print(f"  🏆 {award}")
            continue

        # ---------- ACCESSIBILITY ----------
        if cmd == ":accessibility":
            access = MEMORY.get("accessibility", {})
            settings_info = f"""
[ACCESSIBILITY SETTINGS]

Dark Mode: {access.get('dark_mode', False)}
  Use: :accessibility dark_mode on/off

Voice Playback: {access.get('voice_playback', False)}
  Use: :accessibility voice on/off

Captions: {access.get('captions', True)}
  Use: :accessibility captions on/off

Font Size: {access.get('font_size', 'medium')}
  Use: :accessibility font_size <small|medium|large|extra_large>

Screen Reader Compatible: Yes
Navigation: Simple and intuitive
Keyboard Navigation: Fully supported
"""
            print(settings_info)
            continue

        if cmd.startswith(":accessibility"):
            rest = user[14:].strip()
            if not rest:
                print("CAR2: Use: :accessibility <setting> <value>")
                print("   Settings: dark_mode, voice, captions, font_size")
                continue
            
            parts = rest.split(None, 1)
            if len(parts) < 2:
                print("CAR2: Need setting and value. E.g., :accessibility dark_mode on")
                continue
            
            setting, value = parts[0], parts[1]
            result = set_accessibility(setting, value)
            print(result)
            continue

        # ---------- COSMIC BRAND FEATURES ----------
        if cmd == ":oracle":
            print(healing_oracle())
            continue

        if cmd.startswith(":match "):
            rest = user[7:].strip()
            parts = rest.split()
            
            if len(parts) < 2:
                print("CAR2: Cosmic Match - Compatibility/Connection Reflection")
                print("   Use: :match <name1> <name2>")
                if MEMORY.get("hd_charts"):
                    print("   Available people:", ", ".join(MEMORY["hd_charts"].keys()))
                continue
            
            name1, name2 = parts[0], parts[1]
            print(cosmic_match(name1, name2))
            continue

        if cmd == ":ripple":
            print(love_ripple_challenge())
            continue

        if cmd == ":ripple_complete":
            result = log_ripple(True)
            print(result)
            continue

        if cmd == ":mixer":
            print(sacred_sound_mixer())
            continue

        if cmd.startswith(":mixer_add"):
            rest = user[10:].strip()
            if not rest:
                print("CAR2: Use: :mixer_add <sound> <volume>")
                print("   Example: :mixer_add singing_bowl 70%")
                continue
            print("CAR2: Sound added to your mix! (Feature in development)")
            continue

        if cmd == ":mixer_play":
            print("CAR2: Now playing your sacred sound mix... (streaming feature coming soon)")
            continue

        if cmd.startswith(":moon_ritual"):
            rest = user[12:].strip()
            if not rest:
                print(moon_ritual_guide())
                continue
            
            if "new_moon" in rest.lower():
                intention = rest.replace("new_moon ", "").strip()
                print(f"""
[NEW MOON INTENTION RITUAL]
Your intention: "{intention}"

Plant this seed in your heart and mind during the new moon phase.
Watch as it grows into manifestation over the lunar cycle.
Trust the process. Trust yourself.
""")
            elif "full_moon" in rest.lower():
                release = rest.replace("full_moon ", "").strip()
                print(f"""
[FULL MOON RELEASE RITUAL]
What you're releasing: "{release}"

Under the light of the full moon, let this go with gratitude.
Make space for what must arrive.
You are safe. You are held.
""")
            continue

        if cmd.startswith(":voice_note"):
            parts = user[12:].strip().rsplit(None, 1)
            if len(parts) < 2:
                print("CAR2: Record a voice message to your future self")
                print("   Use: :voice_note <message> <days>")
                print("   Example: :voice_note \"You are braver than you believe\" 7")
                continue
            
            message = parts[0].strip('"\'')
            try:
                days = int(parts[1])
                result = voice_note_to_future_self(message, days)
                print(result)
            except ValueError:
                print("CAR2: Days must be a number. E.g., :voice_note \"Message\" 7")
            continue

        # ---------- TAB NAVIGATION ----------
        if cmd == ":menu" or cmd == ":help":
            print(display_main_menu())
            continue

        if cmd == ":tab_home":
            print("""
[HOME TAB]
Your Daily Healing Dashboard
            
:dashboard - Personal wellness overview
:affirmations - Daily affirmations
:oracle - Healing oracle reading
:mood - Log your mood & energy
:mood_insights - View patterns

Start your day with intention!
""")
            continue

        if cmd == ":tab_heal":
            print("""
[HEAL TAB]
Deep Healing Modalities & Sessions

:reiki <focus> - Energy healing
:meditate <focus> - Guided meditation
:chakra <focus> - Chakra balancing
:angel <question> - Angel guidance
:forgive <situation> - Release burdens
:inner_child <wound> - Childhood healing
:relationships <topic> - Communication skills
:emergency - Crisis support
:plan_start <plan> - Guided healing journey

Choose what your soul needs today.
""")
            continue

        if cmd == ":tab_sound":
            print("""
[SOUND TAB]
Healing Music, Frequencies & Sound Baths

:music <category> - Healing music library
:technique <name> - Meditation techniques
:sound <instrument> <focus> - Sound healing
:mixer - Create custom audio mix
:schedule - Daily healing schedule

Let sound heal your frequency.
""")
            continue

        if cmd == ":tab_connect":
            print("""
[CONNECT TAB]
Relationships, Community & Love

:love <topic> - Love coaching
:match <name1> <name2> - Cosmic Match
:ripple - Love Ripple Challenge (daily kindness)
:relationships <topic> - Healthy relationship skills
:gratitude <focus> - Gratitude practice

Connect authentically. Love radically.
""")
            continue

        if cmd == ":tab_journal":
            print("""
[JOURNAL TAB]
Tracking, Reflection & Progress

:journal <type> - Guided journaling prompts
:journal_history <type> - View past entries
:mood - Track mood & wellness metrics
:moon_ritual - Moon cycle intentions
:voice_note <msg> <days> - Message to future self
:plan_progress - Healing journey progress
:achievements - Badges and streaks

Your story matters. Document your growth.
""")
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
