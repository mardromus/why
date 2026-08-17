# llm/groq_api.py

from typing import Any, Dict, List, Union

from config import get_groq_api_key, groq_model

MessageInput = Union[str, List[Dict[str, str]]]


class GroqAPI:
    def __init__(self):
        self._client = None
        self._init_error = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        api_key = get_groq_api_key()
        if not api_key:
            self._init_error = (
                "GROQ_API_KEY is not set. Add it to Streamlit secrets, a .env file, or api_keys.py."
            )
            return None
        try:
            from groq import Groq

            self._client = Groq(api_key=api_key, timeout=20.0)
            self._init_error = None
            return self._client
        except Exception as exc:
            self._init_error = str(exc)
            return None

    def generate_response(
        self,
        prompt: MessageInput,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        client = self._get_client()
        if client is None:
            return {"error": self._init_error or "Groq client unavailable", "response": None}

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a legal expert assistant for an Indian civil courtroom simulation. "
                        "Stay in role, be concise, and do not invent exhibits or statutes that were not provided."
                    ),
                },
                {"role": "user", "content": str(prompt)},
            ]

        try:
            completion = client.chat.completions.create(
                model=model or groq_model(),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False,
            )
            content = completion.choices[0].message.content if completion.choices else ""
            return {
                "response": content,
                "model": model or groq_model(),
                "usage": getattr(completion, "usage", None),
            }
        except Exception as exc:
            print(f"Error in Groq API call: {exc}")
            return {"error": str(exc), "response": None}

    def is_configured(self) -> bool:
        return bool(get_groq_api_key())


groq_api = GroqAPI()

if __name__ == "__main__":
    result = groq_api.generate_response("What is the role of a judge in an Indian civil court?")
    print(result)
