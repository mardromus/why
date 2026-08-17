"""Evidence similarity lab powered by the RAG pipeline."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from rag.document_loader import extract_text_from_upload
from rag.pipeline import LegalRAGPipeline, SimilarityReport, evidence_to_text
from utils.helpers import get_case_by_id, load_cases


@st.cache_resource
def get_rag_pipeline() -> LegalRAGPipeline:
    return LegalRAGPipeline()


def _active_case() -> Optional[dict]:
    if st.session_state.get("custom_case"):
        return st.session_state.custom_case
    case_id = st.session_state.get("selected_case_id")
    if case_id:
        return get_case_by_id(case_id)
    return None


def render_similarity_report(report: SimilarityReport):
    st.markdown(f"### {report.evidence_name}")
    st.caption(report.evidence_preview or "No preview available.")
    if report.extraction_note:
        st.warning(report.extraction_note)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall", f"{report.overall_score:.0%}", report.label)
    c2.metric("Case context", f"{report.case_similarity:.0%}")
    c3.metric("Existing evidence", f"{report.evidence_similarity:.0%}")
    c4.metric("Legal materials", f"{report.legal_similarity:.0%}")
    st.progress(min(max(report.overall_score, 0.0), 1.0))
    st.info(report.recommendation)

    if report.analysis:
        st.markdown("#### Clerk's similarity note")
        st.write(report.analysis)

    def _render_hits(title: str, hits):
        st.markdown(f"#### {title}")
        if not hits:
            st.caption("No close matches.")
            return
        for hit in hits:
            st.markdown(
                f'<div class="hit-card"><b>{hit.title}</b> · {hit.source} · {hit.score:.0%}<br>{hit.text}</div>',
                unsafe_allow_html=True,
            )

    col_a, col_b = st.columns(2)
    with col_a:
        _render_hits("Similar case context", report.case_matches)
        _render_hits("Similar existing evidence", report.evidence_matches)
    with col_b:
        _render_hits("Similar statutory material", report.legal_matches)
        _render_hits("Similar principles / precedents", report.precedent_matches)


def render_evidence_lab(embedded: bool = False):
    st.header("Evidence similarity")
    st.write(
        "Upload an exhibit or paste its text. The RAG pipeline compares it with the "
        "selected case, existing evidence, and the legal knowledge base."
    )

    case = _active_case()
    cases = load_cases()
    if not case and cases:
        labels = ["Use selected courtroom case"] + [f"{c['case_id']}: {c['title']}" for c in cases]
        picked = st.selectbox("Compare against", labels, key="rag_case_picker")
        if picked != "Use selected courtroom case":
            case = get_case_by_id(picked.split(":")[0])

    if case:
        st.success(f"Active matter: {case.get('title')} ({case.get('case_id', 'custom')})")
        with st.expander("Case facts and listed evidence"):
            st.write(case.get("facts") or case.get("description", ""))
            for item in case.get("evidence") or []:
                st.markdown(f"- {evidence_to_text(item)}")
    else:
        st.warning("No case selected. Similarity will be measured against the legal knowledge base only.")

    source = st.radio("Evidence source", ["Upload file", "Paste text"], horizontal=True)
    evidence_text = ""
    evidence_name = "Pasted evidence"
    extraction_note = ""

    if source == "Upload file":
        uploaded = st.file_uploader(
            "Upload exhibit",
            type=["pdf", "docx", "txt", "md", "json", "csv"],
            key="rag_uploader",
        )
        if uploaded:
            evidence_name = uploaded.name
            evidence_text, extraction_note = extract_text_from_upload(uploaded)
            if extraction_note:
                st.warning(extraction_note)
            if evidence_text:
                st.text_area("Extracted text", evidence_text, height=180, key="rag_extracted")
    else:
        evidence_name = st.text_input("Exhibit name", value="User exhibit")
        evidence_text = st.text_area("Paste the evidence text", height=180, key="rag_paste")

    extra = []
    sim = st.session_state.get("simulation")
    if sim and getattr(sim, "evidence_presented", None):
        extra = [evidence_to_text(item.get("item") or item) for item in sim.evidence_presented]

    if st.button("Check similarity", type="primary", disabled=not bool((evidence_text or "").strip())):
        pipeline = get_rag_pipeline()
        with st.spinner("Retrieving similar context and drafting the clerk note..."):
            report = pipeline.score_evidence(
                evidence_text,
                case=case,
                evidence_name=evidence_name,
                extra_evidence=extra,
            )
        st.session_state.last_similarity_report = report.to_dict()
        st.session_state.last_similarity_object = report

    report = st.session_state.get("last_similarity_object")
    if report:
        render_similarity_report(report)
        if embedded and st.session_state.get("simulation") and st.session_state.get("selected_role") != "Observer":
            if st.button("Tender this exhibit in court"):
                sim = st.session_state.simulation
                side = "plaintiff" if "Plaintiff" in (st.session_state.get("selected_role") or "") else "defendant"
                sim.present_uploaded_evidence(side, report.evidence_name, report.evidence_preview, report.to_dict())
                st.success("Exhibit added to the court record.")
