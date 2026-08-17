"""Application configuration. Secrets come from env, Streamlit secrets, then api_keys.py."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
LEGAL_CODES_DIR = DATA_DIR / "legal_codes"

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

APP_NAME = "Lex Orion"
APP_TAGLINE = "Indian Court Simulator"
DEFAULT_JUDGE = {
    "name": "Justice Rao",
    "experience": "20 years",
    "specialization": "Civil Law",
}
DEFAULT_PLAINTIFF_LAWYER = {
    "name": "Adv. Mehta",
    "experience": "15 years",
    "specialization": "Contracts",
}
DEFAULT_DEFENDANT_LAWYER = {
    "name": "Adv. Singh",
    "experience": "12 years",
    "specialization": "Contracts",
}

PHASES = [
    "opening",
    "examination_in_chief",
    "cross_examination",
    "evidence",
    "objection",
    "closing",
    "judgment",
    "completed",
]

AUTH_ENABLED = os.getenv("LEX_AUTH_ENABLED", "true").lower() in {"1", "true", "yes"}
DEMO_USERNAME = os.getenv("LEX_DEMO_USER", "admin")
DEMO_PASSWORD = os.getenv("LEX_DEMO_PASSWORD", "1234")


def get_groq_api_key() -> str:
    key = (os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY") or "").strip()
    if key:
        return key

    try:
        import streamlit as st

        secrets = getattr(st, "secrets", None)
        if secrets and "GROQ_API_KEY" in secrets:
            return str(secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass

    try:
        from api_keys import GROQ_API_KEY as fallback

        if fallback and fallback != "YOUR_GROQ_API_KEY_HERE":
            return str(fallback).strip()
    except Exception:
        pass

    return ""


def groq_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
