import os, json, datetime, pathlib
from typing import List, Dict

# Auto-load .env for API keys & settings
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = pathlib.Path(__file__).parent

# ---------- File Helpers ----------
def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- Load Persona & Memory ----------
PERSONA = read_text(ROOT / "persona.txt")
MEMORY = read_json(ROOT / "memory.json")
SETTINGS = read_json(ROOT / "settings.json")

# ---------- PDF Loader ----------
def load_pdfs_from_data(max_pages=40, max_chars=12000) -> str:
    """Reads PDFs from ./data and returns combined text (truncated for safety)."""
    data_dir = ROOT / "data"
    if not data_dir.exists():
        return ""

    try:
        import PyPDF2
    except ImportError:
        print("Note: PyPDF2 not installed. Run: pip install PyPDF2")
        return ""

    chunks, total_chars = [], 0
    for name in sorted(os.listdir(data_dir)):
        if not name.lower().endswith(".pdf"):
            continue
        path = data_dir / name
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages[:max_pages]:
                    text = page.extract_text() or ""
                    if not text.strip():
                        continue
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
            print(f"Error reading {name}: {e}")

    combined = "\n".join(chunks).strip()
    if combined:
        print("Loaded PDF knowledge from /data.")
    return combined

def find_in_pdf(pdf_text: str, query: str, window=80, max_hits=10):
    """Search inside PDF text and return snippets."""
    results = []
    hay, needle = pdf_text.lower(), query.lower()
    start = 0
    while len(results) < max_hits:
        idx = hay.find(needle, start)
        if idx == -1:
            break
        left, right = max(0, idx-window), min(len(pdf_text), idx+len(query)+window)
        snippet = pdf_text[left:right].replace("\n", " ")
        if left > 0: snippet = "…" + snippet
        if right < len(pdf_text): snippet += "…"
        results.append(snippet.strip())
        start = idx + len(query)
    return results

PDF_KNOWLEDGE = load_pdfs_from_data()

# ---------- System Prompt Builder ----------
def build_system_prompt(persona: str, memory: Dict) -> str:
    facts = "\n".join(f"- {x}" for x in memory.get("facts", []))
    rules = "\n".join(f"- {x}" for x in memory.get("style_rules", []))
    prefs = "\n".join(f"- {k}: {v}" for k, v in memory.get("user_prefs", {}).items())
    return f"""{persona}

[Long-term memory — facts]
{facts}

[Style rules]
{rules}

[User preferences]
{prefs}

Be concise by default. If the user says "carnal", it's a friendly address — respond warmly.
"""

SYSTEM_PROMPT = build_system_prompt(PERSONA, MEMORY)

# ---------- OpenAI Client ----------
from openai import OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "no-key"),
    base_url=os.environ.get("OPENAI_BASE_URL", None)
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

# ---------- Memory & Transcript ----------
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
    SYSTEM_PROMPT = build_system_prompt(PERSONA, MEMORY)

# ---------- Main Loop ----------
def main():
    print("Carnal 2.0 — PDF ready. Commands: ':quit', ':showmem', ':remember <fact>', ':reloadpdf', ':find <word>'")
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    if PDF_KNOWLEDGE:
        history.append({"role": "system", "content": "[PDF Knowledge]\n" + PDF_KNOWLEDGE})

    # Boot greeting
    history.append({"role": "user", "content": "Greet me briefly and confirm you're Carnal 2.0."})
    try:
        print(f"CAR2: {chat_once(history)}\n")
    except Exception as e:
        print("Boot greeting failed.", e)

    global PDF_KNOWLEDGE
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
            append_memory_fact(fact)
            print("CAR2: Noted. Memory updated.")
            continue
        if user.lower() == ":showmem":
            print(json.dumps(MEMORY, indent=2))
            continue
        if user.lower() == ":reloadpdf":
            PDF_KNOWLEDGE = load_pdfs_from_data()
            print("CAR2: PDF knowledge reloaded." if PDF_KNOWLEDGE else "CAR2: No PDFs found.")
            continue
        if user.lower().startswith(":find "):
            term = user[len(":find "):].strip()
            if PDF_KNOWLEDGE:
                hits = find_in_pdf(PDF_KNOWLEDGE, term)
                if hits:
                    print("CAR2: Search results:")
                    for h in hits:
                        print(" -", h)
                else:
                    print("CAR2: No matches found.")
            else:
                print("CAR2: No PDF knowledge loaded.")
            continue

        history.append({"role": "user", "content": user})
        if PDF_KNOWLEDGE:
            history.insert(1, {"role": "system", "content": "[PDF Knowledge]\n" + PDF_KNOWLEDGE})
        try:
            reply = chat_once(history)
        except Exception as e:
            print("CAR2 error:", e)
            continue
        history.append({"role": "assistant", "content": reply})
        print(f"CAR2: {reply}\n")

if __name__ == "__main__":
    main()
