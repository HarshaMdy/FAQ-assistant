# pipeline/retriever.py
"""
Phase 7: Vector Retrieval Module
Encodes user queries using the identical embedding model (sentence-transformers/all-MiniLM-L6-v2)
and performs nearest-neighbor semantic search against persistent ChromaDB vector storage.
Returns top-K relevant chunks with source URLs, similarity scores, and metadata.
"""

import os
import sys
import yaml
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

CONFIG_PATH = BASE_DIR / "config.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

MODEL_NAME = CONFIG.get("embedding", {}).get("model", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_DIR = str(BASE_DIR / CONFIG.get("vector_db", {}).get("persist_directory", "./chroma_store"))
COLLECTION_NAME = CONFIG.get("vector_db", {}).get("collection_name", "hdfc_mf_faq")
DEFAULT_TOP_K = CONFIG.get("vector_db", {}).get("top_k", 5)

# Module-level singletons (loaded once and kept hot in memory)
_model = None
_collection = None


def get_retriever():
    """Lazy loader for model and ChromaDB collection singleton."""
    global _model, _collection
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    if _collection is None:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _model, _collection


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    fund_slug: str = None,
    chunk_type: str = None,
) -> list[dict]:
    """
    Encode query and perform vector similarity search.

    Args:
        query: User question or fact lookup text.
        top_k: Number of chunks to retrieve (default: 5).
        fund_slug: Optional filter by scheme (e.g., 'hdfc_large_cap').
        chunk_type: Optional filter ('table_metric' or 'prose_window').

    Returns:
        List of dicts: [
            {
                "chunk_text": str,
                "source_url": str,
                "fund_slug": str,
                "chunk_type": str,
                "scraped_at": str,
                "score": float,  # Cosine similarity (1 - distance)
            }
        ]
    """
    if not query or not query.strip():
        return []

    model, collection = get_retriever()

    # Encode query with identical 384-dimensional model
    query_vector = model.encode(query.strip(), convert_to_numpy=True).tolist()

    # Optional metadata filter
    where_filter = {}
    if fund_slug and chunk_type:
        where_filter = {"$and": [{"fund_slug": fund_slug}, {"chunk_type": chunk_type}]}
    elif fund_slug:
        where_filter = {"fund_slug": fund_slug}
    elif chunk_type:
        where_filter = {"chunk_type": chunk_type}

    query_params = {
        "query_embeddings": [query_vector],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        query_params["where"] = where_filter

    results = collection.query(**query_params)

    hits = []
    if results and results.get("documents") and results["documents"][0]:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, distances):
            score = round(max(0.0, 1.0 - dist), 4)  # cosine similarity
            hits.append({
                "chunk_text": doc,
                "source_url": meta.get("source_url", ""),
                "fund_slug": meta.get("fund_slug", ""),
                "chunk_type": meta.get("chunk_type", ""),
                "metric_key": meta.get("metric_key", ""),
                "scraped_at": meta.get("scraped_at", ""),
                "score": score,
            })

    return hits


def test_retriever():
    """Smoke test retriever on key factual mutual fund queries."""
    test_queries = [
        "What is the expense ratio of HDFC Large Cap Fund?",
        "What is the lock-in period for HDFC ELSS Tax Saver Fund?",
        "What is the minimum SIP amount for HDFC Mid Cap?",
        "What is the exit load for HDFC Flexi Cap Fund?",
        "What is the benchmark index for HDFC Large Cap?",
        "How do I download statement or capital gains?",
    ]

    print(f"\n=======================================================")
    print(f" Phase 7: Testing Vector Retrieval Module")
    print(f" Model: {MODEL_NAME}")
    print(f" Collection: {COLLECTION_NAME}")
    print(f"=======================================================\n")

    for idx, q in enumerate(test_queries, 1):
        print(f"Query {idx}: \"{q}\"")
        hits = retrieve(q, top_k=3)
        if not hits:
            print("  [No hits found]")
        for h_idx, hit in enumerate(hits, 1):
            doc_preview = hit["chunk_text"].replace("\n", " ").replace("₹", "Rs. ")[:90]
            print(f"  [{h_idx}] Score: {hit['score']:.4f} | Fund: {hit['fund_slug']} | Type: {hit['chunk_type']}")
            try:
                print(f"      Text: {doc_preview}...")
            except UnicodeEncodeError:
                safe_text = doc_preview.encode("ascii", errors="replace").decode("ascii")
                print(f"      Text: {safe_text}...")
            print(f"      URL : {hit['source_url']}")
        print()


if __name__ == "__main__":
    test_retriever()
