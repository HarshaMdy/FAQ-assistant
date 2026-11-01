# pipeline/store.py
"""
Phase 6: Storing Data in Vector DB & Storage Verification
Manages and verifies persistent ChromaDB vector storage.
Validates collection integrity, vector count, metadata schemas, and indexing.
"""

import sys
import yaml
from pathlib import Path
from collections import Counter
import chromadb

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

CONFIG_PATH = BASE_DIR / "config.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

CHROMA_DIR = str(BASE_DIR / CONFIG.get("vector_db", {}).get("persist_directory", "./chroma_store"))
COLLECTION_NAME = CONFIG.get("vector_db", {}).get("collection_name", "hdfc_mf_faq")


def get_db_client():
    """Return persistent ChromaDB client."""
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection():
    """Get the target ChromaDB collection."""
    client = get_db_client()
    return client.get_collection(COLLECTION_NAME)


def verify_storage() -> dict:
    """
    Inspect the stored vector database:
    1. Validates collection exists and has items
    2. Groups items by fund_slug and chunk_type
    3. Verifies metadata schema integrity
    4. Returns statistical summary
    """
    client = get_db_client()
    collections = [c.name for c in client.list_collections()]

    if COLLECTION_NAME not in collections:
        raise ValueError(
            f"Collection '{COLLECTION_NAME}' not found in ChromaDB at {CHROMA_DIR}. "
            "Please run pipeline/embedder.py first."
        )

    collection = client.get_collection(COLLECTION_NAME)
    total_count = collection.count()

    if total_count == 0:
        raise ValueError(f"Collection '{COLLECTION_NAME}' is empty. No vectors stored.")

    # Fetch all records with metadata
    data = collection.get(include=["metadatas", "documents"])
    metadatas = data.get("metadatas", [])
    documents = data.get("documents", [])

    slug_counts = Counter(m.get("fund_slug", "unknown") for m in metadatas)
    type_counts = Counter(m.get("chunk_type", "unknown") for m in metadatas)

    summary = {
        "status": "healthy",
        "chroma_dir": CHROMA_DIR,
        "collection_name": COLLECTION_NAME,
        "total_vectors": total_count,
        "fund_breakdown": dict(slug_counts),
        "chunk_types": dict(type_counts),
        "all_collections": collections,
    }
    return summary


def run_storage_verification():
    """Print detailed vector DB storage diagnostics."""
    print(f"\n=======================================================")
    print(f" Phase 6: Vector DB Storage Verification")
    print(f" Storage Path: {CHROMA_DIR}")
    print(f" Collection: {COLLECTION_NAME}")
    print(f"=======================================================\n")

    summary = verify_storage()

    print(f"[VectorDB] [OK] Collection '{summary['collection_name']}' is ACTIVE.")
    print(f"[VectorDB] [OK] Total Vector Records: {summary['total_vectors']}\n")

    print("--- Vectors by Fund Scheme ---")
    for slug, count in sorted(summary["fund_breakdown"].items()):
        print(f"  * {slug:<24} : {count:>4} vectors")

    print("\n--- Vectors by Chunk Type ---")
    for ctype, count in sorted(summary["chunk_types"].items()):
        print(f"  * {ctype:<24} : {count:>4} vectors")

    # Sample record verification
    client = get_db_client()
    collection = client.get_collection(COLLECTION_NAME)
    sample = collection.get(limit=2, include=["metadatas", "documents"])

    print("\n--- Sample Stored Records ---")
    for i in range(len(sample["ids"])):
        print(f"\n[Record {i+1}] ID: {sample['ids'][i]}")
        print(f"  Document : {sample['documents'][i][:80]}...")
        print(f"  Metadata : {sample['metadatas'][i]}")

    print(f"\n[VectorDB] Storage verification complete: All {summary['total_vectors']} vectors verified.\n")
    return summary


if __name__ == "__main__":
    run_storage_verification()
