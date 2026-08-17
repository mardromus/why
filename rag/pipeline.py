"""RAG pipeline: retrieve similar legal/case context for uploaded evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from config import DATA_DIR, LEGAL_CODES_DIR
from rag.document_loader import chunk_text, extract_text_from_upload
from rag.embeddings import (
    TfidfRetriever,
    recommendation_from_score,
    similarity_label,
)

SOURCE_LEGAL = "legal_code"
SOURCE_PRECEDENT = "precedent"
SOURCE_PRINCIPLE = "legal_principle"
SOURCE_CASE = "case_context"
SOURCE_EVIDENCE = "case_evidence"
SOURCE_WITNESS = "witness"
SOURCE_UPLOAD = "uploaded_evidence"


@dataclass
class RAGDocument:
    doc_id: str
    text: str
    source: str
    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str
    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimilarityReport:
    evidence_name: str
    evidence_preview: str
    overall_score: float
    label: str
    case_similarity: float
    evidence_similarity: float
    legal_similarity: float
    case_matches: List[RetrievedChunk] = field(default_factory=list)
    evidence_matches: List[RetrievedChunk] = field(default_factory=list)
    legal_matches: List[RetrievedChunk] = field(default_factory=list)
    precedent_matches: List[RetrievedChunk] = field(default_factory=list)
    analysis: str = ""
    recommendation: str = ""
    extraction_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _preview(text: str, limit: int = 420) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


class LegalRAGPipeline:
    """Ingest legal knowledge + case files, then score uploaded evidence."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir or DATA_DIR)
        self.retriever = TfidfRetriever()
        self.legal_docs: List[RAGDocument] = []
        self._legal_index = None
        self.build_legal_index()

    def build_legal_index(self) -> None:
        self.legal_docs = []
        self.legal_docs.extend(self._load_legal_codes())
        self.legal_docs.extend(self._load_precedents())
        self.legal_docs.extend(self._load_principles())
        if self.legal_docs:
            self._legal_index = self.retriever.build([doc.text for doc in self.legal_docs])
        else:
            self._legal_index = None

    def ingest_case(self, case: Dict[str, Any]) -> List[RAGDocument]:
        docs: List[RAGDocument] = []
        case_id = str(case.get("case_id") or case.get("id") or "case")
        title = case.get("title", case_id)
        description = case.get("description") or case.get("facts") or ""
        facts = case.get("facts") or ""
        parties = case.get("parties") or {}
        party_text = f"Plaintiff: {parties.get('plaintiff', case.get('plaintiff', ''))}. Defendant: {parties.get('defendant', case.get('defendant', ''))}."
        core = "\n".join(
            part for part in [title, case.get("case_type", ""), party_text, description, facts] if part
        )
        if core.strip():
            docs.append(
                RAGDocument(
                    doc_id=f"{case_id}-facts",
                    text=core,
                    source=SOURCE_CASE,
                    title=f"Case facts: {title}",
                    metadata={"case_id": case_id, "kind": "facts"},
                )
            )

        for idx, item in enumerate(case.get("evidence") or [], start=1):
            text = evidence_to_text(item)
            if not text:
                continue
            item_id = item.get("id", f"EVD-{idx}") if isinstance(item, dict) else f"EVD-{idx}"
            docs.append(
                RAGDocument(
                    doc_id=f"{case_id}-{item_id}",
                    text=text,
                    source=SOURCE_EVIDENCE,
                    title=f"Existing evidence {item_id}",
                    metadata={"case_id": case_id, "evidence_id": item_id},
                )
            )

        for idx, witness in enumerate(case.get("witnesses") or [], start=1):
            if isinstance(witness, dict):
                text = " | ".join(
                    str(witness.get(key, ""))
                    for key in ("name", "role", "testimony", "statement")
                    if witness.get(key)
                )
                name = witness.get("name", f"Witness {idx}")
            else:
                text = str(witness)
                name = f"Witness {idx}"
            if text.strip():
                docs.append(
                    RAGDocument(
                        doc_id=f"{case_id}-wit-{idx}",
                        text=text,
                        source=SOURCE_WITNESS,
                        title=f"Witness: {name}",
                        metadata={"case_id": case_id},
                    )
                )
        return docs

    def retrieve_legal(self, query: str, top_k: int = 6) -> List[RetrievedChunk]:
        if not self._legal_index or not self.legal_docs:
            return []
        hits = self.retriever.query(self._legal_index, query, top_k=top_k)
        return [self._to_chunk(self.legal_docs[i], score) for i, score in hits]

    def retrieve_from_docs(self, query: str, docs: Sequence[RAGDocument], top_k: int = 6) -> List[RetrievedChunk]:
        if not docs:
            return []
        index = self.retriever.build([doc.text for doc in docs])
        hits = self.retriever.query(index, query, top_k=top_k)
        return [self._to_chunk(docs[i], score) for i, score in hits]

    def score_evidence(
        self,
        evidence_text: str,
        case: Optional[Dict[str, Any]] = None,
        evidence_name: str = "Uploaded evidence",
        extra_evidence: Optional[Sequence[str]] = None,
        include_analysis: bool = True,
    ) -> SimilarityReport:
        text = (evidence_text or "").strip()
        case_docs = self.ingest_case(case or {})
        if extra_evidence:
            for idx, extra in enumerate(extra_evidence, start=1):
                if extra and str(extra).strip():
                    case_docs.append(
                        RAGDocument(
                            doc_id=f"extra-{idx}",
                            text=str(extra),
                            source=SOURCE_EVIDENCE,
                            title=f"Presented evidence {idx}",
                            metadata={"kind": "presented"},
                        )
                    )

        fact_docs = [d for d in case_docs if d.source in {SOURCE_CASE, SOURCE_WITNESS}]
        evidence_docs = [d for d in case_docs if d.source == SOURCE_EVIDENCE]

        case_matches = self.retrieve_from_docs(text, fact_docs, top_k=5)
        evidence_matches = self.retrieve_from_docs(text, evidence_docs, top_k=5)
        legal_hits = self.retrieve_legal(text, top_k=8)
        legal_matches = [h for h in legal_hits if h.source == SOURCE_LEGAL][:5]
        precedent_matches = [h for h in legal_hits if h.source in {SOURCE_PRECEDENT, SOURCE_PRINCIPLE}][:5]

        case_similarity = self._max_score(case_matches)
        if fact_docs:
            joined_facts = "\n".join(d.text for d in fact_docs)
            case_similarity = max(case_similarity, self.retriever.pairwise_score(text, joined_facts))
        evidence_similarity = self._max_score(evidence_matches)
        legal_similarity = self._max_score(legal_matches + precedent_matches)

        overall = self._overall_score(case_similarity, evidence_similarity, legal_similarity)
        report = SimilarityReport(
            evidence_name=evidence_name,
            evidence_preview=_preview(text),
            overall_score=overall,
            label=similarity_label(overall),
            case_similarity=case_similarity,
            evidence_similarity=evidence_similarity,
            legal_similarity=legal_similarity,
            case_matches=case_matches,
            evidence_matches=evidence_matches,
            legal_matches=legal_matches,
            precedent_matches=precedent_matches,
            recommendation=recommendation_from_score(overall),
        )
        if include_analysis:
            report.analysis = self._generate_analysis(text, case or {}, report)
        else:
            report.analysis = self._fallback_analysis(report)
        return report

    def score_upload(self, uploaded: Any, case: Optional[Dict[str, Any]] = None) -> SimilarityReport:
        text, note = extract_text_from_upload(uploaded)
        name = str(getattr(uploaded, "name", "uploaded_evidence"))
        if not text:
            return SimilarityReport(
                evidence_name=name,
                evidence_preview="",
                overall_score=0.0,
                label="Dissimilar",
                case_similarity=0.0,
                evidence_similarity=0.0,
                legal_similarity=0.0,
                analysis=note or "No text could be extracted from the upload.",
                recommendation="Re-upload a text-based PDF, DOCX, or TXT file.",
                extraction_note=note,
            )
        chunks = chunk_text(text)
        query = " ".join(chunks[:3]) if chunks else text
        report = self.score_evidence(query, case=case, evidence_name=name)
        report.extraction_note = note
        report.evidence_preview = _preview(text)
        return report

    def search(self, query: str, top_k: int = 8) -> List[RetrievedChunk]:
        return self.retrieve_legal(query, top_k=top_k)

    def _generate_analysis(self, evidence_text: str, case: Dict[str, Any], report: SimilarityReport) -> str:
        try:
            from llm.groq_api import groq_api
        except Exception:
            return self._fallback_analysis(report)

        case_title = case.get("title", "the current matter")
        facts = case.get("facts") or case.get("description") or ""
        retrieved = self._format_hits(report.case_matches + report.evidence_matches + report.legal_matches)
        prompt = f"""You are an Indian court clerk helping assess whether uploaded evidence is contextually similar to a case.

Case title: {case_title}
Case type: {case.get('case_type', 'Civil')}
Facts: {facts}

Uploaded evidence (excerpt):
{evidence_text[:3500]}

Similarity scores (0 to 1):
- Overall: {report.overall_score:.2f} ({report.label})
- Case facts: {report.case_similarity:.2f}
- Existing evidence: {report.evidence_similarity:.2f}
- Legal materials: {report.legal_similarity:.2f}

Most similar retrieved context:
{retrieved or 'None'}

Write a concise clerk note with:
1. Whether the uploaded material is about the same dispute/context
2. Whether it supports, duplicates, or contradicts existing evidence
3. Any Indian Evidence Act admissibility caution (relevance, hearsay, electronic records)
4. A one-line recommendation for the bench

Do not invent facts that are not in the materials."""

        try:
            result = groq_api.generate_response(prompt)
            analysis = (result or {}).get("response") if isinstance(result, dict) else None
            if not analysis:
                return self._fallback_analysis(report)
            return analysis.strip()
        except Exception:
            return self._fallback_analysis(report)

    def _fallback_analysis(self, report: SimilarityReport) -> str:
        return (
            f"Automated similarity only (LLM unavailable). Overall score {report.overall_score:.2f} "
            f"({report.label}). Case-context match {report.case_similarity:.2f}, "
            f"existing-evidence match {report.evidence_similarity:.2f}, "
            f"legal-material match {report.legal_similarity:.2f}. {report.recommendation}"
        )

    def _load_legal_codes(self) -> List[RAGDocument]:
        docs: List[RAGDocument] = []
        codes_dir = LEGAL_CODES_DIR
        if not codes_dir.exists():
            return docs
        seen = set()
        for path in sorted(codes_dir.glob("*.json")):
            try:
                data = _read_json(path)
            except Exception:
                continue
            act = data.get("name") or path.stem.replace("_", " ").title()
            for section in data.get("sections") or []:
                number = str(section.get("number", "")).strip()
                title = section.get("title") or ""
                text = section.get("text") or ""
                body = f"{act} Section {number}: {title}. {text}".strip()
                key = body.lower()
                if not text or key in seen:
                    continue
                seen.add(key)
                docs.append(
                    RAGDocument(
                        doc_id=f"code-{path.stem}-{number}",
                        text=body,
                        source=SOURCE_LEGAL,
                        title=f"{act} § {number}",
                        metadata={"act": act, "section": number, "file": path.name},
                    )
                )
        return docs

    def _load_precedents(self) -> List[RAGDocument]:
        path = self.data_dir / "precedents.json"
        if not path.exists():
            return []
        try:
            raw = _read_json(path)
        except Exception:
            return []
        items = raw if isinstance(raw, list) else raw.get("precedents") or []
        docs = []
        for item in items:
            principles = item.get("principles") or []
            principle_text = "; ".join(principles) if isinstance(principles, list) else str(principles)
            text = (
                f"{item.get('title', '')} ({item.get('court', '')}, {item.get('year', '')}). "
                f"{item.get('summary', '')} Principles: {principle_text}"
            )
            docs.append(
                RAGDocument(
                    doc_id=str(item.get("id") or item.get("title")),
                    text=text,
                    source=SOURCE_PRECEDENT,
                    title=item.get("title", "Precedent"),
                    metadata={"case_type": item.get("case_type", "")},
                )
            )
        return docs

    def _load_principles(self) -> List[RAGDocument]:
        path = self.data_dir / "legal_principles.json"
        if not path.exists():
            return []
        try:
            raw = _read_json(path)
        except Exception:
            return []
        items = raw if isinstance(raw, list) else raw.get("principles") or []
        docs = []
        for item in items:
            keys = item.get("key_principles") or item.get("principles") or []
            key_text = "; ".join(keys) if isinstance(keys, list) else str(keys)
            keywords = item.get("keywords") or []
            text = (
                f"{item.get('title', '')}: {item.get('description', '')} "
                f"Keywords: {', '.join(keywords) if isinstance(keywords, list) else keywords}. "
                f"Principles: {key_text}"
            )
            docs.append(
                RAGDocument(
                    doc_id=str(item.get("id") or item.get("title")),
                    text=text,
                    source=SOURCE_PRINCIPLE,
                    title=item.get("title", "Legal principle"),
                    metadata={"keywords": keywords},
                )
            )
        return docs

    @staticmethod
    def _to_chunk(doc: RAGDocument, score: float) -> RetrievedChunk:
        return RetrievedChunk(
            text=doc.text,
            score=float(score),
            source=doc.source,
            title=doc.title,
            metadata=doc.metadata,
        )

    @staticmethod
    def _max_score(chunks: Sequence[RetrievedChunk]) -> float:
        if not chunks:
            return 0.0
        return max(c.score for c in chunks)

    @staticmethod
    def _overall_score(case_sim: float, evidence_sim: float, legal_sim: float) -> float:
        if evidence_sim > 0:
            return round(0.45 * case_sim + 0.35 * evidence_sim + 0.20 * legal_sim, 4)
        return round(0.70 * case_sim + 0.30 * legal_sim, 4)

    @staticmethod
    def _format_hits(chunks: Sequence[RetrievedChunk], limit: int = 6) -> str:
        lines = []
        for chunk in chunks[:limit]:
            lines.append(f"- [{chunk.source}] {chunk.title} (score {chunk.score:.2f}): {_preview(chunk.text, 240)}")
        return "\n".join(lines)


def evidence_to_text(item: Any) -> str:
    if item is None:
        return ""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        parts = [
            str(item.get(key, "")).strip()
            for key in ("id", "type", "description", "relevance", "content", "text")
            if item.get(key)
        ]
        return " | ".join(parts)
    return str(item).strip()
