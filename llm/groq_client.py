# llm/groq_client.py
"""
Groq API Client (Primary LLM Provider)
Uses Groq API with specified model (e.g. qwen/qwen3-8b or llama-3.3-70b-versatile).
"""

import os
from llm.base import BaseLLMClient


class GroqClient(BaseLLMClient):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "qwen/qwen3-8b").strip()
        self.client = None

        if self.is_available():
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[GroqClient] Initialization error: {e}")

    def is_available(self) -> bool:
        """Check if a valid non-placeholder API key is set."""
        return bool(self.api_key and not self.api_key.startswith("your_"))

    def chat(self, system: str, message: str) -> str:
        if not self.client:
            raise RuntimeError("Groq client is not available. Please check GROQ_API_KEY in .env.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        return response.choices[0].message.content
