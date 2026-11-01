# pipeline/chunker.py
"""
Phase 4: Content-Aware Document Chunking
Consumes validated documents from pipeline.loader.
Applies content-aware chunking:
  1. Atomic table-row chunking for exact metrics (Expense Ratio, Exit Load, SIP, etc.)
  2. Sliding-window paragraph chunking for descriptive / FAQ / background text.
Stores chunks in data/chunks/{slug}_chunks.json.
"""

import json
import uuid
import yaml
import sys
from pathlib import Path

# Resolve paths and ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from pipeline.loader import load_documents
CONFIG_PATH = BASE_DIR / "config.yaml"
CHUNK_DIR = BASE_DIR / "data" / "chunks"
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

CHUNK_SIZE = CONFIG.get("chunking", {}).get("chunk_size", 512)
CHUNK_OVERLAP = CONFIG.get("chunking", {}).get("chunk_overlap", 64)

# Approximation: 1 token ≈ 4 characters
CHAR_SIZE = CHUNK_SIZE * 4
CHAR_OVERLAP = CHUNK_OVERLAP * 4


def make_chunk(
    text: str,
    source_url: str,
    slug: str,
    scraped_at: str,
    chunk_type: str,
    extra_meta: dict = None,
) -> dict:
    """Construct an individual chunk record with rich metadata."""
    chunk = {
        "chunk_id": str(uuid.uuid4()),
        "source_url": source_url,
        "fund_slug": slug,
        "scraped_at": scraped_at,
        "chunk_type": chunk_type,
        "chunk_text": text.strip(),
    }
    if extra_meta:
        chunk.update(extra_meta)
    return chunk


def chunk_tables(tables: list, url: str, slug: str, scraped_at: str) -> list[dict]:
    """
    Atomic table-row chunking:
    Converts key-value pairs and structured metrics into independent, highly retrievable fact chunks.
    Prefixed with fund slug context for semantic disambiguation.
    """
    chunks = []
    fund_title = slug.replace("_", " ").title()

    for table in tables:
        if not isinstance(table, dict):
            continue
        for key, val in table.items():
            key_clean = str(key).strip()
            val_clean = str(val).strip()

            # Skip header-only or blank rows
            if not key_clean or not val_clean or key_clean.lower() == val_clean.lower():
                continue

            fact_text = f"Scheme: {fund_title} | {key_clean}: {val_clean}"
            chunks.append(
                make_chunk(
                    text=fact_text,
                    source_url=url,
                    slug=slug,
                    scraped_at=scraped_at,
                    chunk_type="table_metric",
                    extra_meta={"metric_key": key_clean},
                )
            )
    return chunks


def chunk_prose(text: str, url: str, slug: str, scraped_at: str) -> list[dict]:
    """
    Sliding-window chunking for descriptive prose, guidelines, and FAQs.
    """
    chunks = []
    if not text:
        return chunks

    start = 0
    fund_title = slug.replace("_", " ").title()

    while start < len(text):
        end = start + CHAR_SIZE
        window = text[start:end].strip()

        if window:
            chunk_content = f"[{fund_title}]\n{window}"
            chunks.append(
                make_chunk(
                    text=chunk_content,
                    source_url=url,
                    slug=slug,
                    scraped_at=scraped_at,
                    chunk_type="prose_window",
                )
            )

        start += CHAR_SIZE - CHAR_OVERLAP
    return chunks


def chunk_document(record: dict) -> list[dict]:
    """Applies content-aware chunking to an individual document."""
    url = record["url"]
    slug = record["slug"]
    scraped_at = record["scraped_at"]

    table_chunks = chunk_tables(record.get("tables", []), url, slug, scraped_at)
    prose_chunks = chunk_prose(record.get("raw_text", ""), url, slug, scraped_at)

    return table_chunks + prose_chunks


def run_chunker():
    """Execute chunking across all validated documents."""
    documents = load_documents()
    total_chunks = 0
    all_summary = []

    print(f"\n=======================================================")
    print(f" Phase 4: Data Chunking")
    print(f" Output Directory: {CHUNK_DIR}")
    print(f" Chunk Size: {CHUNK_SIZE} tokens (~{CHAR_SIZE} chars)")
    print(f" Overlap: {CHUNK_OVERLAP} tokens (~{CHAR_OVERLAP} chars)")
    print(f"=======================================================\n")

    for doc in documents:
        slug = doc["slug"]
        chunks = chunk_document(doc)

        out_path = CHUNK_DIR / f"{slug}_chunks.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        table_count = sum(1 for c in chunks if c["chunk_type"] == "table_metric")
        prose_count = sum(1 for c in chunks if c["chunk_type"] == "prose_window")

        print(
            f"  [OK] {slug:<24} "
            f"-> {len(chunks):>3} total chunks "
            f"({table_count:>2} table facts, {prose_count:>2} prose) "
            f"-> {out_path.name}"
        )

        total_chunks += len(chunks)
        all_summary.append({"slug": slug, "chunks": len(chunks), "path": str(out_path)})

    print(f"\n[Chunker] Completed: {total_chunks} chunks generated across {len(documents)} documents.\n")
    return all_summary


if __name__ == "__main__":
    run_chunker()
