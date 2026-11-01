# Architecture Document
## HDFC Mutual Fund FAQ Assistant — RAG Demo

**Version:** 1.0  
**Date:** 2026-11-01  
**Based on:** PRD v1.0

---

## 1. System Overview

The HDFC MF FAQ Assistant is a **Retrieval-Augmented Generation (RAG)** system. It scrapes official Groww public pages, builds a searchable knowledge base, and uses an LLM to answer factual mutual fund queries with citations — while refusing advice-oriented questions.

The system is intentionally designed to **expose every RAG stage explicitly** for demo and evaluation purposes.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                           │
│                                                                     │
│  [Groww Pages]                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌─────────────┐  │
│  │  Phase1 │───▶│  Phase2  │───▶│  Phase 3  │───▶│  ChromaDB   │  │
│  │  Scrape │    │  Chunk   │    │   Embed   │    │  (Persist)  │  │
│  └─────────┘    └──────────┘    └───────────┘    └─────────────┘  │
│                                  all-MiniLM-L6-v2                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                              │
│                                                                     │
│  [User Query]                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌─────────────┐  │
│  │  Phase4 │───▶│  Phase4  │───▶│  Phase 5  │───▶│  Response   │  │
│  │  Embed  │    │ Retrieve │    │    LLM    │    │ + Citation  │  │
│  │  Query  │    │ Top-K    │    │ Generate  │    │ + Refusal   │  │
│  └─────────┘    └──────────┘    └───────────┘    └─────────────┘  │
│  all-MiniLM-L6-v2  ChromaDB    Groq/Gemini/OAI                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Architecture

### 3.1 Full Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             UI Layer                                     │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │  Chat Interface                                                 │    │
│   │  - Welcome message                                              │    │
│   │  - 3 example questions                                          │    │
│   │  - "Facts-only. No investment advice." disclaimer               │    │
│   │  - Free-text input box                                          │    │
│   │  - Answer display (answer + citation + last-updated)            │    │
│   └──────────────────────────┬─────────────────────────────────────┘    │
└─────────────────────────────-│──────────────────────────────────────────┘
                               │  User Query
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           Application Layer                              │
│                                                                          │
│   ┌────────────────┐    ┌──────────────────┐    ┌─────────────────────┐ │
│   │  Query Router  │───▶│  Guard / Filter  │───▶│   RAG Orchestrator  │ │
│   │                │    │  (Advice check)  │    │                     │ │
│   └────────────────┘    └──────────────────┘    └──────────┬──────────┘ │
│                                │                            │            │
│                         [Refuse + link]              [Factual query]    │
│                                │                            │            │
│                                ▼                            ▼            │
│                         ┌────────────┐           ┌──────────────────┐   │
│                         │  Refusal   │           │  Retrieval Chain │   │
│                         │  Response  │           │  (Phase 4+5)     │   │
│                         └────────────┘           └──────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                                                         │
                               ┌─────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            RAG Core Layer                                │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                      Ingestion Pipeline                          │  │
│   │                                                                  │  │
│   │  ┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌─────────┐  │  │
│   │  │ Scraper  │──▶│ Chunker  │──▶│   Embedder   │──▶│ChromaDB │  │  │
│   │  │(Phase 1) │   │(Phase 2) │   │  (Phase 3)   │   │ Store   │  │  │
│   │  └──────────┘   └──────────┘   └──────────────┘   └─────────┘  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                      Query Pipeline                              │  │
│   │                                                                  │  │
│   │  ┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌─────────┐  │  │
│   │  │  Query   │──▶│  Vector  │──▶│  LLM Client  │──▶│Response │  │  │
│   │  │ Embedder │   │ Retrieval│   │  (Phase 5)   │   │ Builder │  │  │
│   │  │(Phase 4) │   │(Phase 4) │   └──────────────┘   └─────────┘  │  │
│   │  └──────────┘   └──────────┘                                    │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Infrastructure Layer                             │
│                                                                          │
│   ┌───────────────┐   ┌────────────────┐   ┌──────────────────────────┐ │
│   │   ChromaDB    │   │ Embedding Model│   │      LLM Providers       │ │
│   │ (Vector Store)│   │ all-MiniLM-L6-v2  │   │ Groq / Gemini / OpenAI  │ │
│   │ ./chroma_store│   │ (local/cached) │   │ Anthropic / Mistral      │ │
│   └───────────────┘   └────────────────┘   └──────────────────────────┘ │
│                                                                          │
│   ┌───────────────┐   ┌────────────────┐                                │
│   │  Raw Data     │   │  config.yaml   │                                │
│   │  Store        │   │  + .env        │                                │
│   │ (scraped HTML)│   │ (config-driven)│                                │
│   └───────────────┘   └────────────────┘                                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Phase-by-Phase Design

### Phase 1 — Data Loading (Scraper)

```
┌────────────────────────────────────────────────────┐
│                   Scraper Module                   │
│                                                    │
│  Input : List of 5 Groww URLs (config)             │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  for each URL:                               │  │
│  │    1. Fetch page (requests / Playwright)     │  │
│  │    2. Parse HTML → extract text + tables     │  │
│  │    3. Attach metadata:                       │  │
│  │         source_url, scrape_timestamp         │  │
│  │    4. Write to raw_data/ as JSON             │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  Output : raw_data/{fund_slug}.json                │
│           { url, scraped_at, raw_text, tables[] }  │
└────────────────────────────────────────────────────┘
```

**Notes:**
- Groww pages are JS-rendered → use **Playwright** or **Selenium** as fallback over plain `requests`.
- Store raw content as-is for traceability and re-chunking without re-scraping.

---

### Phase 2 — Data Chunking

```
┌────────────────────────────────────────────────────┐
│                   Chunker Module                   │
│                                                    │
│  Input : raw_data/{fund_slug}.json                 │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  Content-type detection:                     │  │
│  │    ├─ Table data  → table-aware chunking     │  │
│  │    │   (each row / key-value = 1 chunk)      │  │
│  │    └─ Prose text  → paragraph/sentence       │  │
│  │        chunking (size=512, overlap=64 tokens) │  │
│  │                                              │  │
│  │  Each chunk stored with:                     │  │
│  │    chunk_id, source_url, chunk_text,         │  │
│  │    chunk_type, fund_slug                     │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  Output : chunks/{fund_slug}_chunks.json           │
│           [ { chunk_id, source_url,                │
│               chunk_text, chunk_type } ]           │
└────────────────────────────────────────────────────┘
```

**Chunking Strategy Decision (AI Agent):**

| Content Type | Strategy | Rationale |
|---|---|---|
| Scheme fact tables (expense ratio, exit load, NAV) | Table-row chunking — 1 fact = 1 chunk | Maximizes retrieval precision for point lookups |
| AMC overview prose | Paragraph chunking (512 tokens, 64 overlap) | Captures context around each fact |
| FAQs / structured lists | Section-level chunking | Keeps Q&A pairs together |

---

### Phase 3 — Data Embedding & Storage

```
┌────────────────────────────────────────────────────┐
│                  Embedder Module                   │
│                                                    │
│  Input : chunks/{fund_slug}_chunks.json            │
│                                                    │
│  Model : sentence-transformers/all-MiniLM-L6-v2   │
│          (384-dim dense vector)                    │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  for each chunk:                             │  │
│  │    1. Encode chunk_text → embedding vector   │  │
│  │    2. Upsert into ChromaDB collection        │  │
│  │       - id       = chunk_id                  │  │
│  │       - embedding = vector                   │  │
│  │       - document  = chunk_text               │  │
│  │       - metadata  = { source_url,            │  │
│  │                       fund_slug,             │  │
│  │                       scraped_at }           │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  Output : ChromaDB collection "hdfc_mf_faq"        │
│           persisted at ./chroma_store/             │
└────────────────────────────────────────────────────┘
```

**ChromaDB Collection Schema:**

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique chunk identifier |
| `embedding` | float[384] | all-MiniLM-L6-v2 vector |
| `document` | string | Raw chunk text |
| `source_url` | string (metadata) | Originating Groww page URL |
| `fund_slug` | string (metadata) | e.g., `hdfc-large-cap` |
| `scraped_at` | ISO datetime (metadata) | When the source was scraped |

---

### Phase 4 — Query Embedding & Retrieval

```
┌────────────────────────────────────────────────────┐
│                  Retriever Module                  │
│                                                    │
│  Input : user_query (string)                       │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  1. Encode query with all-MiniLM-L6-v2       │  │
│  │     (same model as ingestion)                │  │
│  │  2. Query ChromaDB:                          │  │
│  │     collection.query(                        │  │
│  │       query_embeddings=[query_vec],          │  │
│  │       n_results=top_k,          # e.g. 5    │  │
│  │       include=["documents",                  │  │
│  │                "metadatas",                  │  │
│  │                "distances"]                  │  │
│  │     )                                        │  │
│  │  3. Return top-k chunks + source_url + score │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  Output : [ { chunk_text, source_url,              │
│               score, fund_slug } ]                 │
└────────────────────────────────────────────────────┘
```

---

### Phase 5 — LLM Generation

```
┌────────────────────────────────────────────────────┐
│                   LLM Generator                    │
│                                                    │
│  Input : user_query + retrieved_chunks[]           │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  System Prompt (always injected):            │  │
│  │  "You are a facts-only MF assistant.         │  │
│  │   Answer ONLY from the provided context.     │  │
│  │   Max 3 sentences. Always cite source URL.   │  │
│  │   NEVER give investment advice.              │  │
│  │   NEVER compute or compare returns."         │  │
│  │                                              │  │
│  │  User Message:                               │  │
│  │  Context: {chunk_1}\n{chunk_2}...\n          │  │
│  │  Question: {user_query}                      │  │
│  │                                              │  │
│  │  LLM Response →                             │  │
│  │    answer_text (≤ 3 sentences)               │  │
│  │    + citation_url (from chunk metadata)      │  │
│  │    + "Last updated from sources: {date}"     │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  LLM Provider : resolved from LLM_PROVIDER in .env │
└────────────────────────────────────────────────────┘
```

---

## 5. Query Flow — Sequence Diagram

```
User          UI          Guard        Retriever      LLM         ChromaDB
 │             │             │              │            │             │
 │──query────▶│             │              │            │             │
 │             │──query────▶│              │            │             │
 │             │             │             │            │             │
 │             │  [Advice?]──┘             │            │             │
 │             │  ┌──Yes──▶ Refuse msg     │            │             │
 │             │  └──No──────────────────▶│             │            │
 │             │             │        embed query        │             │
 │             │             │              │──────────────────────▶│
 │             │             │              │◀── top-k chunks ──────│
 │             │             │              │            │             │
 │             │             │              │──chunks──▶│             │
 │             │             │              │            │──generate──▶
 │             │             │              │            │◀── answer ──
 │             │             │◀─────────────────────────│             │
 │             │◀──response──│              │            │             │
 │◀──answer + │             │              │            │             │
 │  citation──│             │              │            │             │
```

---

## 6. Guard / Filter Logic

```
┌──────────────────────────────────────────────────────┐
│                 Query Guard Module                   │
│                                                      │
│  Input: user_query                                   │
│                                                      │
│  Rules (applied in order):                          │
│  ┌────────────────────────────────────────────────┐  │
│  │  1. PII check — reject if query contains:      │  │
│  │     PAN / Aadhaar / phone / email / OTP        │  │
│  │     → "We cannot process personal information" │  │
│  │                                                │  │
│  │  2. Advice check — reject if query contains:   │  │
│  │     should I / buy / sell / recommend /        │  │
│  │     better than / invest in / portfolio        │  │
│  │     → Polite refusal + educational link        │  │
│  │                                                │  │
│  │  3. Returns check — reject if query asks:      │  │
│  │     returns / CAGR / performance / compare     │  │
│  │     → "Please see official factsheet" + link   │  │
│  │                                                │  │
│  │  4. Pass → send to Retriever                   │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Output: { action: "answer" | "refuse",              │
│            reason?, refusal_link? }                  │
└──────────────────────────────────────────────────────┘
```

---

## 7. Project Folder Structure

```
hdfc-mf-faq-assistant/
│
├── config.yaml                  # Embedding model, vector DB, chunking config
├── .env                         # API keys, LLM provider selection
├── requirements.txt             # Python dependencies
├── README.md
│
├── data/
│   ├── raw/                     # Phase 1 output: scraped JSON files
│   │   ├── hdfc_amc_overview.json
│   │   ├── hdfc_large_cap.json
│   │   ├── hdfc_flexi_cap.json
│   │   ├── hdfc_elss.json
│   │   └── hdfc_mid_cap.json
│   │
│   └── chunks/                  # Phase 2 output: chunked JSON files
│       ├── hdfc_amc_overview_chunks.json
│       └── ...
│
├── chroma_store/                # Phase 3 output: persisted ChromaDB
│
├── pipeline/
│   ├── scraper.py               # Phase 1 — Data Loading
│   ├── chunker.py               # Phase 2 — Data Chunking
│   ├── embedder.py              # Phase 3 — Embedding & ChromaDB upsert
│   ├── retriever.py             # Phase 4 — Query embedding + retrieval
│   └── generator.py             # Phase 5 — LLM response generation
│
├── llm/
│   ├── base.py                  # LLM client interface
│   ├── groq_client.py           # Groq (primary)
│   ├── gemini_client.py
│   ├── openai_client.py
│   ├── anthropic_client.py
│   └── mistral_client.py
│
├── app/
│   ├── guard.py                 # Query Guard / Filter
│   ├── orchestrator.py          # RAG Orchestrator
│   └── ui.py                    # Chat UI (Gradio / Streamlit)
│
└── outputs/
    ├── sample_qa.md             # Deliverable: 5–10 sample Q&A
    └── sources.md               # Deliverable: source URL list
```

---

## 8. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| **Scraping** | Playwright (primary) / BeautifulSoup | JS-rendered pages need Playwright |
| **Chunking** | Custom Python logic | Table-aware + paragraph chunking |
| **Embedding** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, local inference |
| **Vector DB** | ChromaDB | Persisted locally at `./chroma_store` |
| **LLM (primary)** | Groq — `qwen/qwen3-8b` | Fast inference; model set in `.env` |
| **LLM (alternate)** | Gemini / OpenAI / Anthropic / Mistral | Switchable via `LLM_PROVIDER` in `.env` |
| **UI** | Gradio or Streamlit | Minimal chat interface |
| **Config** | `config.yaml` + `.env` | Fully config-driven |
| **Language** | Python 3.10+ | — |

---

## 9. Configuration Reference

### `config.yaml`

```yaml
data_sources:
  urls:
    - https://groww.in/mutual-funds/amc/hdfc-mutual-funds
    - https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
    - https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
    - https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
    - https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth

embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"

vector_db:
  provider: "chromadb"
  collection_name: "hdfc_mf_faq"
  persist_directory: "./chroma_store"
  top_k: 5

chunking:
  strategy: "auto"        # auto | paragraph | table | sentence
  chunk_size: 512
  chunk_overlap: 64
```

### `.env`

```env
# Primary LLM (groq | gemini | openai | anthropic | mistral)
LLM_PROVIDER=groq

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=qwen/qwen3-8b

GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
MISTRAL_API_KEY=your_mistral_api_key
```

---

## 10. Data Flow Summary

| Phase | Module | Input | Output | Storage |
|---|---|---|---|---|
| 1 — Load | `scraper.py` | 5 Groww URLs | Raw HTML/text + metadata | `data/raw/*.json` |
| 2 — Chunk | `chunker.py` | Raw JSON files | Chunk list with metadata | `data/chunks/*.json` |
| 3 — Embed | `embedder.py` | Chunk JSON | 384-dim vectors | ChromaDB (`chroma_store/`) |
| 4 — Retrieve | `retriever.py` | User query | Top-k chunks + source URLs | In-memory |
| 5 — Generate | `generator.py` | Query + chunks | ≤ 3-sentence answer + citation | Returned to UI |

---

## 11. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Same embedding model for ingestion and retrieval | `all-MiniLM-L6-v2` | Ensures vector space consistency; avoids retrieval drift |
| Explicit per-phase data persistence | JSON files + ChromaDB | Demo requirement — each stage must be inspectable |
| Config-driven LLM switching | `.env` + provider factory | Supports 5 providers without code changes |
| Table-aware chunking | One fact per chunk | MF data is tabular; point-lookup retrieval benefits from atomic chunks |
| System prompt refusal guard | Hard-coded in prompt | Prevents LLM from reasoning around the no-advice boundary |
| No PII acceptance | Guard layer check | Regulatory compliance + privacy |

---

## 12. Constraints & Mitigations

| Constraint | Risk | Mitigation |
|---|---|---|
| Groww uses JS rendering | `requests` returns empty content | Use Playwright with `page.wait_for_load_state("networkidle")` |
| Scheme data changes over time | Stale answers | Store `scraped_at` timestamp; display "Last updated from sources: {date}" in every answer |
| LLM hallucination | Answer not grounded in retrieved chunks | System prompt enforces "Answer ONLY from provided context"; no web search |
| No advice boundary crossing | LLM rewrites refusal | Advice check done at Guard layer before LLM is called |
| ChromaDB cold start | Empty collection on first run | Run `python pipeline/scraper.py && chunker.py && embedder.py` before starting the app |

---

*This architecture document is derived from PRD v1.0. Implementation details may be refined during development.*
