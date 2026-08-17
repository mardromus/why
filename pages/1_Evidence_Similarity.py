import streamlit as st

st.set_page_config(page_title="Evidence Similarity | Lex Orion", page_icon="⚖️", layout="wide")

from ui.evidence_lab import render_evidence_lab
from ui.setup import render_header
from ui.styles import COURTROOM_CSS

st.markdown(COURTROOM_CSS, unsafe_allow_html=True)
render_header()
render_evidence_lab(embedded=False)
