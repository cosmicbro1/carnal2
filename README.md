# Carnal 2.0 - Cosmic Healing Companion

## Our Promise

**Carnal 2.0 is a comprehensive digital healing and connection platform that combines AI guidance, sound healing, meditation, journaling, and personalized coaching to help people cultivate self-love, emotional healing, and conscious relationships.**

We believe healing is a journey, not a destination. Carnal 2.0 provides daily tools, cosmic guidance, and accountability to support your transformation with compassion, privacy, and trust.

---

## ✨ Core Features

### **1. Healing Modalities**
🕉️ Reiki Energy Sessions | 🧘 Guided Meditation | 👼 Angel Guidance | 🔷 Chakra Balancing | 🔊 Sound Healing

### **2. Personalized Healing Plans**
📋 7-Day & 21-Day Transformation Programs | Daily sequenced healing activities | Progress tracking & milestones

### **3. Sound & Frequencies**
🎵 30+ Healing Music Tracks | 5 Solfeggio Frequency Sets | Binaural Beats | Sacred Sound Mixer (create custom mixes)

### **4. Guided Journaling**
📔 6 Journal Types with AI Reflection | Mood & Energy Tracking | Gratitude Practices | Shadow Work & Inner Child Healing

### **5. Relationship Support**
💕 Love Coaching | Healthy Communication Training | Cosmic Match (compatibility analysis) | 6 Specialized Healing Flows

### **6. Cosmic Features**
🔮 Daily Healing Oracle | 🌙 Moon Ritual Guidance | 💬 Voice Notes to Future Self | 💝 Love Ripple Challenge (daily kindness)

### **7. User Personalization**
👤 Healing Profile (goals, preferences, spiritual interests) | Customizable Modalities | Music Preferences | Notification Timing

### **8. Gamification & Progress**
🏆 7 Achievement Badges | Daily Streaks | Leaderboards Coming | Non-aggressive, compassion-focused rewards

### **9. Accessibility**
🌙 Dark Mode | 🔊 Voice Playback | 📝 Captions | 🔤 Adjustable Fonts | ♿ Screen Reader Compatible

### **10. Trust & Safety**
🛡️ Clear Safety Disclaimers | Crisis Support Resources (988, Crisis Text Line, NAMI) | Privacy-First Journaling | Community Guidelines  

---

## 🚀 SUPER PRODUCTIVE MODE - Gemma 4 Integration

**Carnal 2.0 now integrates Gemma 4 for maximum productivity!**

| Feature | Gemma 4 | GPT-4o-mini |
|---------|---------|-----------|
| **Speed** | 200-500ms | 1-3s |
| **Cost** | $0.18/month | $3.60/month |
| **Requests/min** | 60 (free) | Paid tier |
| **Best For** | Healing, Speed | Long context |

✨ **10-100x faster healing sessions**
💰 **95% cheaper than OpenAI** 
🎯 **Excellent for empathetic responses**
🔄 **Auto-fallback to OpenAI if needed**

📖 **Setup in 2 minutes:** See `GEMMA4_SETUP.md`

---

## Quick Start

### Prerequisites
- Python 3.8+
- **Either:** OpenAI API key (paid) **OR** Local LLM (free)

### Installation

1. **Clone the repo:**
```bash
git clone https://github.com/cosmicbro1/carnal2.git
cd carnal2
```

2. **Create virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Choose your LLM:**

#### **Option A: FREE + OPEN SOURCE - Use Ollama (BEST FOR STUDENTS)** ⭐

**Completely free, open source, runs locally. Zero API keys, zero cost, forever.**

1. Download: https://ollama.ai
2. Run: `ollama pull gemma2` (recommended) or `ollama pull mistral`
3. Start: `ollama serve` (keep terminal open)
4. Edit `settings.json`:
```json
{
  "llm_provider": "auto",
  "ollama": {
    "base_url": "http://localhost:11434",
    "model": "gemma2"
  },
  "temperature": 0.7,
  "max_tokens": 800
}
```

**Perfect for:**
- 🆓 Students with no budget
- 🔐 Privacy-first (local only, no servers)
- 🌐 Works offline
- 📖 Open source & transparent

📖 **Complete Setup Guide:** See `OPENSOURCE_STUDENT_SETUP.md`

#### **Option B: FREE TIER - Use Google Gemma 4 API** 

Free API key: https://ai.google.dev/gemini-api (no credit card, 60 req/min)

1. Create `.env`: `GOOGLE_API_KEY=your_key_here`
2. Install: `pip install google-generativeai`
3. Edit `settings.json`:
```json
{
  "llm_provider": "gemma"
}
```

**Benefits:**
- 🚀 10x faster than Ollama local
- ⚡ 95% cheaper than OpenAI
- 🆓 Free tier
- 🔄 Cloud-based (faster)

#### **Option C: PAID - Use OpenAI**

Most expensive option, but most capable.

1. Create `.env`: `OPENAI_API_KEY=sk-...`
2. Edit `settings.json`:
```json
{
  "llm_provider": "openai",
  "model": "gpt-4o-mini"
}
```

**Recommendation Priority:**
1. **Ollama** (Free, open source, local) ← Best for students
2. Google Gemma API (Free tier, fast)
3. OpenAI (Paid, most capable)

#### **Option C: PAID - Use OpenAI**

Create a `.env` file with your API key:
```
OPENAI_API_KEY=sk-...your_key...
OPENAI_BASE_URL=https://api.openai.com/v1
```

Then edit `settings.json`:
```json
{
  "llm_provider": "openai",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 800
}
```

5. **Run the bot:**

**CLI mode:**
```bash
python carnal2.py
```

**Web mode (access from iPhone):**
```bash
python web_app.py
```
Then visit `http://YOUR_COMPUTER_IP:8080` from your iPhone

## Commands

### CLI Mode
- `:quit` - Exit
- `:showmem` - Show memory
- `:remember <fact>` - Add memory
- `:img <prompt>` - Generate image
- `:card <name> [style]` - Generate tarot card
- `:voice <text>` - Speak text
- `:tts on/off` - Enable/disable auto-speak

## Configuration

Edit `settings.json`:
```json
{
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 800,
  "tts": {
    "enabled": false,
    "rate": 150,
    "volume": 0.9
  },
  "image": {
    "provider": "openai",
    "output_dir": "outputs"
  }
}
```

## Free vs Paid

### **Completely Free Setup** 🎉
- **LLM**: Ollama (local) - no API key needed
- **TTS**: pyttsx3 (built-in)
- **Images**: Skip image generation, or use free tier services
- **Cost**: $0/month

### **Paid Setup** 💳
- **LLM**: OpenAI/Claude ($10-20/month depending on usage)
- **Images**: OpenAI DALL-E or Stable Diffusion (extra cost)
- **TTS**: Optional (use local for free)
- **Cost**: $10-50/month depending on usage

## Using Local LLMs

Set `openai_base_url` in `settings.json` to your local server:
- **Ollama**: `http://localhost:11434/v1` (Recommended! Free!)
- **LM Studio**: `http://localhost:1234/v1`
- **vLLM**: `http://localhost:8000/v1`
- **GPT4All**: `http://localhost:4891/v1`

Popular free models:
- `mistral` - Fast, smart (Recommended)
- `llama2` - Meta's open model
- `neural-chat` - Optimized for chat
- `orca-mini` - Lightweight

Just run `ollama pull mistral` and you're done! 🚀

## Project Structure

```
carnal2.0/
├── carnal2.py              # Main CLI bot
├── web_app.py              # Flask web server
├── web_chat.html           # Mobile chat UI
├── tts.py                  # Text-to-speech engine
├── generate_cert.py        # SSL certificate generator
├── settings.json           # Configuration
├── persona.txt             # Bot personality
├── memory.json             # Learned facts
├── requirements.txt        # Dependencies
└── data/                   # PDFs for knowledge
```

## Tips

- **Faster responses**: Use `gpt-4o-mini` or a local LLM
- **Better persona**: Edit `persona.txt`
- **Teach it**: Use `:remember` to add facts
- **Images**: Requires credits on OpenAI or local Stable Diffusion

## Troubleshooting

**"Can't connect from iPhone"**
- Make sure both devices are on same WiFi
- Check IP with `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
- Try different ports in web_app.py (8080, 3000, 5000)

**"API key error"**
- Check `.env` file exists and has correct key
- Or set it in `settings.json`

**"No speech output"**
- Install pyttsx3: `pip install pyttsx3`
- Enable in `settings.json`: `"tts": {"enabled": true}`

## Contributing

Found a bug? Want to add features? PRs welcome! 🚀

## License

MIT - Free to use, modify, and distribute

## Disclaimer

This is a fan project. Not affiliated with OpenAI or any other company.

---

**Made with ❤️ because healing shouldn't cost a thing** 📚
