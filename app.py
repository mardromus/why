import streamlit as st

from config import APP_NAME, APP_TAGLINE, PHASES, get_groq_api_key

st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from courtroom import create_simulation
from ui.courtroom_view import render_courtroom
from ui.evidence_lab import render_evidence_lab
from ui.legal_library import render_legal_library
from ui.setup import render_case_selection, render_header, render_login, render_role_selection
from ui.styles import COURTROOM_CSS
from utils.helpers import build_simulation_case, phase_label
from utils.tts import TTSEngine

st.markdown(COURTROOM_CSS, unsafe_allow_html=True)


def _init_state():
    defaults = {
        "logged_in": False,
        "username": None,
        "selected_case_id": None,
        "custom_case": None,
        "selected_role": None,
        "current_phase": "opening",
        "current_speaker": None,
        "audio_on": False,
        "step_token": 0,
        "evidence_index": 0,
        "evidence_side": "plaintiff",
        "history": [],
        "show_end_confirm": False,
        "show_restart_confirm": False,
        "nav_page": "Courtroom",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "tts_engine" not in st.session_state:
        st.session_state.tts_engine = TTSEngine()


def _snapshot():
    keys = [
        "simulation",
        "transcript",
        "current_phase",
        "selected_witness",
        "current_speaker",
        "selected_case_id",
        "selected_role",
        "step_token",
        "evidence_index",
        "evidence_side",
    ]
    return {k: st.session_state.get(k) for k in keys}


def _clear_hearing(keep_case: bool = True):
    keys = [
        "simulation",
        "current_phase",
        "current_speaker",
        "step_token",
        "evidence_index",
        "evidence_side",
        "last_question",
        "last_objection",
        "user_opening_done",
        "ai_opening_done",
        "user_closing_done",
        "ai_closing_done",
        "last_similarity_report",
        "last_similarity_object",
        "history",
    ]
    if not keep_case:
        keys.extend(["selected_case_id", "custom_case", "selected_role"])
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.current_phase = "opening"
    st.session_state.step_token = 0
    st.session_state.evidence_index = 0
    st.session_state.evidence_side = "plaintiff"


def render_sidebar(case):
    st.sidebar.header("Hearing controls")
    st.session_state.audio_on = st.sidebar.checkbox("Generate speech audio", value=st.session_state.audio_on)
    if not get_groq_api_key():
        st.sidebar.error("Set GROQ_API_KEY in Streamlit secrets or `.env`.")
    else:
        st.sidebar.caption("Groq LLM connected.")

    phase = st.session_state.get("current_phase", "opening")
    try:
        progress = PHASES.index(phase) / (len(PHASES) - 1)
    except ValueError:
        progress = 0
    st.sidebar.progress(progress, text=f"Phase: {phase_label(phase)}")

    if case:
        st.sidebar.markdown(f"**Matter:** {case.get('title', '')}")
        st.sidebar.caption(f"Role: {st.session_state.get('selected_role') or '—'}")

    if st.sidebar.button("Undo last snapshot"):
        history = st.session_state.get("history") or []
        if history:
            last = history.pop()
            for key, value in last.items():
                st.session_state[key] = value
            st.rerun()
        else:
            st.sidebar.warning("Nothing to undo.")

    if st.sidebar.button("End hearing"):
        st.session_state.show_end_confirm = True
    if st.session_state.get("show_end_confirm"):
        if st.sidebar.checkbox("Confirm end hearing"):
            _clear_hearing(keep_case=False)
            st.session_state.show_end_confirm = False
            st.rerun()

    if st.sidebar.button("Restart hearing"):
        st.session_state.show_restart_confirm = True
    if st.session_state.get("show_restart_confirm"):
        if st.sidebar.checkbox("Confirm restart"):
            _clear_hearing(keep_case=True)
            st.session_state.show_restart_confirm = False
            st.rerun()

    sim = st.session_state.get("simulation")
    if sim and sim.get_transcript():
        st.sidebar.download_button(
            "Download transcript",
            data=sim.transcript_text(),
            file_name="courtroom_transcript.txt",
            mime="text/plain",
        )

    st.sidebar.markdown("---")
    st.session_state.nav_page = st.sidebar.radio(
        "Workspace",
        ["Courtroom", "Evidence similarity", "Legal library"],
        index=["Courtroom", "Evidence similarity", "Legal library"].index(st.session_state.nav_page)
        if st.session_state.nav_page in {"Courtroom", "Evidence similarity", "Legal library"}
        else 0,
    )


def ensure_simulation(case: dict):
    if "simulation" not in st.session_state:
        st.session_state.simulation = create_simulation(build_simulation_case(case))
        st.session_state.current_phase = "opening"
        st.session_state.step_token = 0
        st.session_state.history = []
        st.session_state.history.append(_snapshot())


def main():
    _init_state()
    render_header()
    render_login()
    case = render_case_selection()
    render_role_selection()
    ensure_simulation(case)
    render_sidebar(case)

    page = st.session_state.nav_page
    if page == "Evidence similarity":
        render_evidence_lab(embedded=False)
        return
    if page == "Legal library":
        render_legal_library()
        return
    render_courtroom(case)


main()
