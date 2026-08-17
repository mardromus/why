"""Shared visual styles for Lex Orion."""

COURTROOM_CSS = """
<style>
body, .stApp {
    background-color: #111 !important;
    color: #fff !important;
}
.stButton>button, .stTextInput>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>div>div {
    background: #222 !important;
    color: #fff !important;
    border: 2px solid #e10600 !important;
    border-radius: 8px !important;
}
.stButton>button:hover {
    background: #e10600 !important;
    color: #fff !important;
    border: 2px solid #fff !important;
}
.stProgress > div > div > div > div {
    background-color: #e10600 !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #e10600 !important;
}
.lex-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
}
.lex-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #e10600;
    letter-spacing: 1px;
}
.lex-sub {
    color: #bbb;
    margin-top: -6px;
}
.score-card {
    background: #1c1c22;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.hit-card {
    background: #18181f;
    border-left: 4px solid #e10600;
    padding: 10px 12px;
    margin: 8px 0;
    border-radius: 6px;
}
.phase-banner {
    background: linear-gradient(90deg, #e10600 0%, #23232a 100%);
    color: #fff;
    font-size: 1.15rem;
    font-weight: bold;
    text-align: center;
    border-radius: 8px;
    margin: 12px 0;
    padding: 10px 0;
}
</style>
"""
