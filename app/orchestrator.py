# app/orchestrator.py
"""
RAG Application Orchestrator
Coordinates the end-to-end question answering pipeline:
1. Guardrail filter check (PII, advice, returns refusal)
2. Vector retrieval from persistent ChromaDB store
3. Grounded LLM response generation with citation link
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.guard import guard
from pipeline.retriever import retrieve
from pipeline.generator import generate


def ask(query: str) -> dict:
    """
    Main entry point for answering user queries.

    Args:
        query: Raw user question string.

    Returns:
        dict: {
            "status": "answered" | "refused",
            "answer": str,
            "source_url": str,
            "last_updated": str,
            "refusal_reason": str (optional)
        }
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return {
            "status": "refused",
            "answer": "Please ask a factual question about HDFC mutual fund schemes.",
            "source_url": "",
            "last_updated": "",
        }

    # Step 1: Guardrails check
    guard_eval = guard(cleaned_query)
    if guard_eval["action"] == "refuse":
        return {
            "status": "refused",
            "answer": guard_eval["message"],
            "source_url": "",
            "last_updated": "",
            "refusal_reason": guard_eval.get("reason", ""),
        }

    # Step 2: Retrieve relevant context chunks
    chunks = retrieve(cleaned_query, top_k=8)

    if not chunks:
        return {
            "status": "answered",
            "answer": "I could not find matching information in the official Groww pages.",
            "source_url": "https://groww.in/mutual-funds/amc/hdfc-mutual-funds",
            "last_updated": "",
        }

    # Step 3: LLM generation
    gen_result = generate(cleaned_query, chunks)

    return {
        "status": "answered",
        "answer": gen_result["answer"],
        "source_url": gen_result["source_url"],
        "last_updated": gen_result["last_updated"],
    }
