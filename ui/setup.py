"""Login, case selection, and role selection."""

from __future__ import annotations

import time
from typing import Optional

import streamlit as st

from config import AUTH_ENABLED, DEMO_PASSWORD, DEMO_USERNAME
from utils.helpers import get_case_by_id, load_cases


def render_header():
    from pathlib import Path

    cols = st.columns([1, 6])
    with cols[0]:
        logo = Path("logo.png")
        if logo.exists():
            st.image(str(logo), width=92)
        else:
            st.markdown("<div style='font-size:3rem;'>⚖️</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(
            '<div class="lex-title">Lex Orion</div>'
            '<div class="lex-sub">Indian Court Simulator with evidence similarity RAG</div>',
            unsafe_allow_html=True,
        )


def render_login() -> bool:
    if st.session_state.get("logged_in"):
        return True
    if not AUTH_ENABLED:
        st.session_state.logged_in = True
        st.session_state.username = "guest"
        return True

    st.subheader("Sign in")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        guest = st.button("Continue as guest", use_container_width=True)
        login = st.button("Login", type="primary", use_container_width=True)
        if guest:
            st.session_state.logged_in = True
            st.session_state.username = "guest"
            st.rerun()
        if login:
            if username == DEMO_USERNAME and password == DEMO_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Welcome to Lex Orion.")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.caption("Demo login is `admin` / `1234`, or continue as guest.")
    st.stop()


def render_case_selection() -> Optional[dict]:
    if st.session_state.get("custom_case"):
        return st.session_state.custom_case
    if st.session_state.get("selected_case_id"):
        return get_case_by_id(st.session_state.selected_case_id)

    st.subheader("Select a case")
    cases = load_cases()
    titles = [f"{case['case_id']}: {case['title']}" for case in cases]
    titles.append("➕ Create new case")
    choice = st.selectbox("Choose a case", titles)

    if choice == "➕ Create new case":
        with st.form("create_case_form"):
            title = st.text_input("Case title")
            case_type = st.selectbox(
                "Case type",
                [
                    "Contract Dispute",
                    "Property Dispute",
                    "Family Law",
                    "Consumer Protection",
                    "Commercial Dispute",
                    "Tort Claim",
                    "Other",
                ],
            )
            plaintiff = st.text_input("Plaintiff")
            defendant = st.text_input("Defendant")
            description = st.text_area("Case description / facts")
            witnesses_raw = st.text_area("Witnesses (one per line: Name:Role:Statement)")
            evidence_raw = st.text_area("Evidence (one per line)")
            submitted = st.form_submit_button("Create case")
        if submitted:
            witnesses = []
            for line in witnesses_raw.splitlines():
                parts = [p.strip() for p in line.split(":")]
                if len(parts) >= 2:
                    witness = {"name": parts[0], "role": parts[1]}
                    if len(parts) > 2:
                        witness["testimony"] = ":".join(parts[2:]).strip()
                    witnesses.append(witness)
            evidence = [
                {"id": f"EVD-C{i+1}", "type": "Document", "description": row.strip(), "relevance": "User-supplied"}
                for i, row in enumerate(evidence_raw.splitlines())
                if row.strip()
            ]
            st.session_state.custom_case = {
                "case_id": "custom",
                "title": title or "Custom case",
                "case_type": case_type,
                "parties": {"plaintiff": plaintiff, "defendant": defendant},
                "description": description,
                "facts": description,
                "witnesses": witnesses,
                "evidence": evidence,
            }
            st.rerun()
        st.stop()

    if st.button("Confirm case", type="primary") and choice != "➕ Create new case":
        st.session_state.selected_case_id = choice.split(":")[0]
        st.rerun()
    st.stop()


def render_role_selection() -> Optional[str]:
    if st.session_state.get("selected_role"):
        return st.session_state.selected_role

    st.subheader("Choose your role")
    roles = {
        "Plaintiff Lawyer": "Present the plaintiff's case, tender evidence, and examine witnesses.",
        "Defendant Lawyer": "Challenge the claim, cross-examine, and test evidence similarity.",
        "Observer": "Watch AI counsel and the bench run the hearing step by step.",
    }
    cols = st.columns(3)
    for col, (role, desc) in zip(cols, roles.items()):
        with col:
            st.markdown(f"### {role}")
            st.caption(desc)
    role = st.selectbox("Select your role", list(roles))
    if st.button("Confirm role", type="primary"):
        st.session_state.selected_role = role
        st.rerun()
    st.stop()
