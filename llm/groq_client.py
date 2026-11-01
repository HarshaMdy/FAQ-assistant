# llm/groq_client.py
"""
Groq API Client (Primary LLM Provider)
Uses Groq API with specified model (e.g. qwen/qwen3.8-27b or llama-3.3-70b-versatile).
Includes native urllib.request fallback for zero-dependency serverless environments (Vercel).
"""

import os
import json
import urllib.request
import urllib.error
from llm.base import BaseLLMClient


class GroqClient(BaseLLMClient):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
        self.client = None

        if self.is_available():
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception:
                # Standard library HTTP fallback will be used
                self.client = None

    def is_available(self) -> bool:
        """Check if a valid non-placeholder API key is set."""
        return bool(self.api_key and not self.api_key.startswith("your_"))

    def chat(self, system: str, message: str) -> str:
        if not self.is_available():
            raise RuntimeError("Groq client is not available. Please check GROQ_API_KEY.")

        # 1. Try official groq SDK if installed
        if self.client:
            try:
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
            except Exception:
                pass

        # 2. Resilient stdlib urllib.request fallback (Zero external dependencies)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "HDFC-FAQ-Assistant/1.0",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            "temperature": 0.1,
            "max_tokens": 300,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"Groq API HTTP {e.code}: {err_body}")
        except Exception as e:
            raise RuntimeError(f"Groq API connection error: {str(e)}")
