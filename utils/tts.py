# utils/tts.py

from __future__ import annotations

import os
import tempfile
from typing import Dict, Any, Optional

try:
    from gtts import gTTS
except ImportError:
    gTTS = None


class TTSEngine:
    """Generate speech with gTTS. Playback uses Streamlit audio on Cloud."""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lexorion_tts_")
        self.voice_settings = {
            "judge": {"language": "en", "slow": False},
            "plaintiff": {"language": "en", "slow": False},
            "defendant": {"language": "en", "slow": False},
            "witness": {"language": "en", "slow": False},
        }
        self.playback_available = False
        if os.environ.get("LEX_ENABLE_PYGAME_AUDIO") == "1":
            try:
                import pygame

                pygame.mixer.init()
                self.playback_available = True
            except Exception:
                self.playback_available = False

    def generate_tts(self, text: str, role: str = "judge", language: str = "en") -> Optional[str]:
        if not gTTS or not text or not str(text).strip():
            return None
        settings = self.voice_settings.get(role, {"language": language, "slow": False})
        try:
            tts = gTTS(text=str(text)[:4500], lang=settings.get("language", language), slow=settings.get("slow", False))
            filename = f"tts_{role}_{abs(hash(text))}.mp3"
            filepath = os.path.join(self.temp_dir, filename)
            tts.save(filepath)
            return filepath
        except Exception as exc:
            print(f"Error generating TTS: {exc}")
            return None

    def generate_bytes(self, text: str, role: str = "judge", language: str = "en") -> Optional[bytes]:
        filepath = self.generate_tts(text, role=role, language=language)
        if not filepath:
            return None
        try:
            with open(filepath, "rb") as handle:
                return handle.read()
        except Exception:
            return None

    def play_audio(self, filepath: str) -> bool:
        if not self.playback_available:
            return False
        try:
            import pygame
            import time

            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            return True
        except Exception as exc:
            print(f"Error playing audio: {exc}")
            return False

    def speak(self, text: str, role: str = "judge", language: str = "en") -> bool:
        audio = self.generate_bytes(text, role=role, language=language)
        if not audio:
            return False
        try:
            import streamlit as st

            st.audio(audio, format="audio/mp3")
            return True
        except Exception:
            filepath = self.generate_tts(text, role=role, language=language)
            return bool(filepath and self.play_audio(filepath))

    def cleanup(self):
        try:
            for filename in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, filename))
            os.rmdir(self.temp_dir)
        except Exception as exc:
            print(f"Error cleaning up TTS files: {exc}")

    def set_voice_settings(self, role: str, settings: Dict[str, Any]):
        self.voice_settings[role] = settings

    def get_available_languages(self) -> Dict[str, str]:
        return {"en": "English", "hi": "Hindi"}


def generate_tts(text, language="en", voice="default"):
    engine = TTSEngine()
    return engine.generate_tts(text, role=voice, language=language)
