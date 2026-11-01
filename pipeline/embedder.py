# pipeline/embedder.py
"""
Phase 5: Data Embedding & ChromaDB Storage
Loads chunk files from data/chunks/*.json.
Encodes chunk texts using sentence-transformers/all-MiniLM-L6-v2 (384-dimensional).
Persists vectors and rich metadata into a local ChromaDB collection.
"""

import json
import os
import sys
import yaml
from pathlib import Path

# Resolve base path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

CONFIG_PATH = BASE_DIR / "config.yaml"
CHUNK_DIR = BASE_DIR / "data" / "chunks"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

MODEL_NAME = CONFIG.get("embedding", {}).get("model", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_DIR = str(BASE_DIR / CONFIG.get("vector_db", {}).get("persist_directory", "./chroma_store"))
COLLECTION_NAME = CONFIG.get("vector_db", {}).get("collection_name", "hdfc_mf_faq")


def run_embedder():
    """Embed all chunks and upsert into ChromaDB."""
    from sentence_transformers import SentenceTransformer
    import chromadb

    print(f"\n=======================================================")
    print(f" Phase 5: Data Embedding & Vector DB Storage")
    print(f" Embedding Model: {MODEL_NAME}")
    print(f" Vector DB: ChromaDB (persistent)")
    print(f" Storage Path: {CHROMA_DIR}")
    print(f" Collection: {COLLECTION_NAME}")
    print(f"=======================================================\n")

    print(f"[Embedder] Loading SentenceTransformer: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"[Embedder] [OK] Model loaded successfully.")

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    chunk_files = sorted(CHUNK_DIR.glob("*_chunks.json"))
    if not chunk_files:
        raise FileNotFoundError(f"No chunk files found in {CHUNK_DIR}. Run pipeline/chunker.py first.")

    total_chunks = 0
    batch_size = 64

    for chunk_file in chunk_files:
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        print(f"\n[Embedder] Processing {chunk_file.name} ({len(chunks)} chunks)...")

        # Process in batches for efficiency
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c["chunk_text"] for c in batch]
            ids = [c["chunk_id"] for c in batch]

            # Generate dense embeddings (384-dimensional)
            embeddings = model.encode(texts, convert_to_numpy=True).tolist()

            metadatas = [
                {
                    "source_url": c.get("source_url", ""),
                    "fund_slug": c.get("fund_slug", ""),
                    "scraped_at": c.get("scraped_at", ""),
                    "chunk_type": c.get("chunk_type", ""),
                    "metric_key": c.get("metric_key", ""),
                }
                for c in batch
            ]

            # Batch upsert to ChromaDB
            collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )

        total_chunks += len(chunks)
        print(f"  [OK] Upserted {len(chunks)} chunks from {chunk_file.name}")

    count = collection.count()
    print(f"\n[Embedder] Completed. Total items in collection '{COLLECTION_NAME}': {count}\n")
    return count


if __name__ == "__main__":
    run_embedder()
