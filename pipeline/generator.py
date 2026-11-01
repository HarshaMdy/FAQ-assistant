# pipeline/generator.py
"""
Phase 7.2: LLM Response Generator
Combines retrieved context chunks with user query under strict factual prompting.
Enforces:
  1. Maximum 3 sentences
  2. One official citation link
  3. "Last updated from sources: <date>"
  4. Strict factual grounding with safe refusals
"""

import sys
from pathlib import Path
from datetime import datetime

# Resolve project paths
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from llm.base import get_llm_client

SYSTEM_PROMPT = """You are a facts-only mutual fund FAQ assistant for HDFC mutual fund schemes on Groww.

STRICT INSTRUCTIONS:
1. Answer using the provided Context facts and official scheme details. State the specific fact clearly and directly (e.g. Expense Ratio, Exit Load, Minimum SIP, Benchmark index, ELSS 3-year statutory lock-in).
2. Keep your answer concise: 1 to 2 sentences.
3. NEVER provide investment advice, buy/sell recommendations, or portfolio opinions.
4. NEVER compute, project, or compare fund returns.
5. If the context and official scheme facts genuinely do not contain the answer, respond: "I could not find this specific fact in the official Groww scheme documentation."
"""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Format retrieved context chunks and user question."""
    context_blocks = []
    for idx, c in enumerate(chunks, 1):
        context_blocks.append(
            f"[Context {idx}] (Source: {c['source_url']})\n{c['chunk_text']}"
        )
    context_text = "\n\n".join(context_blocks)
    return f"Context:\n{context_text}\n\nQuestion: {query}"


def generate(query: str, chunks: list[dict]) -> dict:
    """
    Generate grounded response using LLM client.

    Returns:
        {
            "answer": str,
            "source_url": str,
            "last_updated": str,
        }
    """
    if not chunks:
        return {
            "answer": "I could not find relevant information in the available official sources.",
            "source_url": "https://groww.in/mutual-funds/amc/hdfc-mutual-funds",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
        }

    prompt = build_prompt(query, chunks)
    llm = get_llm_client()
    raw_answer = llm.chat(system=SYSTEM_PROMPT, message=prompt)

    # Resolve primary citation source URL (from highest scoring chunk)
    primary_source = chunks[0].get("source_url", "")
    scraped_dates = [c.get("scraped_at", "")[:10] for c in chunks if c.get("scraped_at")]
    last_updated = max(scraped_dates) if scraped_dates else datetime.now().strftime("%Y-%m-%d")

    return {
        "answer": raw_answer.strip(),
        "source_url": primary_source,
        "last_updated": last_updated,
    }
