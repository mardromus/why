# Lex Orion — Indian Court Simulator

Streamlit app that runs a civil courtroom simulation with AI counsel, a judge, witnesses, and a **RAG pipeline** that checks whether uploaded evidence is contextually similar to the case and the legal knowledge base.

## Features

- Role play as plaintiff counsel, defendant counsel, or observer
- Step-by-step hearing (no blocking autoplay — safe for Streamlit Cloud)
- Evidence upload (PDF, DOCX, TXT) with similarity scoring against:
  - case facts and witness statements
  - exhibits already on the record
  - Indian statutes, principles, and precedents
- Clerk-style LLM note on relevance, consistency, and Evidence Act caution
- Legal library search over the same knowledge base
- Transcript download

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Put your Groq key in `.env`:

```
GROQ_API_KEY=gsk_...
```

Then:

```bash
streamlit run app.py
```

Demo login is `admin` / `1234`, or use **Continue as guest**.

## Streamlit Community Cloud

1. Push this repo to GitHub.
2. Create an app at [share.streamlit.io](https://share.streamlit.io) with `app.py` as the entry point.
3. In **App settings → Secrets** add:

```toml
GROQ_API_KEY = "gsk_..."
```

4. Deploy. Python version is pinned in `runtime.txt`.

Optional secrets / env vars:

| Key | Purpose |
| --- | --- |
| `GROQ_API_KEY` | Required for agent speech and the clerk note |
| `GROQ_MODEL` | Defaults to `llama-3.3-70b-versatile` |
| `LEX_AUTH_ENABLED` | `false` skips the login screen |
| `LEX_DEMO_USER` / `LEX_DEMO_PASSWORD` | Override demo credentials |

## How evidence similarity works

1. **Ingest** statutes under `data/legal_codes/`, plus `data/precedents.json` and `data/legal_principles.json`.
2. **Retrieve** with TF-IDF cosine similarity (no GPU, Streamlit-friendly).
3. **Augment** the prompt with the top matching case chunks and legal provisions.
4. **Generate** a short clerk analysis with Groq.

Open **Evidence similarity** in the sidebar (or the Evidence Similarity page) and upload an exhibit while a case is selected.

## Project layout

```
app.py                 Streamlit entry
pages/                 Extra Streamlit pages
rag/                   RAG ingest, retrieval, scoring
courtroom/             Hearing engine
agents/                Judge, counsel, witness
data/                  Cases and legal knowledge
ui/                    Streamlit views
```

Educational use only — not legal advice.
