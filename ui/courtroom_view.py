"""Courtroom hearing UI: observer auto-steps and interactive counsel."""

from __future__ import annotations

import streamlit as st

from frontend.components import CourtroomUI
from ui.evidence_lab import render_evidence_lab
from utils.helpers import format_evidence_label


def _play_audio(role: str, text: str):
    if not st.session_state.get("audio_on"):
        return
    engine = st.session_state.get("tts_engine")
    if engine and text:
        engine.speak(text, role=role)


def _user_side():
    role = st.session_state.get("selected_role")
    if role == "Plaintiff Lawyer":
        return "plaintiff"
    if role == "Defendant Lawyer":
        return "defendant"
    return None


def render_courtroom(case: dict):
    sim = st.session_state.simulation
    phase = st.session_state.current_phase
    ui = CourtroomUI()

    st.markdown(
        f"<div style='text-align:center'><h2>{case.get('title')}</h2>"
        f"<p>{case.get('description') or case.get('facts', '')}</p></div>",
        unsafe_allow_html=True,
    )
    ui.display_phase_banner(phase)
    ui.display_courtroom(sim.get_simulation_state(), st.session_state.get("current_speaker"))

    with st.expander("Live transcript", expanded=True):
        transcript = sim.get_transcript()
        if not transcript:
            st.caption("The record is empty. Start the hearing from the controls below.")
        for entry in transcript[-40:]:
            st.markdown(f"**{entry['speaker']}** ({entry.get('timestamp', '')}): {entry['content']}")

    if phase == "completed":
        st.success("Case closed. You can download the transcript from the sidebar.")
        return

    st.markdown("---")
    if st.session_state.selected_role == "Observer":
        _render_observer_controls(sim, phase)
    else:
        _render_counsel_controls(sim, case, phase)


def _advance_phase():
    from config import PHASES

    current = st.session_state.current_phase
    idx = PHASES.index(current) if current in PHASES else 0
    nxt = PHASES[idx + 1] if idx + 1 < len(PHASES) else "completed"
    st.session_state.current_phase = nxt
    st.session_state.simulation.set_current_phase(nxt)
    st.session_state.step_token = 0


def _render_observer_controls(sim, phase: str):
    st.subheader("Observer controls")
    st.caption("Each click generates the next courtroom turn. Nothing auto-plays, so Streamlit Cloud will not time out.")
    if st.button("Play next step", type="primary"):
        _observer_step(sim, phase)
        st.rerun()
    if phase != "completed" and st.button("Skip to next phase"):
        _advance_phase()
        st.rerun()


def _observer_step(sim, phase: str):
    token = st.session_state.get("step_token", 0)
    if phase == "opening":
        if token == 0:
            text = sim.generate_opening("plaintiff")
            st.session_state.current_speaker = "plaintiff"
            _play_audio("plaintiff", text)
            st.session_state.step_token = 1
        else:
            text = sim.generate_opening("defendant")
            st.session_state.current_speaker = "defendant"
            _play_audio("defendant", text)
            _advance_phase()
    elif phase == "examination_in_chief":
        if token == 0:
            text = sim.generate_examination_question()
            st.session_state.last_question = text
            _play_audio("plaintiff", text)
            st.session_state.step_token = 1
        else:
            text = sim.generate_witness_answer(st.session_state.get("last_question", "What happened?"))
            _play_audio("witness", text)
            _advance_phase()
    elif phase == "cross_examination":
        if token == 0:
            text = sim.generate_cross_question()
            st.session_state.last_question = text
            _play_audio("defendant", text)
            st.session_state.step_token = 1
        else:
            text = sim.generate_witness_answer(st.session_state.get("last_question", "Is that accurate?"))
            _play_audio("witness", text)
            _advance_phase()
    elif phase == "evidence":
        evidence = sim.case_data.get("evidence") or []
        if not evidence:
            _advance_phase()
            return
        index = st.session_state.get("evidence_index", 0)
        side = st.session_state.get("evidence_side", "plaintiff")
        if index < len(evidence):
            text = sim.present_case_evidence(side, index)
            _play_audio(side, text or "")
            st.session_state.evidence_index = index + 1
        elif side == "plaintiff":
            st.session_state.evidence_side = "defendant"
            st.session_state.evidence_index = 0
        else:
            st.session_state.evidence_index = 0
            st.session_state.evidence_side = "plaintiff"
            _advance_phase()
    elif phase == "objection":
        if token == 0:
            text = sim.generate_objection()
            st.session_state.last_objection = text
            _play_audio("defendant", text)
            st.session_state.step_token = 1
        else:
            text = sim.generate_ruling(st.session_state.get("last_objection", "Objection."))
            _play_audio("judge", text)
            _advance_phase()
    elif phase == "closing":
        if token == 0:
            text = sim.generate_closing("plaintiff")
            _play_audio("plaintiff", text)
            st.session_state.step_token = 1
        else:
            text = sim.generate_closing("defendant")
            _play_audio("defendant", text)
            _advance_phase()
    elif phase == "judgment":
        text = sim.generate_judgment()
        _play_audio("judge", text)
        _advance_phase()


def _render_counsel_controls(sim, case: dict, phase: str):
    side = _user_side()
    opponent = "defendant" if side == "plaintiff" else "plaintiff"
    st.subheader("Your turn")

    if phase == "opening":
        _counsel_statement_phase(
            sim,
            side,
            user_label="Opening statement",
            user_flag="user_opening_done",
            ai_flag="ai_opening_done",
            user_fn=lambda text: sim.record_user_turn(
                "Plaintiff Lawyer" if side == "plaintiff" else "Defendant Lawyer",
                text,
                side,
            ),
            ai_fn=lambda: sim.generate_opening(opponent),
            ai_role=opponent,
        )
    elif phase in {"examination_in_chief", "cross_examination"}:
        examining = side == "plaintiff" if phase == "examination_in_chief" else side == "defendant"
        if examining:
            question = st.text_area("Question for the witness", key=f"q_{phase}")
            if st.button("Put the question", type="primary") and question.strip():
                speaker = "Plaintiff Lawyer" if side == "plaintiff" else "Defendant Lawyer"
                sim.record_user_turn(speaker, question, side)
                answer = sim.generate_witness_answer(question)
                _play_audio("witness", answer)
                st.rerun()
            if st.button("Finish this examination"):
                _advance_phase()
                st.rerun()
        else:
            st.info("Opposing counsel is examining. Generate their question, then the witness will answer.")
            if st.button("Hear opposing question and answer", type="primary"):
                q = sim.generate_examination_question() if phase == "examination_in_chief" else sim.generate_cross_question()
                a = sim.generate_witness_answer(q)
                _play_audio(opponent, q)
                _play_audio("witness", a)
                _advance_phase()
                st.rerun()
    elif phase == "evidence":
        _render_evidence_phase(sim, case, side)
    elif phase == "objection":
        objection = st.text_area("Objection (leave blank to let AI raise one)", key="user_objection")
        if st.button("Raise / generate objection", type="primary"):
            text = objection.strip() or sim.generate_objection()
            if objection.strip():
                speaker = "Plaintiff Lawyer" if side == "plaintiff" else "Defendant Lawyer"
                sim.record_user_turn(speaker, text, side)
            ruling = sim.generate_ruling(text)
            _play_audio("judge", ruling)
            st.rerun()
        if st.button("Proceed after ruling"):
            _advance_phase()
            st.rerun()
    elif phase == "closing":
        _counsel_statement_phase(
            sim,
            side,
            user_label="Closing argument",
            user_flag="user_closing_done",
            ai_flag="ai_closing_done",
            user_fn=lambda text: sim.record_user_turn(
                "Plaintiff Lawyer" if side == "plaintiff" else "Defendant Lawyer",
                text,
                side,
            ),
            ai_fn=lambda: sim.generate_closing(opponent),
            ai_role=opponent,
        )
    elif phase == "judgment":
        if st.button("Call for judgment", type="primary"):
            text = sim.generate_judgment()
            _play_audio("judge", text)
            _advance_phase()
            st.rerun()


def _counsel_statement_phase(sim, side, user_label, user_flag, ai_flag, user_fn, ai_fn, ai_role):
    if not st.session_state.get(user_flag):
        text = st.text_area(user_label, key=f"area_{user_flag}")
        if st.button(f"Submit {user_label.lower()}", type="primary") and text.strip():
            spoken = user_fn(text)
            _play_audio(side, spoken)
            st.session_state[user_flag] = True
            st.rerun()
        return
    if not st.session_state.get(ai_flag):
        if st.button("Hear the opposing address", type="primary"):
            spoken = ai_fn()
            _play_audio(ai_role, spoken)
            st.session_state[ai_flag] = True
            st.rerun()
        return
    if st.button("Proceed to next phase", type="primary"):
        st.session_state[user_flag] = False
        st.session_state[ai_flag] = False
        _advance_phase()
        st.rerun()


def _render_evidence_phase(sim, case: dict, side: str):
    st.write("Tender listed exhibits, or upload a new exhibit and run the similarity RAG check first.")
    listed = case.get("evidence") or []
    options = [format_evidence_label(item) for item in listed]
    if options:
        choice = st.selectbox("Listed evidence", options)
        if st.button("Present listed exhibit"):
            index = options.index(choice)
            text = sim.present_case_evidence(side, index)
            _play_audio(side, text or "")
            st.rerun()

    st.markdown("#### Upload and test similarity")
    render_evidence_lab(embedded=True)
    if st.button("Close evidence phase"):
        _advance_phase()
        st.rerun()
