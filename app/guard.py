# app/guard.py
"""
Guardrails Filter Module
Applies strict, ordered evaluation rules to every user query before it reaches the RAG pipeline:
1. PII check (PAN, Aadhaar, phone numbers, emails, OTPs)
2. Investment Advice check (recommendations, buy/sell, portfolio advice)
3. Performance / Returns computation check
"""

import re

# Refusal Messages (with mandated official / educational links)
MSG_PII = (
    "I cannot process queries containing personal information "
    "(PAN, Aadhaar, phone, email, OTP). Please ask a factual question about HDFC mutual funds."
)

MSG_ADVICE = (
    "I provide facts only and cannot offer investment advice or recommendations. "
    "For financial planning, please consult a SEBI-registered investment advisor.\n\n"
    "Educational resources: https://www.amfiindia.com/investor-corner/knowledge-center"
)

MSG_RETURNS = (
    "I cannot compute or compare fund returns or performance figures. "
    "For historical performance, please refer to the official fund factsheet:\n\n"
    "Official factsheet: https://www.hdfcfund.com/our-products/equity-funds"
)

# Regex Patterns
PII_PATTERNS = [
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",                               # Indian PAN format (case-sensitive uppercase)
    r"\b[2-9][0-9]{11}\b",                                        # 12-digit Aadhaar
    r"\b[6-9]\d{9}\b",                                            # 10-digit Indian Mobile
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",      # Email
    r"\botp\b",                                                   # OTP mention
]

ADVICE_KEYWORDS = [
    "should i", "recommend", "better than", "which is better",
    "should i buy", "should i sell", "should i invest",
    "worth investing", "buy", "sell", "invest in",
    "portfolio", "best fund", "good fund", "which fund should",
]

RETURNS_KEYWORDS = [
    "returns", "cagr", "performance", "annualised", "annualized",
    "historical return", "past return", "how much return", "xirr",
    "compare returns",
]


def guard(query: str) -> dict:
    """
    Evaluate user query against rejection guardrails.

    Returns:
        {"action": "answer"} -> Passed all guardrails.
        {"action": "refuse", "message": str, "reason": str} -> Refused.
    """
    if not query:
        return {"action": "answer"}

    q_lower = query.lower()

    # Rule 1: PII Detection
    for pattern in PII_PATTERNS:
        if re.search(pattern, query):  # check on original query (preserves PAN case)
            return {
                "action": "refuse",
                "message": MSG_PII,
                "reason": "pii_detected",
            }

    # Rule 2: Investment Advice Detection
    for kw in ADVICE_KEYWORDS:
        if kw in q_lower:
            return {
                "action": "refuse",
                "message": MSG_ADVICE,
                "reason": "advice_refusal",
            }

    # Rule 3: Returns / Performance Detection
    for kw in RETURNS_KEYWORDS:
        if kw in q_lower:
            return {
                "action": "refuse",
                "message": MSG_RETURNS,
                "reason": "returns_refusal",
            }

    return {"action": "answer"}
