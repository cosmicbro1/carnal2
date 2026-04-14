import pyttsx3
import os
import json
import pathlib
from typing import Optional

ROOT = pathlib.Path(__file__).parent

class TTSEngine:
    """Text-to-speech engine for Carnal 2.0."""
    
    def __init__(self, config_path: Optional[pathlib.Path] = None):
        """Initialize TTS engine with optional config."""
        self.engine = pyttsx3.init()
        self.config_path = config_path or ROOT / "settings.json"
        self.config = self._load_config()
        self._apply_config()
    
    def _load_config(self) -> dict:
        """Load TTS settings from settings.json."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("tts", {})
        return {}
    
    def _apply_config(self):
        """Apply configuration to the engine."""
        rate = self.config.get("rate", 150)
        volume = self.config.get("volume", 0.9)
        voice_id = self.config.get("voice", None)
        
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)
        
        if voice_id:
            voices = self.engine.getProperty("voices")
            if voice_id < len(voices):
                self.engine.setProperty("voice", voices[voice_id].id)
    
    def speak(self, text: str, wait: bool = True):
        """
        Speak the given text.
        
        Args:
            text: The text to speak
            wait: If True, block until speech finishes. If False, start async.
        """
        self.engine.say(text)
        if wait:
            self.engine.runAndWait()
    
    def speak_async(self, text: str):
        """Start speaking without blocking."""
        self.speak(text, wait=False)
    
    def get_voices(self) -> list:
        """Return list of available voices with IDs."""
        voices = self.engine.getProperty("voices")
        return [
            {"id": i, "name": v.name, "lang": v.languages}
            for i, v in enumerate(voices)
        ]
    
    def set_rate(self, rate: int):
        """Set speech rate (50-300, default ~150)."""
        self.engine.setProperty("rate", rate)
    
    def set_volume(self, volume: float):
        """Set volume (0.0-1.0)."""
        self.engine.setProperty("volume", max(0.0, min(1.0, volume)))
    
    def stop(self):
        """Stop speaking."""
        self.engine.stop()


def main_demo():
    """Demo the TTS engine."""
    tts = TTSEngine()
    
    print("Available voices:")
    for voice in tts.get_voices():
        print(f"  {voice['id']}: {voice['name']}")
    
    print("\nTesting TTS...")
    tts.speak("Hey bro! I can talk now!")
    
    print("Test complete.")


if __name__ == "__main__":
    main_demo()
