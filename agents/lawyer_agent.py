# agents/lawyer_agent.py

from typing import Dict, Any, List
from .agent_base import AgentBase

class LawyerAgent(AgentBase):
    def __init__(self, config: Dict[str, Any] = None, llm_provider: str = "Groq"):
        super().__init__("lawyer", llm_provider)
        self.config = config or {
            "name": "Advocate",
            "experience": "10 years",
            "specialization": "Civil Law",
        }
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the lawyer"""
        return f"""You are {self.config['name']}, {self.config['experience']} of experience in {self.config['specialization']}.
        You are representing a client in court. Your role is to:
        1. Present arguments effectively
        2. Examine witnesses
        3. Present evidence
        4. Raise objections when necessary
        5. Protect your client's interests
        
        Respond professionally and maintain courtroom decorum."""
        
    def prepare_examination_questions(self, witness_id: str) -> List[str]:
        """Prepare questions for witness examination"""
        prompt = f"""Prepare a series of questions to examine witness {witness_id}.
        The questions should:
        1. Be clear and specific
        2. Establish facts
        3. Support your case
        4. Avoid leading questions
        5. Be legally appropriate
        
        Return the questions as a numbered list."""
        response = self.generate_response(prompt)
        return [q.strip() for q in response.split('\n') if q.strip()]
        
    def raise_objection(self, context: str) -> str:
        """Raise an objection during proceedings"""
        prompt = f"""In the following context:
        {context}
        
        Raise an appropriate objection with legal basis."""
        return self.generate_response(prompt)
        
    def present_argument(self, topic: str) -> str:
        """Present legal arguments"""
        prompt = f"""Present arguments on the following topic:
        {topic}
        
        Include:
        1. Legal principles
        2. Relevant precedents
        3. Application to the case
        4. Conclusion
        
        Keep it concise and persuasive."""
        return self.generate_response(prompt)
