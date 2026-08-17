from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib

class EvidenceManager:
    def __init__(self):
        self.evidence_types = {
            "Documentary": {
                "description": "Written or printed documents",
                "authentication_required": True,
                "admissibility_criteria": ["Original", "Certified Copy", "Secondary Evidence"]
            },
            "Electronic": {
                "description": "Digital evidence including emails, messages, and digital files",
                "authentication_required": True,
                "admissibility_criteria": ["Hash Verification", "Chain of Custody", "Metadata"]
            },
            "Expert": {
                "description": "Opinions from qualified experts",
                "authentication_required": True,
                "admissibility_criteria": ["Qualifications", "Methodology", "Reliability"]
            },
            "Photographic": {
                "description": "Photographs and images",
                "authentication_required": True,
                "admissibility_criteria": ["Authenticity", "Relevance", "Chain of Custody"]
            },
            "Audio-Visual": {
                "description": "Audio and video recordings",
                "authentication_required": True,
                "admissibility_criteria": ["Authenticity", "Chain of Custody", "Clarity"]
            },
            "Forensic": {
                "description": "Scientific analysis and testing",
                "authentication_required": True,
                "admissibility_criteria": ["Scientific Validity", "Chain of Custody", "Expert Testimony"]
            },
            "Medical": {
                "description": "Medical reports and records",
                "authentication_required": True,
                "admissibility_criteria": ["Certification", "Relevance", "Completeness"]
            },
            "Financial": {
                "description": "Financial records and statements",
                "authentication_required": True,
                "admissibility_criteria": ["Authentication", "Completeness", "Relevance"]
            },
            "Property": {
                "description": "Property-related documents",
                "authentication_required": True,
                "admissibility_criteria": ["Registration", "Chain of Title", "Authenticity"]
            },
            "Witness": {
                "description": "Witness statements and testimonies",
                "authentication_required": False,
                "admissibility_criteria": ["Credibility", "Relevance", "Consistency"]
            }
        }
        
        self.evidence_log: Dict[str, List[Dict[str, Any]]] = {}
        self.chain_of_custody: Dict[str, List[Dict[str, Any]]] = {}
        self.authentication_records: Dict[str, Dict[str, Any]] = {}

    def register_evidence(self, case_id: str, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register new evidence for a case"""
        if case_id not in self.evidence_log:
            self.evidence_log[case_id] = []
            self.chain_of_custody[case_id] = []
            self.authentication_records[case_id] = {}
        
        evidence_id = f"EVID-{case_id}-{len(self.evidence_log[case_id]) + 1}"
        
        evidence = {
            "evidence_id": evidence_id,
            "type": evidence_data["type"],
            "description": evidence_data["description"],
            "submitted_by": evidence_data["submitted_by"],
            "submission_date": datetime.now().isoformat(),
            "status": "pending_authentication",
            "metadata": self._generate_metadata(evidence_data)
        }
        
        self.evidence_log[case_id].append(evidence)
        self._update_chain_of_custody(case_id, evidence_id, "registration", evidence_data["submitted_by"])
        
        return evidence

    def authenticate_evidence(self, case_id: str, evidence_id: str, authentication_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate registered evidence"""
        evidence = self._get_evidence(case_id, evidence_id)
        if not evidence:
            raise ValueError("Evidence not found")
        
        evidence_type = evidence["type"]
        auth_criteria = self.evidence_types[evidence_type]["admissibility_criteria"]
        
        authentication_result = {
            "authenticated": True,
            "criteria_met": [],
            "criteria_failed": [],
            "notes": []
        }
        
        for criterion in auth_criteria:
            if criterion in authentication_data and authentication_data[criterion]:
                authentication_result["criteria_met"].append(criterion)
            else:
                authentication_result["criteria_failed"].append(criterion)
                authentication_result["authenticated"] = False
        
        if authentication_result["authenticated"]:
            evidence["status"] = "authenticated"
            self._update_chain_of_custody(case_id, evidence_id, "authentication", authentication_data["authenticated_by"])
        
        self.authentication_records[case_id][evidence_id] = authentication_result
        return authentication_result

    def verify_admissibility(self, case_id: str, evidence_id: str) -> Dict[str, Any]:
        """Verify if evidence is admissible in court"""
        evidence = self._get_evidence(case_id, evidence_id)
        if not evidence:
            raise ValueError("Evidence not found")
        
        auth_record = self.authentication_records[case_id].get(evidence_id, {})
        if not auth_record.get("authenticated", False):
            return {
                "admissible": False,
                "reason": "Evidence not authenticated"
            }
        
        evidence_type = evidence["type"]
        admissibility_criteria = self.evidence_types[evidence_type]["admissibility_criteria"]
        
        admissibility_result = {
            "admissible": True,
            "criteria_met": auth_record["criteria_met"],
            "criteria_failed": auth_record["criteria_failed"],
            "notes": auth_record["notes"]
        }
        
        if len(admissibility_result["criteria_failed"]) > 0:
            admissibility_result["admissible"] = False
        
        return admissibility_result

    def get_evidence_chain_of_custody(self, case_id: str, evidence_id: str) -> List[Dict[str, Any]]:
        """Get chain of custody for specific evidence"""
        return self.chain_of_custody.get(case_id, {}).get(evidence_id, [])

    def update_evidence_status(self, case_id: str, evidence_id: str, status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Update evidence status"""
        evidence = self._get_evidence(case_id, evidence_id)
        if not evidence:
            raise ValueError("Evidence not found")
        
        evidence["status"] = status
        if notes:
            evidence["notes"] = notes
        
        self._update_chain_of_custody(case_id, evidence_id, "status_update", f"Status changed to {status}")
        return evidence

    def generate_evidence_report(self, case_id: str) -> Dict[str, Any]:
        """Generate comprehensive evidence report for a case"""
        if case_id not in self.evidence_log:
            raise ValueError("Case not found")
        
        report = {
            "case_id": case_id,
            "total_evidence": len(self.evidence_log[case_id]),
            "evidence_by_type": {},
            "authentication_status": {},
            "admissibility_status": {},
            "chain_of_custody_summary": {}
        }
        
        for evidence in self.evidence_log[case_id]:
            evidence_type = evidence["type"]
            
            # Count by type
            report["evidence_by_type"][evidence_type] = report["evidence_by_type"].get(evidence_type, 0) + 1
            
            # Authentication status
            auth_status = self.authentication_records[case_id].get(evidence["evidence_id"], {}).get("authenticated", False)
            report["authentication_status"][evidence["evidence_id"]] = auth_status
            
            # Admissibility status
            admissibility = self.verify_admissibility(case_id, evidence["evidence_id"])
            report["admissibility_status"][evidence["evidence_id"]] = admissibility["admissible"]
            
            # Chain of custody summary
            report["chain_of_custody_summary"][evidence["evidence_id"]] = len(
                self.chain_of_custody[case_id].get(evidence["evidence_id"], [])
            )
        
        return report

    def _generate_metadata(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for evidence"""
        metadata = {
            "hash": hashlib.sha256(str(evidence_data).encode()).hexdigest(),
            "timestamp": datetime.now().isoformat(),
            "size": len(str(evidence_data)),
            "format": evidence_data.get("format", "unknown")
        }
        
        if "file_path" in evidence_data:
            metadata["file_path"] = evidence_data["file_path"]
        
        return metadata

    def _update_chain_of_custody(self, case_id: str, evidence_id: str, action: str, actor: str) -> None:
        """Update chain of custody for evidence"""
        if case_id not in self.chain_of_custody:
            self.chain_of_custody[case_id] = {}
        
        if evidence_id not in self.chain_of_custody[case_id]:
            self.chain_of_custody[case_id][evidence_id] = []
        
        self.chain_of_custody[case_id][evidence_id].append({
            "action": action,
            "actor": actor,
            "timestamp": datetime.now().isoformat()
        })

    def _get_evidence(self, case_id: str, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Get evidence by ID"""
        if case_id not in self.evidence_log:
            return None
        
        for evidence in self.evidence_log[case_id]:
            if evidence["evidence_id"] == evidence_id:
                return evidence
        
        return None

    def save_evidence_data(self, case_id: str, filename: str) -> None:
        """Save evidence data to file"""
        if case_id not in self.evidence_log:
            raise ValueError("Case not found")
        
        data = {
            "evidence_log": self.evidence_log[case_id],
            "chain_of_custody": self.chain_of_custody[case_id],
            "authentication_records": self.authentication_records[case_id]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_evidence_data(self, case_id: str, filename: str) -> None:
        """Load evidence data from file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.evidence_log[case_id] = data["evidence_log"]
        self.chain_of_custody[case_id] = data["chain_of_custody"]
        self.authentication_records[case_id] = data["authentication_records"]

    def assess_context_similarity(self, evidence_text: str, case_data: Dict[str, Any], evidence_name: str = "Exhibit") -> Dict[str, Any]:
        """Score uploaded evidence against case context and the legal knowledge base."""
        from rag.pipeline import LegalRAGPipeline

        pipeline = LegalRAGPipeline()
        report = pipeline.score_evidence(evidence_text, case=case_data, evidence_name=evidence_name)
        return report.to_dict() 