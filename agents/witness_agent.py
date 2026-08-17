from typing import Dict, Any, List
from .agent_base import AgentBase
from llm.groq_api import groq_api

class WitnessAgent(AgentBase):
    def __init__(self, llm_provider: str = "Groq"):
        super().__init__("witness", llm_provider)
        self.testimony = ""
        self.background = ""
        self.credibility = 0.8  # Default credibility score
    
    def generate_opening_statement(self, case_data: Dict[str, Any]) -> str:
        prompt = f"""You are a witness in an Indian court. Briefly introduce yourself and your relevance to this case:\nCase Details: {case_data}\n"""
        result = groq_api.generate_response(prompt)
        return result.get("response", f"[LLM Error: {result.get('error', 'Unknown error')}] Opening statement could not be generated.")

    def generate_question(self, context: Dict[str, Any]) -> str:
        prompt = f"""You are a witness. What question would you expect to be asked in this context?\nContext: {context}\n"""
        result = groq_api.generate_response(prompt)
        return result.get("response", f"[LLM Error: {result.get('error', 'Unknown error')}] Question could not be generated.")

    def generate_closing_argument(self, case_data: Dict[str, Any]) -> str:
        prompt = f"""You are a witness. Summarize your testimony and its importance for this case:\nCase Details: {case_data}\n"""
        result = groq_api.generate_response(prompt)
        return result.get("response", f"[LLM Error: {result.get('error', 'Unknown error')}] Closing summary could not be generated.")

    def generate_response(self, context: Dict[str, Any]) -> str:
        prompt = f"You are a witness in court. Respond to this context: {context}"
        result = groq_api.generate_response(prompt)
        return result.get("response", f"[LLM Error: {result.get('error', 'Unknown error')}] Response could not be generated.")

    def give_testimony(self, question: str, case_data: Dict[str, Any]) -> str:
        prompt = f"""You are a witness in an Indian court. Answer the following question truthfully, based on your knowledge and the case details.\nQuestion: {question}\nCase Details: {case_data}\n"""
        result = groq_api.generate_response(prompt)
        return result.get("response", f"[LLM Error: {result.get('error', 'Unknown error')}] Testimony could not be generated.")
    
    def analyze_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the case from witness's perspective"""
        return {
            "testimony_consistency": self.analyze_testimony(),
            "credibility_score": self.credibility,
            "background_relevance": self._assess_background_relevance(case_data),
            "potential_challenges": self._identify_potential_challenges(case_data)
        }
    
    def prepare_arguments(self, case_data: Dict[str, Any]) -> List[str]:
        """Prepare arguments for the witness's testimony"""
        return [
            f"My testimony is consistent with my background as {self.background}",
            f"I have direct knowledge of the events in question",
            f"My credibility score of {self.credibility} indicates reliable testimony",
            f"My testimony aligns with the documented evidence"
        ]
    
    def set_testimony(self, testimony: str):
        """Set the witness's testimony"""
        self.testimony = testimony
    
    def set_background(self, background: str):
        """Set the witness's background information"""
        self.background = background
    
    def set_credibility(self, credibility: float):
        """Set the witness's credibility score (0.0 to 1.0)"""
        self.credibility = max(0.0, min(1.0, credibility))
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build a detailed prompt for the witness's response"""
        question = context.get("question", "")
        previous_exchange = context.get("previous_exchange", "")
        pressure_level = context.get("pressure_level", 0)
        
        return f"""As a witness in court, respond to this question:
        Question: {question}
        
        Your Background: {self.background}
        Your Testimony: {self.testimony}
        Credibility Level: {self.credibility}
        Pressure Level: {pressure_level}
        
        Previous Exchange: {previous_exchange}
        
        Guidelines for your response:
        1. Answer truthfully based on your knowledge
        2. Stay consistent with your testimony
        3. Be clear and concise
        4. If you don't know, say so
        5. If you need clarification, ask for it
        6. Maintain appropriate level of detail based on credibility
        7. Consider the pressure level in your response
        
        Generate a natural, witness-appropriate response."""
    
    def analyze_testimony(self) -> Dict[str, Any]:
        """Analyze the witness's testimony for consistency and credibility"""
        prompt = f"""Analyze this witness testimony:
        Testimony: {self.testimony}
        Background: {self.background}
        Credibility: {self.credibility}
        
        Provide an analysis of:
        1. Key points in the testimony
        2. Potential inconsistencies
        3. Areas of strength
        4. Areas of vulnerability
        5. Suggested improvements
        6. Credibility assessment
        
        Format the response as a structured analysis."""
        
        analysis = groq_api.generate_response(prompt)
        text = analysis.get("response", str(analysis)) if isinstance(analysis, dict) else str(analysis)
        return self._parse_analysis(text)
    
    def prepare_for_examination(self, case_context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare the witness for examination"""
        prompt = f"""Prepare this witness for examination:
        Case Context: {case_context}
        Testimony: {self.testimony}
        Background: {self.background}
        Credibility: {self.credibility}
        
        Generate preparation guidelines including:
        1. Key points to emphasize
        2. Potential questions to expect
        3. Areas to be cautious about
        4. Suggested responses to difficult questions
        5. Body language and demeanor recommendations
        6. Credibility enhancement strategies
        
        Format the response as preparation guidelines."""
        
        preparation = groq_api.generate_response(prompt)
        text = preparation.get("response", str(preparation)) if isinstance(preparation, dict) else str(preparation)
        return self._parse_preparation(text)

    def _parse_analysis(self, analysis: str) -> Dict[str, Any]:
        return {"raw_analysis": analysis or "", "credibility_score": self.credibility}

    def _parse_preparation(self, preparation: str) -> Dict[str, Any]:
        return {"guidelines": preparation or "", "background": self.background}
    
    def _assess_background_relevance(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how relevant the witness's background is to the case"""
        return {
            "relevance_score": 0.8,  # Default score
            "key_connections": [],
            "potential_biases": []
        }
    
    def _identify_potential_challenges(self, case_data: Dict[str, Any]) -> List[str]:
        """Identify potential challenges to the witness's testimony"""
        return [
            "Memory accuracy",
            "Perception reliability",
            "Potential biases",
            "Inconsistencies in testimony"
        ] 