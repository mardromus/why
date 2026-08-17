# utils/stt.py

from __future__ import annotations

import os
import tempfile
from typing import Optional, Dict, Any


class STTEngine:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lexorion_stt_")
        self.language_settings = {"en": "en-US", "hi": "hi-IN"}
        self.available = False
        self.recognizer = None
        try:
            import speech_recognition as sr

            self.recognizer = sr.Recognizer()
            self.available = True
        except Exception:
            self.available = False

    def process_audio(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        if not self.available or not audio_data:
            return None
        import speech_recognition as sr

        filepath = os.path.join(self.temp_dir, "temp_audio.wav")
        try:
            with open(filepath, "wb") as handle:
                handle.write(audio_data)
            with sr.AudioFile(filepath) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(
                    audio, language=self.language_settings.get(language, "en-US")
                )
        except Exception as exc:
            print(f"Error processing audio: {exc}")
            return None

    def process_microphone_input(self, language: str = "en") -> Optional[str]:
        if not self.available:
            return None
        import speech_recognition as sr

        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                return self.recognizer.recognize_google(
                    audio, language=self.language_settings.get(language, "en-US")
                )
        except Exception as exc:
            print(f"Error processing microphone input: {exc}")
            return None

    def cleanup(self):
        try:
            for filename in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, filename))
            os.rmdir(self.temp_dir)
        except Exception as exc:
            print(f"Error cleaning up STT files: {exc}")

    def set_language_code(self, language: str, code: str):
        self.language_settings[language] = code

    def get_available_languages(self) -> Dict[str, str]:
        return {"en": "English", "hi": "Hindi"}
