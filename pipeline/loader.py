# pipeline/loader.py
"""
Phase 3: Document Loading & Validation
Loads raw scraped JSON records from data/raw/, validates schema completeness,
normalises contents, and provides clean document objects for chunking.
"""

import json
from pathlib import Path
from datetime import datetime

# Resolve base paths reliably
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

REQUIRED_FIELDS = ["slug", "url", "scraped_at", "raw_text"]


def validate(record: dict) -> list[str]:
    """Return a list of missing or empty required fields."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in record or not record[field]:
            errors.append(field)
    return errors


def normalise(record: dict) -> dict:
    """Clean raw text and sanitise table entries."""
    # Normalise whitespace
    record["raw_text"] = record.get("raw_text", "").strip()

    # Clean table dictionaries
    clean_tables = []
    for table in record.get("tables", []):
        if not isinstance(table, dict):
            continue
        clean = {
            str(k).strip(): str(v).strip()
            for k, v in table.items()
            if str(k).strip() and str(v).strip()
        }
        if clean:
            clean_tables.append(clean)
    record["tables"] = clean_tables

    return record


def load_documents() -> list[dict]:
    """
    Load, validate, and normalise all scraped raw JSON files.

    Returns:
        List of validated document dicts ready for chunker.
    Raises:
        FileNotFoundError if data/raw/ is empty.
        ValueError if any file fails validation.
    """
    raw_files = sorted(RAW_DIR.glob("*.json"))

    if not raw_files:
        raise FileNotFoundError(
            f"No raw JSON files found in {RAW_DIR}/. "
            "Please run pipeline/scraper.py first."
        )

    documents = []
    print(f"\n=======================================================")
    print(f" Phase 3: Loading & Validating Documents")
    print(f" Directory: {RAW_DIR}")
    print(f" Found: {len(raw_files)} files")
    print(f"=======================================================\n")

    for raw_file in raw_files:
        try:
            with open(raw_file, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception as e:
            raise ValueError(f"[Loader] [FAIL] Error parsing JSON file {raw_file.name}: {e}")

        # Validate
        errors = validate(record)
        if errors:
            raise ValueError(
                f"[Loader] [FAIL] {raw_file.name} missing required fields: {errors}"
            )

        # Normalise
        record = normalise(record)

        table_rows = sum(len(t) for t in record.get("tables", []))
        scrape_date = str(record.get("scraped_at", ""))[:19].replace("T", " ")
        chars = len(record.get("raw_text", ""))

        print(
            f"  [OK] {record['slug']:<24} "
            f"| Chars: {chars:>6} "
            f"| Table Rows: {table_rows:>3} "
            f"| Scraped: {scrape_date}"
        )

        documents.append(record)

    print(f"\n[Loader] Successfully loaded and validated {len(documents)} document(s).\n")
    return documents


if __name__ == "__main__":
    docs = load_documents()
    for d in docs:
        print(f"\n--- {d['slug']} ---")
        print(f"  Source URL : {d['url']}")
        print(f"  Scraped At : {d['scraped_at']}")
        print(f"  Chars      : {len(d['raw_text'])}")
        print(f"  Tables     : {len(d['tables'])} table(s)")
        if d["tables"]:
            sample_keys = list(d["tables"][0].keys())[:4]
            print(f"  Sample Keys: {sample_keys}")
