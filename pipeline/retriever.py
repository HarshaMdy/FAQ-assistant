# pipeline/retriever.py
"""
Phase 7: Vector & Semantic Retrieval Module
Encodes user queries using dense vector similarity against ChromaDB,
with an ultra-fast in-memory fallback loader for serverless environments (Vercel)
where ChromaDB storage or PyTorch weights may not be locally persisted.
"""

import os
import re
import sys
import json
import yaml
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

CONFIG_PATH = BASE_DIR / "config.yaml"

CONFIG = {}
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            CONFIG = yaml.safe_load(f) or {}
    except Exception:
        CONFIG = {}

MODEL_NAME = CONFIG.get("embedding", {}).get("model", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_DIR = str(BASE_DIR / CONFIG.get("vector_db", {}).get("persist_directory", "./chroma_store"))
COLLECTION_NAME = CONFIG.get("vector_db", {}).get("collection_name", "hdfc_mf_faq")
DEFAULT_TOP_K = CONFIG.get("vector_db", {}).get("top_k", 8)

# Module-level singletons
_model = None
_collection = None
_DISK_CHUNKS_CACHE = None


def load_all_disk_chunks() -> list[dict]:
    """Loads all chunk JSON files from data/chunks/ into memory."""
    global _DISK_CHUNKS_CACHE
    if _DISK_CHUNKS_CACHE is not None:
        return _DISK_CHUNKS_CACHE

    chunks = []
    chunks_dir = BASE_DIR / "data" / "chunks"
    if chunks_dir.exists():
        for json_file in chunks_dir.glob("*_chunks.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        chunks.extend(data)
            except Exception:
                continue

    _DISK_CHUNKS_CACHE = chunks
    return _DISK_CHUNKS_CACHE


def fallback_chunk_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    fund_slug: str = None,
    chunk_type: str = None,
) -> list[dict]:
    """
    Lightweight, deterministic BM25-style keyword search across disk chunks.
    Guarantees fast (<5ms) sub-second retrieval in serverless environments.
    """
    all_chunks = load_all_disk_chunks()
    if not all_chunks:
        return []

    q_clean = query.lower()
    q_tokens = set(re.findall(r"\w+", q_clean))

    scored = []
    for ch in all_chunks:
        if fund_slug and ch.get("fund_slug") != fund_slug:
            continue
        if chunk_type and ch.get("chunk_type") != chunk_type:
            continue

        text = ch.get("chunk_text", "").lower()
        metric_key = (ch.get("metric_key") or "").lower()
        ch_tokens = set(re.findall(r"\w+", text))

        score = 0.0

        # Exact metric key match boost
        if metric_key and metric_key in q_clean:
            score += 25.0

        # Token overlap
        overlap = len(q_tokens & ch_tokens)
        score += overlap * 2.0

        # Fund name matching boost
        fund_name = ch.get("fund_slug", "").replace("_", " ")
        for part in fund_name.split():
            if part in q_clean and part not in ("hdfc", "fund"):
                score += 5.0

        # Substring presence
        for token in q_tokens:
            if len(token) > 3 and token in text:
                score += 1.0

        if score > 0:
            scored.append((score, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_hits = scored[:top_k]

    results = []
    for score, ch in top_hits:
        results.append({
            "chunk_text": ch.get("chunk_text", ""),
            "source_url": ch.get("source_url", ""),
            "fund_slug": ch.get("fund_slug", ""),
            "chunk_type": ch.get("chunk_type", ""),
            "metric_key": ch.get("metric_key", ""),
            "scraped_at": ch.get("scraped_at", ""),
            "score": round(score, 4),
        })

    return results


def get_retriever():
    """Lazy loader for model and ChromaDB collection singleton."""
    global _model, _collection
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    if _collection is None:
        import chromadb
        if not os.path.exists(CHROMA_DIR):
            raise FileNotFoundError(f"Chroma directory not found: {CHROMA_DIR}")
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
    Encode query and perform vector similarity search with automatic fallback.
    """
    if not query or not query.strip():
        return []

    # Attempt dense vector retrieval via ChromaDB
    try:
        model, collection = get_retriever()
        query_vector = model.encode(query.strip(), convert_to_numpy=True).tolist()

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
                score = round(max(0.0, 1.0 - dist), 4)
                hits.append({
                    "chunk_text": doc,
                    "source_url": meta.get("source_url", ""),
                    "fund_slug": meta.get("fund_slug", ""),
                    "chunk_type": meta.get("chunk_type", ""),
                    "metric_key": meta.get("metric_key", ""),
                    "scraped_at": meta.get("scraped_at", ""),
                    "score": score,
                })
        if hits:
            return hits
    except Exception:
        # Fall back to high-speed disk chunk search (ideal for Vercel Serverless)
        pass

    return fallback_chunk_retrieve(query, top_k=top_k, fund_slug=fund_slug, chunk_type=chunk_type)
