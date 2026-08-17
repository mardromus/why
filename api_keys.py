# Local fallback only. Prefer GROQ_API_KEY in the environment or Streamlit secrets.
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
