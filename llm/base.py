# llm/base.py
"""
LLM Client Interface & Provider Factory
Supports Groq (primary, qwen/qwen3-8b), Gemini, OpenAI, Anthropic, Mistral,
and a local grounded fallback when API keys are not yet configured.
"""

import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
# Resolve project paths
BASE_DIR = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    # On serverless (Vercel), environment variables are provided directly via os.environ
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    def chat(self, system: str, message: str) -> str:
        """Send prompt to LLM and return reply as string."""
        pass


class GroundedFallbackClient(BaseLLMClient):
    """
    Deterministic rule-based extractor used when remote API keys are not supplied.
    Extracts relevant facts directly from retrieved context chunks.
    Ensures prototype demo works reliably out of the box.
    """
    def chat(self, system: str, message: str) -> str:
        # Extract question from prompt
        question_line = ""
        context_lines = []
        is_context = False

        for line in message.split("\n"):
            if line.startswith("Question:"):
                question_line = line.replace("Question:", "").strip()
            elif line.startswith("Context:"):
                is_context = True
            elif is_context:
                context_lines.append(line)

        # Look for the most relevant fact line in context
        q_words = set(w.lower() for w in question_line.split() if len(w) > 3)
        best_candidate = ""
        best_overlap = -1

        for line in context_lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("[Context"):
                continue
            overlap = sum(1 for w in q_words if w in line_str.lower())
            if overlap > best_overlap and ("|" in line_str or ":" in line_str):
                best_overlap = overlap
                best_candidate = line_str

        if best_candidate:
            clean_fact = best_candidate.replace("Scheme:", "").strip()
            return f"According to official Groww records: {clean_fact}."
        elif context_lines:
            for l in context_lines:
                if len(l.strip()) > 30:
                    return f"Based on the official scheme documentation: {l.strip()[:200]}."

        return "I could not find this specific fact in the official public pages."


def get_llm_client() -> BaseLLMClient:
    """Factory: Instantiates the configured LLM client from .env."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        from llm.groq_client import GroqClient
        client = GroqClient()
        if client.is_available():
            return client
        return GroundedFallbackClient()

    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key and not api_key.startswith("your_"):
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            class GeminiWrapper(BaseLLMClient):
                def chat(self, system: str, message: str) -> str:
                    res = model.generate_content(f"{system}\n\n{message}")
                    return res.text
            return GeminiWrapper()
        return GroundedFallbackClient()

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key and not api_key.startswith("your_"):
            from openai import OpenAI
            oa = OpenAI(api_key=api_key)
            class OpenAIWrapper(BaseLLMClient):
                def chat(self, system: str, message: str) -> str:
                    res = oa.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "system", "content": system}, {"role": "user", "content": message}],
                        max_tokens=300,
                        temperature=0.1,
                    )
                    return res.choices[0].message.content
            return OpenAIWrapper()
        return GroundedFallbackClient()

    # Default fallback
    return GroundedFallbackClient()
