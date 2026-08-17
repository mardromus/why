# utils/knowledge_base.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import DATA_DIR, LEGAL_CODES_DIR


def _load_json(path: Path, default: Any):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default


class KnowledgeBase:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir or DATA_DIR)
        self.precedents: List[Dict[str, Any]] = []
        self.legal_principles: List[Dict[str, Any]] = []
        self.legal_codes: List[Dict[str, Any]] = []
        self.load_knowledge_base()

    def load_knowledge_base(self):
        precedents_raw = _load_json(self.data_dir / "precedents.json", [])
        if isinstance(precedents_raw, dict):
            self.precedents = precedents_raw.get("precedents") or []
        else:
            self.precedents = precedents_raw or []

        principles_raw = _load_json(self.data_dir / "legal_principles.json", [])
        if isinstance(principles_raw, dict):
            self.legal_principles = principles_raw.get("principles") or []
        else:
            self.legal_principles = principles_raw or []

        self.legal_codes = []
        codes_dir = LEGAL_CODES_DIR
        if codes_dir.exists():
            seen_acts = set()
            for path in sorted(codes_dir.glob("*.json")):
                data = _load_json(path, {})
                if not isinstance(data, dict):
                    continue
                act_name = data.get("name") or path.stem
                if act_name in seen_acts and not data.get("sections"):
                    continue
                seen_acts.add(act_name)
                data["_file"] = path.name
                self.legal_codes.append(data)

    def get_section(self, section_id: str) -> Optional[Dict[str, Any]]:
        needle = str(section_id).lower()
        for principle in self.legal_principles:
            if str(principle.get("id", "")).lower() == needle:
                return principle
        for act in self.legal_codes:
            for section in act.get("sections") or []:
                if str(section.get("number", "")).lower() == needle:
                    return {"act": act.get("name"), **section}
        return None

    def get_section_text(self, act_name: str, section_number: Any) -> Optional[str]:
        target_act = (act_name or "").lower()
        target_section = str(section_number).lower()
        for act in self.legal_codes:
            if target_act not in (act.get("name") or "").lower() and target_act not in (act.get("_file") or "").lower():
                continue
            for section in act.get("sections") or []:
                if str(section.get("number", "")).lower() == target_section:
                    title = section.get("title") or ""
                    text = section.get("text") or ""
                    return f"{title}: {text}".strip(": ")
        return None

    def search_principles(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").lower()
        results = []
        for principle in self.legal_principles:
            blob = " ".join(
                [
                    str(principle.get("title", "")),
                    str(principle.get("description", "")),
                    " ".join(principle.get("keywords") or []),
                ]
            ).lower()
            if q in blob:
                results.append(principle)
        return results

    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        q = (query or "").lower()
        sections = []
        for act in self.legal_codes:
            for section in act.get("sections") or []:
                blob = f"{act.get('name', '')} {section.get('number', '')} {section.get('title', '')} {section.get('text', '')}".lower()
                if q in blob:
                    sections.append({"act": act.get("name"), **section})
        precedents = [
            p
            for p in self.precedents
            if q in json.dumps(p).lower()
        ]
        return {
            "sections": sections[:20],
            "precedents": precedents[:10],
            "principles": self.search_principles(query)[:10],
        }

    def get_relevant_precedents(self, case_type: str) -> List[Dict[str, Any]]:
        needle = (case_type or "").lower()
        return [
            precedent
            for precedent in self.precedents
            if needle in (precedent.get("case_type") or "").lower()
            or needle in (precedent.get("title") or "").lower()
            or needle in (precedent.get("summary") or "").lower()
        ]

    def add_precedent(self, precedent: Dict[str, Any]):
        self.precedents.append(precedent)
        self.save_knowledge_base()

    def add_legal_principle(self, principle: Dict[str, Any]):
        self.legal_principles.append(principle)
        self.save_knowledge_base()

    def get_legal_advice(self, case_facts: Dict[str, Any]) -> Dict[str, Any]:
        description = (case_facts.get("description") or case_facts.get("facts") or "").lower()
        relevant_sections = []
        for principle in self.legal_principles:
            keywords = [k.lower() for k in principle.get("keywords", [])]
            if keywords and any(keyword in description for keyword in keywords):
                relevant_sections.append(principle)

        applicable_precedents = self.get_relevant_precedents(case_facts.get("case_type", ""))
        legal_principles = []
        for section in relevant_sections:
            legal_principles.extend(section.get("key_principles") or section.get("principles") or [])

        return {
            "relevant_sections": relevant_sections,
            "applicable_precedents": applicable_precedents,
            "legal_principles": legal_principles,
        }

    def save_knowledge_base(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with (self.data_dir / "precedents.json").open("w", encoding="utf-8") as handle:
            json.dump(self.precedents, handle, indent=4)
        with (self.data_dir / "legal_principles.json").open("w", encoding="utf-8") as handle:
            json.dump({"principles": self.legal_principles}, handle, indent=4)


knowledge_base = KnowledgeBase()


def load_laws():
    knowledge_base.load_knowledge_base()


def get_legal_advice(case_facts: Dict[str, Any]) -> Dict[str, Any]:
    return knowledge_base.get_legal_advice(case_facts)


def get_section_text(act_name: str, section_number: Any) -> Optional[str]:
    return knowledge_base.get_section_text(act_name, section_number)
