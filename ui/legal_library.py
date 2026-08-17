"""Browse and search the legal knowledge base."""

from __future__ import annotations

import streamlit as st

from ui.evidence_lab import get_rag_pipeline
from utils.knowledge_base import knowledge_base


def render_legal_library():
    st.header("Legal library")
    st.write("Search statutes, principles, and precedents used by the RAG retriever.")

    query = st.text_input("Search", placeholder="e.g. breach of contract, electronic record, section 65B")
    if query:
        pipeline = get_rag_pipeline()
        hits = pipeline.search(query, top_k=10)
        if not hits:
            st.info("No ranked matches. Try a shorter phrase.")
        for hit in hits:
            st.markdown(
                f'<div class="hit-card"><b>{hit.title}</b> · {hit.source} · {hit.score:.0%}<br>{hit.text}</div>',
                unsafe_allow_html=True,
            )

    tabs = st.tabs(["Statutes", "Principles", "Precedents"])
    with tabs[0]:
        for act in knowledge_base.legal_codes:
            with st.expander(act.get("name", "Act")):
                for section in act.get("sections") or []:
                    st.markdown(f"**§ {section.get('number')}** {section.get('title') or ''}")
                    st.write(section.get("text", ""))
    with tabs[1]:
        for principle in knowledge_base.legal_principles:
            st.markdown(f"**{principle.get('title')}**")
            st.write(principle.get("description", ""))
            keys = principle.get("key_principles") or principle.get("principles") or []
            for item in keys:
                st.markdown(f"- {item}")
    with tabs[2]:
        for precedent in knowledge_base.precedents:
            st.markdown(
                f"**{precedent.get('title')}** ({precedent.get('court', '')}, {precedent.get('year', '')})"
            )
            st.write(precedent.get("summary", ""))
