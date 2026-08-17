"""Shared helpers for cases, evidence, and session state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import DATA_DIR, DEFAULT_DEFENDANT_LAWYER, DEFAULT_JUDGE, DEFAULT_PLAINTIFF_LAWYER
from rag.pipeline import evidence_to_text


def load_cases() -> List[Dict[str, Any]]:
    path = DATA_DIR / "cases.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("cases", data if isinstance(data, list) else [])


def get_case_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    for case in load_cases():
        if case.get("case_id") == case_id:
            return case
    return None


def build_simulation_case(case: Dict[str, Any]) -> Dict[str, Any]:
    parties = case.get("parties") or {}
    return {
        "case_id": case.get("case_id", "custom"),
        "title": case.get("title", "Untitled case"),
        "type": case.get("case_type") or case.get("type", "Civil"),
        "case_type": case.get("case_type") or case.get("type", "Civil"),
        "plaintiff": parties.get("plaintiff") or case.get("plaintiff", "Plaintiff"),
        "defendant": parties.get("defendant") or case.get("defendant", "Defendant"),
        "parties": {
            "plaintiff": parties.get("plaintiff") or case.get("plaintiff", "Plaintiff"),
            "defendant": parties.get("defendant") or case.get("defendant", "Defendant"),
        },
        "description": case.get("description", ""),
        "facts": case.get("facts") or case.get("description", ""),
        "judge_data": case.get("judge_data") or DEFAULT_JUDGE,
        "plaintiff_lawyer_data": case.get("plaintiff_lawyer_data") or DEFAULT_PLAINTIFF_LAWYER,
        "defendant_lawyer_data": case.get("defendant_lawyer_data") or DEFAULT_DEFENDANT_LAWYER,
        "witnesses": case.get("witnesses") or [],
        "evidence": case.get("evidence") or [],
    }


def format_evidence_label(item: Any) -> str:
    text = evidence_to_text(item)
    return text or "Untitled exhibit"


def phase_label(phase: str) -> str:
    return (phase or "").replace("_", " ").title()
