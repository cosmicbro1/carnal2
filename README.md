# Carnal 2.0 - Open Source AI Chat Companion

A free, open-source AI chatbot with voice input/output, image generation, tarot readings, and mobile access.

## Features

✨ **Chat** - Talk to your AI buddy in real-time  
🎙️ **Voice Input** - Speak instead of type (works on iPhone)  
📢 **Voice Output** - AI responds with text-to-speech  
🖼️ **Image Generation** - Generate images from prompts (OpenAI or Stable Diffusion)  
🔮 **Tarot Cards** - Generate mystical tarot artwork  
📱 **Mobile Access** - Chat from your iPhone on home WiFi  
💾 **Memory** - AI learns facts about you  
🆓 **100% Free** - No subscriptions, no paywalls  

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key (or local LLM endpoint)

### Installation

1. **Clone the repo:**
```bash
git clone https://github.com/YOUR_USERNAME/carnal2.git
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

4. **Set up your API key:**
Create a `.env` file:
```
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

Or edit `settings.json` for custom config.

5. **Run the bot:**

**CLI mode:**
```bash
python carnal2.py
```

**Web mode (access from iPhone):**
```bash
python generate_cert.py
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

## Using Local LLMs

Set `OPENAI_BASE_URL` to your local server:
- **Ollama**: `http://localhost:11434/v1`
- **LM Studio**: `http://localhost:1234/v1`
- **vLLM**: `http://localhost:8000/v1`

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

**Made with ❤️ for broke students everywhere** 📚
