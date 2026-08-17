# agents/agent_base.py

from llm import groq_api
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
from abc import ABC, abstractmethod

class AgentBase(ABC):
    def __init__(self, role: str, llm_provider: str = "Groq"):
        self.role = role
        self.llm_provider = llm_provider
    
    @abstractmethod
    def generate_response(self, context: Dict[str, Any]) -> str:
        """Generate a response based on the given context"""
        pass
    
    @abstractmethod
    def analyze_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the case and provide insights"""
        pass
    
    @abstractmethod
    def prepare_arguments(self, case_data: Dict[str, Any]) -> List[str]:
        """Prepare arguments for the case"""
        pass

class CourtAgent(AgentBase):
    def __init__(self, role: str, llm_provider: str = "Groq"):
        super().__init__(role, llm_provider)
        self.conversation_history: List[Dict[str, str]] = []
        self.state: Dict[str, Any] = {
            "active": True,
            "last_interaction": datetime.now(),
            "emotion": "neutral",
            "focus": "general"
        }
        self.knowledge_base: Dict[str, Any] = {
            "legal_principles": [],
            "procedural_rules": [],
            "case_precedents": [],
            "court_practices": []
        }
        self.performance_metrics: Dict[str, Any] = {
            "interactions": 0,
            "response_time": 0,
            "success_rate": 0,
            "objections": 0,
            "rulings": 0
        }

        self.llm = groq_api
        self.role_prompt = ""

    def set_prompt(self, prompt: str):
        self.role_prompt = prompt

    def generate_response(self, context: Dict[str, Any]) -> str:
        """Generate a response based on the given context"""
        self.performance_metrics["interactions"] += 1
        start_time = datetime.now()

        try:
            messages = [{"role": "system", "content": self.role_prompt}]
            
            # Add conversation history
            for msg in self.conversation_history[-5:]:  # Keep last 5 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add current prompt
            messages.append({"role": "user", "content": context["prompt"]})

            response = self.llm.generate_response(messages)
            if isinstance(response, dict):
                response = response.get("response") or response.get("error") or ""

            response_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["response_time"] = (
                self.performance_metrics["response_time"] * (self.performance_metrics["interactions"] - 1) +
                response_time
            ) / self.performance_metrics["interactions"]

            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })

            return response

        except Exception as e:
            self.performance_metrics["success_rate"] = (
                self.performance_metrics["success_rate"] * (self.performance_metrics["interactions"] - 1)
            ) / self.performance_metrics["interactions"]
            raise e

    def update_state(self, new_state: Dict[str, Any]) -> None:
        """Update the agent's state"""
        self.state.update(new_state)
        self.state["last_interaction"] = datetime.now()

    def update_knowledge(self, category: str, content: Any) -> None:
        """Update the agent's knowledge base"""
        if category in self.knowledge_base:
            self.knowledge_base[category].append(content)
        else:
            self.knowledge_base[category] = [content]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get the agent's performance metrics"""
        return {
            **self.performance_metrics,
            "average_response_time": self.performance_metrics["response_time"],
            "success_rate": self.performance_metrics["success_rate"]
        }

    def reset_state(self) -> None:
        """Reset the agent's state to initial values"""
        self.state = {
            "active": True,
            "last_interaction": datetime.now(),
            "emotion": "neutral",
            "focus": "general"
        }
        self.conversation_history = []

    def log_interaction(self, interaction_type: str, details: Dict[str, Any]) -> None:
        """Log an interaction for analysis"""
        self.conversation_history.append({
            "type": interaction_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def analyze_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the case and provide insights"""
        return {
            "total_interactions": len(self.conversation_history),
            "recent_activity": self.conversation_history[-5:] if self.conversation_history else [],
            "state": self.state,
            "performance": self.get_performance_metrics()
        }

    def handle_error(self, error: Exception) -> str:
        """Handle errors gracefully"""
        self.log_interaction("error", {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.now().isoformat()
        })
        
        return f"I apologize, but I encountered an error: {str(error)}. Please try again or rephrase your request."

    def validate_input(self, input_data: Any, expected_type: type) -> bool:
        """Validate input data"""
        if not isinstance(input_data, expected_type):
            self.log_interaction("validation_error", {
                "expected": expected_type.__name__,
                "received": type(input_data).__name__,
                "input": str(input_data)
            })
            return False
        return True

    def format_response(self, response: str, style: str = "professional") -> str:
        """Format the response according to specified style"""
        if style == "professional":
            return response.strip()
        elif style == "casual":
            return response.strip().replace("I", "I").replace("you", "you")
        else:
            return response.strip()

    def maintain_context(self, context: Dict[str, Any]) -> None:
        """Maintain conversation context"""
        self.state["context"] = context
        self.state["last_context_update"] = datetime.now()

    def get_context(self) -> Optional[Dict[str, Any]]:
        """Get current conversation context"""
        return self.state.get("context")

    def clear_context(self) -> None:
        """Clear conversation context"""
        if "context" in self.state:
            del self.state["context"]

    def prepare_arguments(self, case_data: Dict[str, Any]) -> List[str]:
        """Prepare arguments for the case"""
        # Implementation of prepare_arguments method
        pass
