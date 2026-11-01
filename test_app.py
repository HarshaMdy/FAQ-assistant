# test_app.py
"""
End-to-End Test for RAG Orchestrator & UI Pipeline
Runs sample queries across factual questions and guardrail refusals.
"""

from app.orchestrator import ask

TEST_QUERIES = [
    # 1. Factual question
    "What is the expense ratio of HDFC Large Cap Fund?",
    # 2. ELSS lock-in
    "What is the lock-in period for HDFC ELSS Tax Saver Fund?",
    # 3. Minimum SIP
    "What is the minimum SIP amount for HDFC Mid Cap Fund?",
    # 4. Exit load
    "What is the exit load for HDFC Flexi Cap Fund?",
    # 5. Benchmark
    "What is the benchmark index for HDFC Large Cap?",
    # 6. Advice refusal
    "Should I invest in HDFC Large Cap or Mid Cap?",
    # 7. Returns refusal
    "What are the 3-year returns and CAGR of HDFC ELSS?",
    # 8. PII refusal
    "My PAN is ABCDE1234F, what is my folio status?",
]


def run_tests():
    print("\n=======================================================")
    print(" Running End-to-End RAG Prototype Test")
    print("=======================================================\n")

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}] Question: \"{query}\"")
        res = ask(query)
        print(f"    Status     : {res['status'].upper()}")
        print(f"    Answer     : {res['answer']}")
        if res.get("source_url"):
            print(f"    Source URL : {res['source_url']}")
        if res.get("last_updated"):
            print(f"    Updated    : {res['last_updated']}")
        print()


if __name__ == "__main__":
    run_tests()
