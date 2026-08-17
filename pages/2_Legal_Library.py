import streamlit as st

st.set_page_config(page_title="Legal Library | Lex Orion", page_icon="⚖️", layout="wide")

from ui.legal_library import render_legal_library
from ui.setup import render_header
from ui.styles import COURTROOM_CSS

st.markdown(COURTROOM_CSS, unsafe_allow_html=True)
render_header()
render_legal_library()
