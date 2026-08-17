from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.plaintiff_agent import PlaintiffAgent
from agents.defendant_agent import DefendantAgent
from agents.judge_agent import JudgeAgent
from agents.witness_agent import WitnessAgent
from utils.helpers import format_evidence_label


class CourtroomSimulationManager:
    def __init__(self, case_data: Dict[str, Any]):
        self.case_data = case_data
        self.transcript: List[Dict[str, str]] = []
        self.current_phase = "opening"
        self.evidence_presented: List[Dict[str, Any]] = []
        self.selected_witness: Optional[Dict[str, Any]] = None
        self.current_speaker: Optional[str] = None
        self.similarity_reports: List[Dict[str, Any]] = []
        self.current_role = "Observer"

        self.plaintiff_agent = PlaintiffAgent()
        self.defendant_agent = DefendantAgent()
        self.judge_agent = JudgeAgent(case_data.get("judge_data"))
        self.witness_agent = WitnessAgent()

        if case_data.get("witnesses"):
            self.selected_witness = case_data["witnesses"][0]

    def add_to_transcript(self, speaker: str, content: str):
        self.transcript.append(
            {
                "speaker": speaker,
                "content": content,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        )

    def get_transcript(self) -> List[Dict[str, str]]:
        return self.transcript

    def get_current_phase(self) -> str:
        return self.current_phase

    def get_current_role(self) -> str:
        return self.current_role

    def set_current_phase(self, phase: str):
        self.current_phase = phase

    def set_current_role(self, role: str):
        self.current_role = role

    def get_agent(self, role: str):
        mapping = {
            "Plaintiff": self.plaintiff_agent,
            "Defendant": self.defendant_agent,
            "Judge": self.judge_agent,
            "Witness": self.witness_agent,
        }
        if role not in mapping:
            raise ValueError(f"Unknown role: {role}")
        return mapping[role]

    def process_user_input(self, role: str, input_text: str) -> str:
        agent = self.get_agent(role)
        context = {
            "phase": self.current_phase,
            "transcript": self.transcript,
            "evidence": self.evidence_presented,
            "witness": self.selected_witness,
            "case_data": self.case_data,
            "prompt": input_text,
        }
        return agent.generate_response(context)

    def add_evidence(self, evidence: Dict[str, Any]):
        self.evidence_presented.append(evidence)

    def set_witness(self, witness: Dict[str, Any]):
        self.selected_witness = witness

    def get_simulation_state(self) -> Dict[str, Any]:
        return {
            "transcript": self.transcript,
            "phase": self.current_phase,
            "evidence_presented": self.evidence_presented,
            "selected_witness": self.selected_witness,
            "current_speaker": self.current_speaker,
            "similarity_reports": self.similarity_reports,
        }

    def get_case_summary(self) -> Dict[str, Any]:
        return {
            "title": self.case_data.get("title", ""),
            "description": self.case_data.get("description", ""),
            "facts": self.case_data.get("facts", ""),
        }

    def first_witness(self) -> Dict[str, Any]:
        witnesses = self.case_data.get("witnesses") or []
        if witnesses:
            return witnesses[0]
        return {"name": "Witness", "role": "Fact witness", "testimony": ""}

    def record_user_turn(self, speaker: str, content: str, speaker_key: str):
        self.add_to_transcript(speaker, content)
        self.current_speaker = speaker_key
        return content

    def generate_opening(self, side: str) -> str:
        if side == "plaintiff":
            text = self.plaintiff_agent.generate_opening_statement(self.case_data)
            self.add_to_transcript("Plaintiff Lawyer", text)
            self.current_speaker = "plaintiff"
            return text
        text = self.defendant_agent.generate_opening_statement(self.case_data)
        self.add_to_transcript("Defendant Lawyer", text)
        self.current_speaker = "defendant"
        return text

    def generate_examination_question(self) -> str:
        witness = self.first_witness()
        question = self.plaintiff_agent.generate_question(witness)
        self.add_to_transcript("Plaintiff Lawyer", question)
        self.current_speaker = "plaintiff"
        return question

    def generate_cross_question(self) -> str:
        witness = self.first_witness()
        question = self.defendant_agent.generate_question(witness)
        self.add_to_transcript("Defendant Lawyer", question)
        self.current_speaker = "defendant"
        return question

    def generate_witness_answer(self, question: str) -> str:
        witness = self.first_witness()
        self.witness_agent.set_background(witness.get("role") or witness.get("name", "Witness"))
        self.witness_agent.set_testimony(witness.get("testimony") or witness.get("statement", ""))
        answer = self.witness_agent.give_testimony(question, self.case_data)
        self.add_to_transcript("Witness", answer)
        self.current_speaker = "witness"
        return answer

    def present_case_evidence(self, side: str, index: int) -> Optional[str]:
        evidence_list = self.case_data.get("evidence") or []
        if index >= len(evidence_list):
            return None
        item = evidence_list[index]
        label = format_evidence_label(item)
        speaker = "Plaintiff Lawyer" if side == "plaintiff" else "Defendant Lawyer"
        text = f"Your Honour, I present {label}."
        self.add_to_transcript(speaker, text)
        self.add_evidence({"side": side, "item": item, "label": label})
        self.current_speaker = side
        return text

    def present_uploaded_evidence(self, side: str, name: str, description: str, report: Optional[Dict[str, Any]] = None) -> str:
        speaker = "Plaintiff Lawyer" if side == "plaintiff" else "Defendant Lawyer"
        score = (report or {}).get("overall_score")
        score_note = f" Similarity to the case context is {score:.0%}." if isinstance(score, (int, float)) else ""
        text = f"Your Honour, I tender {name}. {description}{score_note}".strip()
        self.add_to_transcript(speaker, text)
        payload = {"side": side, "item": {"description": name, "content": description}, "label": name, "similarity": report}
        self.add_evidence(payload)
        if report:
            self.similarity_reports.append(report)
        self.current_speaker = side
        return text

    def generate_objection(self) -> str:
        last = self.transcript[-1]["content"] if self.transcript else "the previous question"
        objection = self.defendant_agent.generate_response(
            {"prompt": f"Raise a concise courtroom objection to this: {last}"}
        )
        self.add_to_transcript("Defendant Lawyer", objection)
        self.current_speaker = "defendant"
        return objection

    def generate_ruling(self, objection: str) -> str:
        ruling = self.judge_agent.rule_on_objection(objection)
        self.add_to_transcript("Judge", ruling)
        self.current_speaker = "judge"
        return ruling

    def generate_closing(self, side: str) -> str:
        if side == "plaintiff":
            text = self.plaintiff_agent.generate_closing_argument(self.case_data)
            self.add_to_transcript("Plaintiff Lawyer", text)
            self.current_speaker = "plaintiff"
            return text
        text = self.defendant_agent.generate_closing_argument(self.case_data)
        self.add_to_transcript("Defendant Lawyer", text)
        self.current_speaker = "defendant"
        return text

    def generate_judgment(self) -> str:
        summary_parts = [
            str(self.case_data),
            "Transcript:",
        ]
        for entry in self.transcript[-20:]:
            summary_parts.append(f"{entry['speaker']}: {entry['content']}")
        if self.similarity_reports:
            summary_parts.append("Evidence similarity notes:")
            for report in self.similarity_reports[-5:]:
                summary_parts.append(
                    f"{report.get('evidence_name')}: {report.get('label')} ({report.get('overall_score')})"
                )
        judgment = self.judge_agent.give_judgment("\n".join(summary_parts))
        self.add_to_transcript("Judge", judgment)
        self.current_speaker = "judge"
        return judgment

    def transcript_text(self) -> str:
        lines = []
        for entry in self.transcript:
            stamp = entry.get("timestamp", "")
            lines.append(f"[{stamp}] {entry['speaker']}: {entry['content']}")
        return "\n".join(lines)


def create_simulation(case_data: Dict[str, Any]) -> CourtroomSimulationManager:
    return CourtroomSimulationManager(case_data)
