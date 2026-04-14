import os, json, datetime, pathlib
from typing import List, Dict

# Load .env automatically for API keys
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

ROOT = pathlib.Path(__file__).parent

def read_text(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

PERSONA = read_text(ROOT / "persona.txt")
MEMORY = read_json(ROOT / "memory.json")
SETTINGS = read_json(ROOT / "settings.json")

# Load PDF knowledge from /data
def load_pdfs_from_data(max_pages=40, max_chars=12000):
    data_dir = ROOT / "data"
    if not data_dir.exists():
        data_dir.mkdir()
        return ""

    try:
        import PyPDF2
    except ImportError:
        print("Note: PyPDF2 not installed.")
        print("Run: pip install PyPDF2 any")

    chunks = []
    total_chars = 0
    for name in sorted(os.listdir(data_dir)):
        if not name.lower().endswith(".pdf"):
            continue
        path = data_dir / name
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages[:max_pages]):
                    text = page.extract_text() or ""
                    if text.strip():
                        need = max_chars - total_chars
                        if need <= 0:
                            break
                        if len(text) > need:
                            text = text[:need]
                        chunks.append(text)
                        total_chars += len(text)
                if total_chars >= max_chars:
                    break
        except Exception as e:
            print(f"PDF read issue ({name}): {e}")

    combined = "\n".join(chunks).strip()
    if combined:
        print("Loaded PDF knowledge from /data folder.")
    return combined

PDF_KNOWLEDGE = load_pdfs_from_data()

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

# OpenAI client
from openai import OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "no-key"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)

MODEL = SETTINGS.get("model", "gpt-4o-mini")
TEMPERATURE = SETTINGS.get("temperature", 0.7)
MAX_TOKENS = SETTINGS.get("max_tokens", 800)

def chat_once(messages: List[Dict]) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return resp.choices[0].message.content

def save_transcript(history: List[Dict]):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "transcripts"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"carnal_chat_{ts}.txt"
    with open(path, "w", encoding="utf-8") as f:
        for m in history:
            f.write(f"[{m['role'].upper()}]\n{m['content']}\n\n")
    print(f"Saved transcript to {path}")

def append_memory_fact(fact: str):
    MEMORY.setdefault("facts", []).append(fact)
    with open(ROOT / "memory.json", "w", encoding="utf-8") as f:
        json.dump(MEMORY, f, indent=2)
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = build_system_prompt(PERSONA, MEMORY, PDF_KNOWLEDGE)

def main():
    print("Carnal 2.0 — plug-and-play. ':quit' to exit, ':showmem' to view memory, ':remember <fact>' to save.")
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    history.append({"role": "user", "content": "Greet me briefly and confirm you're Carnal 2.0."})

    try:
        boot = chat_once(history)
        print(f"CAR2: {boot}\n")
    except Exception as e:
        print("Boot greeting failed, continuing.", e)

    while True:
        try:
            user = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            save_transcript(history)
            break

        if not user:
            continue
        if user.lower() in (":quit", ":q", "exit"):
            save_transcript(history)
            break
        if user.lower().startswith(":remember "):
            fact = user[len(":remember "):].strip()
            if fact:
                append_memory_fact(fact)
                print("CAR2: Noted. Memory updated.")
            else:
                print("CAR2: Give me something to remember.")
            continue
        if user.lower() == ":showmem":
            print(json.dumps(MEMORY, indent=2))
            continue

        history.append({"role": "user", "content": user})
        try:
            reply = chat_once(history)
        except Exception as e:
            print("CAR2 error:", e)
            continue
        history.append({"role": "assistant", "content": reply})
        print(f"CAR2: {reply}\n")

if __name__ == "__main__":
    main()
