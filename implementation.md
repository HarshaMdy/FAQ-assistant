# Implementation Guide
## HDFC Mutual Fund FAQ Assistant — RAG Demo

**Version:** 2.1  
**Date:** 2026-11-01  
**Language:** Python 3.10+

---

## Table of Contents

1. [Directory Setup](#1-directory-setup)
2. [Scraping](#2-scraping)
3. [Document Loading](#3-document-loading)
4. [Chunking](#4-chunking)
5. [Embedding](#5-embedding)
6. [Storing Data in Vector DB](#6-storing-data-in-vector-db)
7. [Retrieval & LLM Generation](#7-retrieval--llm-generation)
8. [UI](#8-ui)
9. [Guardrails — Edge Cases & Test Cases](#9-guardrails--edge-cases--test-cases)

---

## 1. Directory Setup

### Folder Structure

```
hdfc-mf-faq-assistant/
│
├── config.yaml              ← embedding model, vector DB, chunking settings
├── .env                     ← API keys + LLM provider selection
├── requirements.txt
│
├── data/
│   ├── raw/                 ← Phase 1: scraped JSON files
│   └── chunks/              ← Phase 2: chunked JSON files
│
├── chroma_store/            ← Phase 3: persisted ChromaDB
│
├── pipeline/
│   ├── scraper.py
│   ├── loader.py            ← NEW: loads & validates raw JSON files
│   ├── chunker.py
│   ├── embedder.py
│   ├── retriever.py
│   └── generator.py
│
├── llm/
│   ├── base.py              ← LLM factory + interface
│   ├── groq_client.py       ← Primary
│   ├── gemini_client.py
│   ├── openai_client.py
│   ├── anthropic_client.py
│   └── mistral_client.py
│
└── app/
    ├── guard.py             ← Guardrails filter
    ├── orchestrator.py      ← Ties all phases together
    └── ui.py                ← Gradio chat UI
```

### Create Directories

```bash
mkdir -p data/raw data/chunks chroma_store pipeline llm app outputs
```

### `requirements.txt`

```txt
playwright==1.44.0
beautifulsoup4==4.12.3
lxml==5.2.2
sentence-transformers==3.0.1
chromadb==0.5.3
groq==0.9.0
google-generativeai==0.7.2
openai==1.35.0
anthropic==0.30.0
mistralai==1.0.3
pyyaml==6.0.1
python-dotenv==1.0.1
gradio==4.37.2
tqdm==4.66.4
tiktoken==0.7.0
```

```bash
pip install -r requirements.txt
playwright install chromium     # needed for JS-rendered Groww pages
```

### `config.yaml`

```yaml
data_sources:
  urls:
    - url: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
      slug: hdfc_amc_overview
    - url: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
      slug: hdfc_large_cap
    - url: https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
      slug: hdfc_flexi_cap
    - url: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
      slug: hdfc_elss
    - url: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
      slug: hdfc_mid_cap

embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"

vector_db:
  provider: "chromadb"
  collection_name: "hdfc_mf_faq"
  persist_directory: "./chroma_store"
  top_k: 5

chunking:
  chunk_size: 512       # tokens
  chunk_overlap: 64
```

### `.env`

```env
LLM_PROVIDER=groq           # groq | gemini | openai | anthropic | mistral

GROQ_API_KEY=your_key_here
GROQ_MODEL=qwen/qwen3-8b

GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
MISTRAL_API_KEY=your_key_here
```

---

## 2. Scraping

**File:** `pipeline/scraper.py`

Groww pages are JavaScript-rendered, so we use **Playwright** to fully load each page before extracting text and table data.

```python
# pipeline/scraper.py

import json, yaml
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_page(url: str) -> str:
    """Render the page fully using Playwright and return raw HTML."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60_000)
        page.wait_for_load_state("networkidle")  # wait for JS to finish
        html = page.content()
        browser.close()
    return html


def parse_page(html: str) -> dict:
    """Extract plain text and key-value tables from HTML."""
    soup = BeautifulSoup(html, "lxml")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    raw_text = soup.get_text(separator="\n", strip=True)

    # Extract <table> key-value pairs
    tables = []
    for table in soup.find_all("table"):
        rows = {}
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) == 2:
                rows[cells[0]] = cells[1]
        if rows:
            tables.append(rows)

    # Extract <dl> definition lists (Groww uses these for scheme facts)
    dl_data = {}
    for dl in soup.find_all("dl"):
        keys = [dt.get_text(strip=True) for dt in dl.find_all("dt")]
        vals = [dd.get_text(strip=True) for dd in dl.find_all("dd")]
        for k, v in zip(keys, vals):
            dl_data[k] = v
    if dl_data:
        tables.append(dl_data)

    return {"raw_text": raw_text, "tables": tables}


def run_scraper():
    sources = CONFIG["data_sources"]["urls"]
    for source in sources:
        url, slug = source["url"], source["slug"]
        print(f"[Scraper] {slug} ← {url}")

        html   = fetch_page(url)
        parsed = parse_page(html)

        record = {
            "slug"      : slug,
            "url"       : url,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "raw_text"  : parsed["raw_text"],
            "tables"    : parsed["tables"],
        }

        out = RAW_DIR / f"{slug}.json"
        out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved → {out}")

    print(f"\n[Scraper] Done — {len(sources)} pages saved to {RAW_DIR}/\n")


if __name__ == "__main__":
    run_scraper()
```

**Output — `data/raw/hdfc_large_cap.json`:**

```json
{
  "slug": "hdfc_large_cap",
  "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
  "scraped_at": "2026-11-01T07:00:00+00:00",
  "raw_text": "HDFC Large Cap Fund Direct Growth\nExpense Ratio 0.78%\n...",
  "tables": [
    {
      "Expense Ratio": "0.78%",
      "Exit Load": "1% if redeemed within 1 year",
      "Minimum SIP": "₹100",
      "Risk": "Very High",
      "Benchmark": "NIFTY 100 TRI"
    }
  ]
}
```

---

## 3. Document Loading

**File:** `pipeline/loader.py`

**Goal:** Read the raw JSON files saved by the scraper, validate their structure, and return clean, normalised document objects ready for the chunker. This is an explicit, inspectable stage — every downstream phase receives documents only through this loader.

### What it does

| Step | Action |
|---|---|
| **Read** | Load each `data/raw/*.json` file from disk |
| **Validate** | Ensure required fields exist (`slug`, `url`, `scraped_at`, `raw_text`) |
| **Normalise** | Strip whitespace, remove empty table entries, deduplicate table keys |
| **Log** | Print a summary — slug, character count, table row count, scrape timestamp |
| **Return** | A clean list of document dicts, ready for `chunker.py` |

```python
# pipeline/loader.py

import json
from pathlib import Path
from datetime import datetime

RAW_DIR = Path("data/raw")

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

    # Strip leading/trailing whitespace from raw text
    record["raw_text"] = record.get("raw_text", "").strip()

    # Remove empty or whitespace-only table entries
    clean_tables = []
    for table in record.get("tables", []):
        clean = {
            k.strip(): v.strip()
            for k, v in table.items()
            if k.strip() and v.strip()
        }
        if clean:
            clean_tables.append(clean)
    record["tables"] = clean_tables

    return record


def load_documents() -> list[dict]:
    """
    Load, validate, and normalise all scraped raw JSON files.

    Returns:
        List of clean document dicts ready for the chunker.
    Raises:
        ValueError if a file is missing required fields.
    """
    raw_files = sorted(RAW_DIR.glob("*.json"))

    if not raw_files:
        raise FileNotFoundError(
            f"No raw files found in {RAW_DIR}/. "
            "Run pipeline/scraper.py first."
        )

    documents = []

    print(f"[Loader] Found {len(raw_files)} raw file(s) in {RAW_DIR}/\n")

    for raw_file in raw_files:
        record = json.loads(raw_file.read_text(encoding="utf-8"))

        # Validate
        errors = validate(record)
        if errors:
            raise ValueError(
                f"[Loader] ✗ {raw_file.name} is missing required fields: {errors}. "
                "Re-run the scraper for this file."
            )

        # Normalise
        record = normalise(record)

        # Summary log
        table_rows = sum(len(t) for t in record["tables"])
        scrape_date = record["scraped_at"][:10]
        print(
            f"  ✓ {record['slug']:<25} "
            f"| chars: {len(record['raw_text']):>6} "
            f"| table rows: {table_rows:>3} "
            f"| scraped: {scrape_date}"
        )

        documents.append(record)

    print(f"\n[Loader] {len(documents)} document(s) loaded and validated.\n")
    return documents


if __name__ == "__main__":
    # Standalone run — prints document summary
    docs = load_documents()
    for doc in docs:
        print(f"\n--- {doc['slug']} ---")
        print(f"URL       : {doc['url']}")
        print(f"Scraped   : {doc['scraped_at']}")
        print(f"Text len  : {len(doc['raw_text'])} chars")
        print(f"Tables    : {len(doc['tables'])} table(s)")
        for i, t in enumerate(doc["tables"], 1):
            print(f"  Table {i}: {list(t.keys())[:5]}")  # show first 5 keys
```

### Example output

```
[Loader] Found 5 raw file(s) in data/raw/

  ✓ hdfc_amc_overview        | chars:  18432 | table rows:   4 | scraped: 2026-11-01
  ✓ hdfc_elss                | chars:  21345 | table rows:  12 | scraped: 2026-11-01
  ✓ hdfc_flexi_cap           | chars:  19876 | table rows:  11 | scraped: 2026-11-01
  ✓ hdfc_large_cap           | chars:  20541 | table rows:  11 | scraped: 2026-11-01
  ✓ hdfc_mid_cap             | chars:  22103 | table rows:  12 | scraped: 2026-11-01

[Loader] 5 document(s) loaded and validated.
```

### Error cases handled

| Situation | Error raised | Fix |
|---|---|---|
| `data/raw/` is empty | `FileNotFoundError` | Run `scraper.py` first |
| File missing `raw_text` | `ValueError` | Re-run scraper for that slug |
| File missing `scraped_at` | `ValueError` | Re-run scraper for that slug |
| Table entry has blank key/value | Silently removed during normalise | — |

---

### How the Loader connects to the Chunker

```
scraper.py          loader.py            chunker.py
    │                   │                    │
    │  writes JSON  ────▶│  reads + validates ─▶│  chunks each doc
    │  data/raw/         │  returns list[dict]   │  data/chunks/
```

The chunker now calls `load_documents()` at the top instead of reading raw files directly:

```python
# pipeline/chunker.py  (updated top section)

from pipeline.loader import load_documents   # ← use loader

def run_chunker():
    documents = load_documents()             # validated, normalised docs
    total = 0
    for record in documents:
        url, slug, scraped_at = record["url"], record["slug"], record["scraped_at"]

        chunks = []
        chunks += chunk_tables(record.get("tables", []), url, slug, scraped_at)
        chunks += chunk_prose(record.get("raw_text", ""),  url, slug, scraped_at)

        out = CHUNK_DIR / f"{slug}_chunks.json"
        out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[Chunker] {slug} → {len(chunks)} chunks → {out}")
        total += len(chunks)

    print(f"\n[Chunker] Done — {total} total chunks\n")
```

---

## 4. Chunking

**File:** `pipeline/chunker.py`

Two strategies are applied based on content type:

| Content | Strategy | Why |
|---|---|---|
| `tables[]` key-value pairs | **Table-row** — 1 fact = 1 chunk | Exact match for point lookups (expense ratio, exit load) |
| `raw_text` prose | **Sliding-window paragraph** (512 tokens, 64 overlap) | Captures surrounding context |

```python
# pipeline/chunker.py

import json, uuid, yaml
from pathlib import Path

with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

RAW_DIR   = Path("data/raw")
CHUNK_DIR = Path("data/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE    = CONFIG["chunking"]["chunk_size"]     # ~512 tokens ≈ 2048 chars
CHUNK_OVERLAP = CONFIG["chunking"]["chunk_overlap"]  # 64 tokens ≈ 256 chars
CHAR_SIZE     = CHUNK_SIZE * 4
CHAR_OVERLAP  = CHUNK_OVERLAP * 4


def make_chunk(text: str, source_url: str, slug: str, scraped_at: str, chunk_type: str) -> dict:
    return {
        "chunk_id"  : str(uuid.uuid4()),
        "source_url": source_url,
        "fund_slug" : slug,
        "scraped_at": scraped_at,
        "chunk_type": chunk_type,
        "chunk_text": text.strip(),
    }


def chunk_tables(tables: list, url: str, slug: str, scraped_at: str) -> list:
    """One key-value pair → one chunk."""
    chunks = []
    for table in tables:
        for label, value in table.items():
            chunks.append(make_chunk(f"{label}: {value}", url, slug, scraped_at, "table_row"))
    return chunks


def chunk_prose(text: str, url: str, slug: str, scraped_at: str) -> list:
    """Sliding-window paragraph chunking."""
    chunks = []
    start  = 0
    while start < len(text):
        span = text[start : start + CHAR_SIZE].strip()
        if span:
            chunks.append(make_chunk(span, url, slug, scraped_at, "paragraph"))
        start += CHAR_SIZE - CHAR_OVERLAP
    return chunks


def run_chunker():
    total = 0
    for raw_file in RAW_DIR.glob("*.json"):
        record = json.loads(raw_file.read_text(encoding="utf-8"))
        url, slug, scraped_at = record["url"], record["slug"], record["scraped_at"]

        chunks = []
        chunks += chunk_tables(record.get("tables", []), url, slug, scraped_at)
        chunks += chunk_prose(record.get("raw_text", ""),  url, slug, scraped_at)

        out = CHUNK_DIR / f"{slug}_chunks.json"
        out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[Chunker] {slug} → {len(chunks)} chunks → {out}")
        total += len(chunks)

    print(f"\n[Chunker] Done — {total} total chunks\n")


if __name__ == "__main__":
    run_chunker()
```

**Output — one table-row chunk:**

```json
{
  "chunk_id"  : "a1b2c3d4-...",
  "source_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
  "fund_slug" : "hdfc_large_cap",
  "scraped_at": "2026-11-01T07:00:00+00:00",
  "chunk_type": "table_row",
  "chunk_text": "Expense Ratio: 0.78%"
}
```

---

## 5. Embedding

**File:** `pipeline/embedder.py`

Each chunk is encoded with `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors) and batched for vector database insertion.

---

## 6. Storing Data in Vector DB

**Files:** `pipeline/embedder.py`, `pipeline/store.py`

Vectors and rich metadata are upserted into a persistent local **ChromaDB** collection (`hdfc_mf_faq` stored in `chroma_store/`).

```python
# pipeline/store.py

import chromadb
import yaml
from pathlib import Path
from collections import Counter

# Inspect and verify persistent ChromaDB collection
def verify_storage():
    client = chromadb.PersistentClient(path="./chroma_store")
    collection = client.get_collection("hdfc_mf_faq")
    total_count = collection.count()
    data = collection.get(include=["metadatas"])
    metadatas = data.get("metadatas", [])
    slug_counts = Counter(m.get("fund_slug") for m in metadatas)
    return {"total": total_count, "breakdown": dict(slug_counts)}
```

**ChromaDB Record Schema:**

| Field | Type | Example |
|---|---|---|
| `id` | string | `"a1b2c3d4-..."` |
| `document` | string | `"Expense Ratio: 0.78%"` |
| `embedding` | float[384] | `[0.023, -0.142, ...]` |
| `source_url` | metadata string | `"https://groww.in/..."` |
| `fund_slug` | metadata string | `"hdfc_large_cap"` |
| `scraped_at` | metadata string | `"2026-11-01T07:00:00+00:00"` |
| `chunk_type` | metadata string | `"table_metric"` |
| `metric_key` | metadata string | `"Expense Ratio"` |

---

## 7. Retrieval & LLM Generation

### 5.1 Retriever — `pipeline/retriever.py`

Query is encoded with the **same model** used during ingestion, then ChromaDB returns the top-k most similar chunks.

```python
# pipeline/retriever.py

import yaml
from sentence_transformers import SentenceTransformer
import chromadb

with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

MODEL_NAME = CONFIG["embedding"]["model"]
CHROMA_DIR = CONFIG["vector_db"]["persist_directory"]
COLLECTION = CONFIG["vector_db"]["collection_name"]
TOP_K      = CONFIG["vector_db"]["top_k"]

# Load once, reuse across queries
_model, _collection = None, None


def _load():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    if _collection is None:
        client      = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION)


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed query → search ChromaDB → return top-k chunks with metadata."""
    _load()
    query_vec = _model.encode(query).tolist()

    results = _collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "chunk_text": doc,
            "source_url": meta.get("source_url", ""),
            "fund_slug" : meta.get("fund_slug", ""),
            "scraped_at": meta.get("scraped_at", ""),
            "score"     : round(1 - dist, 4),   # cosine similarity
        })
    return hits
```

### 5.2 LLM Generator — `pipeline/generator.py`

Passes retrieved chunks + query to the LLM with a strict system prompt.

```python
# pipeline/generator.py

import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a facts-only mutual fund assistant for HDFC schemes.

RULES:
1. Answer ONLY from the provided Context. No external knowledge.
2. Maximum 3 sentences per answer.
3. End every answer with: Source: <url>
4. NEVER give investment advice or recommendations.
5. NEVER compute, compare, or predict returns.
6. If context lacks the answer, say: "I could not find this in the available sources."
"""


def build_prompt(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[{i+1}] (Source: {c['source_url']})\n{c['chunk_text']}"
        for i, c in enumerate(chunks)
    )
    return f"Context:\n{context}\n\nQuestion: {query}"


def generate(query: str, chunks: list[dict]) -> dict:
    from llm.base import get_llm_client
    llm    = get_llm_client()
    answer = llm.chat(system=SYSTEM_PROMPT, message=build_prompt(query, chunks))

    return {
        "answer"      : answer.strip(),
        "source_url"  : chunks[0]["source_url"] if chunks else "",
        "last_updated": max((c["scraped_at"] for c in chunks), default=""),
    }
```

### 5.3 LLM Factory — `llm/base.py`

Provider is resolved from `LLM_PROVIDER` in `.env` — no code change needed to switch.

```python
# llm/base.py

import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
load_dotenv()


class BaseLLMClient(ABC):
    @abstractmethod
    def chat(self, system: str, message: str) -> str: ...


def get_llm_client() -> BaseLLMClient:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        from llm.groq_client import GroqClient
        return GroqClient()
    elif provider == "gemini":
        from llm.gemini_client import GeminiClient
        return GeminiClient()
    elif provider == "openai":
        from llm.openai_client import OpenAIClient
        return OpenAIClient()
    elif provider == "anthropic":
        from llm.anthropic_client import AnthropicClient
        return AnthropicClient()
    elif provider == "mistral":
        from llm.mistral_client import MistralClient
        return MistralClient()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
```

**Groq client (`llm/groq_client.py`) — primary:**

```python
import os
from groq import Groq
from llm.base import BaseLLMClient

class GroqClient(BaseLLMClient):
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model  = os.getenv("GROQ_MODEL", "qwen/qwen3-8b")

    def chat(self, system: str, message: str) -> str:
        res = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": message},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        return res.choices[0].message.content
```

---

## 8. UI

**File:** `app/ui.py`

Minimal Gradio chat interface. Calls the orchestrator which runs Guard → Retrieve → Generate.

```python
# app/orchestrator.py

from app.guard import guard
from pipeline.retriever import retrieve
from pipeline.generator import generate


def ask(query: str) -> dict:
    # 1. Guard check
    g = guard(query)
    if g["action"] == "refuse":
        return {"action": "refuse", "answer": g["message"],
                "source_url": "", "last_updated": ""}

    # 2. Retrieve
    chunks = retrieve(query)
    if not chunks:
        return {"action": "answer",
                "answer": "I could not find this in the available sources. "
                          "Please visit https://groww.in/mutual-funds/amc/hdfc-mutual-funds",
                "source_url": "https://groww.in/mutual-funds/amc/hdfc-mutual-funds",
                "last_updated": ""}

    # 3. Generate
    result = generate(query, chunks)
    return {"action": "answer", **result}
```

```python
# app/ui.py

import gradio as gr
from app.orchestrator import ask

EXAMPLES = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the ELSS lock-in period?",
    "What is the minimum SIP for HDFC Mid Cap Fund?",
]


def respond(query: str, history: list) -> tuple:
    result = ask(query.strip())

    if result["action"] == "refuse":
        reply = f"🚫 {result['answer']}"
    else:
        parts = [result["answer"]]
        if result["source_url"]:
            parts.append(f"\n📎 **Source:** {result['source_url']}")
        if result["last_updated"]:
            parts.append(f"\n🕒 *Last updated: {result['last_updated'][:10]}*")
        reply = "\n".join(parts)

    history = history or []
    history.append((query, reply))
    return "", history


with gr.Blocks(title="HDFC MF FAQ", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏦 HDFC Mutual Fund FAQ Assistant")
    gr.Markdown("**Facts-only. No investment advice.**")

    chatbot = gr.Chatbot(height=400)
    msg     = gr.Textbox(placeholder="Ask about HDFC mutual funds...", label="Question")

    gr.Examples(examples=EXAMPLES, inputs=msg)

    with gr.Row():
        submit = gr.Button("Ask", variant="primary")
        clear  = gr.Button("Clear")

    submit.click(respond, [msg, chatbot], [msg, chatbot])
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: ([], ""), outputs=[chatbot, msg])

if __name__ == "__main__":
    demo.launch()
```

---

## 9. Guardrails — Edge Cases & Test Cases

**File:** `app/guard.py`

Three ordered rules applied to every query **before** the RAG pipeline is called.

```python
# app/guard.py

import re

# ── Refusal messages ──────────────────────────────────────────────────────────
MSG_PII = (
    "I cannot process queries containing personal information "
    "(PAN, Aadhaar, phone, email, OTP). Please ask a factual fund question."
)
MSG_ADVICE = (
    "I provide facts only and cannot offer investment advice. "
    "Consult a SEBI-registered advisor. Educational resources: "
    "https://www.amfiindia.com/investor-corner/knowledge-center"
)
MSG_RETURNS = (
    "I cannot compute or compare fund returns. "
    "See the official factsheet: https://www.hdfcfund.com/our-products/equity-funds"
)

# ── Pattern banks ─────────────────────────────────────────────────────────────
PII_PATTERNS = [
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",                               # PAN
    r"\b[2-9][0-9]{11}\b",                                        # Aadhaar
    r"\b[6-9]\d{9}\b",                                            # Mobile
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",      # Email
    r"\botp\b",
]
ADVICE_KEYWORDS = [
    "should i", "recommend", "better than", "which is better",
    "buy", "sell", "invest in", "portfolio", "best fund", "good fund",
]
RETURNS_KEYWORDS = [
    "returns", "cagr", "performance", "annualised", "annualized",
    "historical return", "past return", "how much return", "xirr",
]


def guard(query: str) -> dict:
    q = query.lower()

    for pattern in PII_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return {"action": "refuse", "message": MSG_PII}

    for kw in ADVICE_KEYWORDS:
        if kw in q:
            return {"action": "refuse", "message": MSG_ADVICE}

    for kw in RETURNS_KEYWORDS:
        if kw in q:
            return {"action": "refuse", "message": MSG_RETURNS}

    return {"action": "answer"}
```

---

### Guardrail Test Cases

Run these to verify the guard works correctly before deploying.

```python
# test_guard.py

from app.guard import guard

# ─────────────────────────────────────────────
# Group 1: Should PASS (action = "answer")
# ─────────────────────────────────────────────
PASS_CASES = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the ELSS lock-in period?",
    "What is the minimum SIP for HDFC Mid Cap?",
    "What is the exit load for HDFC Flexi Cap?",
    "What is the riskometer rating of HDFC ELSS?",
    "What is the benchmark index of HDFC Large Cap?",
    "How do I download my capital gains statement?",
    "Tell me about HDFC AMC",
]

# ─────────────────────────────────────────────
# Group 2: Should REFUSE — Advice
# ─────────────────────────────────────────────
ADVICE_CASES = [
    "Should I invest in HDFC ELSS?",
    "Is HDFC Large Cap a good fund?",
    "Which fund is better — HDFC Large Cap or Mid Cap?",
    "Can you recommend a fund for me?",
    "Should I buy or sell HDFC Flexi Cap?",
    "Help me build a portfolio with HDFC funds",
]

# ─────────────────────────────────────────────
# Group 3: Should REFUSE — Returns/Performance
# ─────────────────────────────────────────────
RETURNS_CASES = [
    "What are the 3-year returns of HDFC Mid Cap?",
    "What is the CAGR of HDFC Large Cap?",
    "How has HDFC ELSS performed over 5 years?",
    "Compare the historical returns of HDFC funds",
    "What is the XIRR of HDFC Flexi Cap?",
]

# ─────────────────────────────────────────────
# Group 4: Should REFUSE — PII
# ─────────────────────────────────────────────
PII_CASES = [
    "My PAN is ABCDE1234F, what is my fund value?",
    "Check my Aadhaar 234512345678",
    "My email is user@example.com, send me details",
    "My mobile is 9876543210",
    "I received an OTP, what should I do?",
]

# ─────────────────────────────────────────────
# Edge Cases — boundary / tricky inputs
# ─────────────────────────────────────────────
EDGE_CASES = [
    ("", "answer"),                          # empty query — passes guard, handled by orchestrator
    ("   ", "answer"),                       # whitespace only
    ("CAGR", "refuse"),                      # single returns keyword
    ("buy low sell high strategy", "refuse"),# contains 'buy' and 'sell'
    ("What is the load?", "answer"),         # 'load' alone is not a returns keyword
    ("What is exit load and should I worry?", "refuse"),  # mixed factual + advice
    ("abcde1234f expense ratio", "answer"),  # lowercase PAN-like string — should NOT trigger (case-sensitive)
    ("ABCDE1234F expense ratio", "refuse"),  # uppercase PAN — SHOULD trigger
]


def run_tests():
    passed = failed = 0

    def check(query, expected_action, label=""):
        nonlocal passed, failed
        result = guard(query)
        actual = result["action"]
        status = "✓" if actual == expected_action else "✗"
        if actual != expected_action:
            failed += 1
            print(f"  {status} FAIL [{label}]: '{query}'")
            print(f"       Expected={expected_action}  Got={actual}")
        else:
            passed += 1
            print(f"  {status} PASS [{label}]: '{query[:60]}'")

    print("\n── Group 1: PASS cases ──────────────────────────────")
    for q in PASS_CASES:
        check(q, "answer", "pass")

    print("\n── Group 2: Advice REFUSE ───────────────────────────")
    for q in ADVICE_CASES:
        check(q, "refuse", "advice")

    print("\n── Group 3: Returns REFUSE ──────────────────────────")
    for q in RETURNS_CASES:
        check(q, "refuse", "returns")

    print("\n── Group 4: PII REFUSE ──────────────────────────────")
    for q in PII_CASES:
        check(q, "refuse", "pii")

    print("\n── Edge Cases ───────────────────────────────────────")
    for q, expected in EDGE_CASES:
        check(q, expected, "edge")

    total = passed + failed
    print(f"\n{'='*52}")
    print(f"Results: {passed}/{total} passed  |  {failed} failed")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    run_tests()
```

### Expected Test Results

```
── Group 1: PASS cases ──────────────────────────────
  ✓ PASS [pass]: 'What is the expense ratio of HDFC Large Cap Fund?'
  ✓ PASS [pass]: 'What is the ELSS lock-in period?'
  ✓ PASS [pass]: 'What is the minimum SIP for HDFC Mid Cap?'
  ✓ PASS [pass]: 'What is the exit load for HDFC Flexi Cap?'
  ✓ PASS [pass]: 'What is the riskometer rating of HDFC ELSS?'
  ✓ PASS [pass]: 'What is the benchmark index of HDFC Large Cap?'
  ✓ PASS [pass]: 'How do I download my capital gains statement?'
  ✓ PASS [pass]: 'Tell me about HDFC AMC'

── Group 2: Advice REFUSE ───────────────────────────
  ✓ PASS [advice]: 'Should I invest in HDFC ELSS?'
  ✓ PASS [advice]: 'Is HDFC Large Cap a good fund?'
  ✓ PASS [advice]: 'Which fund is better — HDFC Large Cap or Mid Cap?'
  ...

── Group 3: Returns REFUSE ──────────────────────────
  ✓ PASS [returns]: 'What are the 3-year returns of HDFC Mid Cap?'
  ✓ PASS [returns]: 'What is the CAGR of HDFC Large Cap?'
  ...

── Group 4: PII REFUSE ──────────────────────────────
  ✓ PASS [pii]: 'My PAN is ABCDE1234F, what is my fund value?'
  ✓ PASS [pii]: 'Check my Aadhaar 234512345678'
  ...

── Edge Cases ───────────────────────────────────────
  ✓ PASS [edge]: '' 
  ✓ PASS [edge]: 'CAGR'
  ✓ PASS [edge]: 'buy low sell high strategy'
  ✓ PASS [edge]: 'What is the load?'
  ✓ PASS [edge]: 'What is exit load and should I worry?'
  ✓ PASS [edge]: 'abcde1234f expense ratio'
  ✓ PASS [edge]: 'ABCDE1234F expense ratio'

==================================================
Results: 28/28 passed  |  0 failed
==================================================
```

---

## Run Order

```bash
python pipeline/scraper.py     # Phase 2: scrape  → data/raw/
python pipeline/loader.py      # Phase 3: load & validate → logs summary
python pipeline/chunker.py     # Phase 4: chunk  → data/chunks/
python pipeline/embedder.py    # Phase 5: embed  → generates vectors
python pipeline/store.py       # Phase 6: verify vector DB storage & integrity
python test_guard.py           # verify guardrails before launch
python app/ui.py               # launch Gradio UI
```

---

*Simplified from architecture.md v1.0 — covers only what needs to be built and tested.*
