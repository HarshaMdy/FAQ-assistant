# Product Requirements Document (PRD)
## HDFC Mutual Fund FAQ Assistant (RAG Demo)

**Version:** 1.0  
**Date:** 2026-11-01  
**Platform:** Groww App Integration  
**Type:** Prototype / Demo

---

## 1. Overview

A small, facts-only FAQ assistant that answers queries about HDFC Mutual Fund schemes using official public pages from Groww. This is a **RAG (Retrieval-Augmented Generation) demo** built to showcase each pipeline stage explicitly — from data loading to LLM response generation.

> **Disclaimer:** This assistant provides factual information only. It does not offer investment advice.

---

## 2. Problem Statement

Retail investors frequently have repetitive factual questions about mutual fund schemes (expense ratios, exit loads, SIP minimums, ELSS lock-ins, etc.) that are publicly available but scattered across different scheme pages. Support and content teams spend time answering these repetitive questions manually.

---

## 3. Target Users

| User Type | Need |
|---|---|
| Retail investors | Compare schemes on factual parameters |
| Support teams | Deflect repetitive MF factual queries |
| Content teams | Reference accurate, sourced MF information |

---

## 4. Goals

- Build a working RAG prototype that answers factual mutual fund queries.
- Demonstrate each RAG stage explicitly (loading → chunking → embedding → retrieval → generation).
- Cite one official source link in every answer.
- Refuse opinionated / portfolio advice queries politely.

---

## 5. Scope

### 5.1 Data Sources (Groww Public Pages Only)

| # | Fund Type | Fund Name | URL |
|---|---|---|---|
| 1 | AMC Overview | HDFC Mutual Fund | https://groww.in/mutual-funds/amc/hdfc-mutual-funds |
| 2 | Large Cap | HDFC Large Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| 3 | Flexi Cap | HDFC Flexi Cap Direct Plan Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| 4 | ELSS (Tax Saver) | HDFC ELSS Tax Saver Fund Direct Plan Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| 5 | Mid Cap | HDFC Mid Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth |

### 5.2 Answerable Query Types

- Expense ratio
- Exit load
- Minimum SIP amount
- ELSS lock-in period
- Riskometer / Risk level
- Benchmark index
- How to download capital-gains / account statement

### 5.3 Out of Scope

- Buy / sell recommendations
- Performance comparisons or return calculations
- Any query requiring PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers
- Third-party blog sources or screenshots of app back-end

---

## 6. Functional Requirements

### 6.1 RAG Pipeline (Phase-wise)

The system must expose each pipeline stage explicitly for demo purposes.

#### Phase 1 — Data Loading
- Scrape the 5 Groww public pages listed in §5.1.
- Store raw scraped content persistently (file / DB).
- Log source URL and scrape timestamp for each page.

#### Phase 2 — Data Chunking
- Apply a chunking strategy suited to the scraped content structure.
- Chunking strategy is determined by the AI coding agent based on content type (e.g., table-aware chunking for scheme data, paragraph chunking for descriptive text).
- Store chunks explicitly with metadata: `source_url`, `chunk_id`, `chunk_text`.

#### Phase 3 — Data Embedding
- Embed each chunk using **`sentence-transformers/all-MiniLM-L6-v2`**.
- Store embeddings in **ChromaDB**.
- Embedding model and vector DB must be configurable via a **config file**.

#### Phase 4 — Data Retrieval
- Use the **same embedding model** as ingestion for query encoding.
- Query **ChromaDB** to retrieve top-k relevant chunks.
- Return retrieved chunks with their source URLs.

#### Phase 5 — LLM Response Generation
- Pass retrieved chunks + user query to the configured LLM.
- LLM selection configurable via **`.env`** file.
- Supported LLM providers:

| Provider | Model / Notes |
|---|---|
| **Groq** *(primary)* | `qwen/qwen3-8b` — model name read from `.env` |
| Gemini | Configurable |
| OpenAI | Configurable |
| Anthropic | Configurable |
| Mistral | Configurable |

### 6.2 FAQ Assistant Behavior

| Condition | Behavior |
|---|---|
| Factual query match | Answer in ≤ 3 sentences + 1 citation link |
| Opinionated / advice query | Politely refuse + link to official factsheet/educational resource |
| Any query | Show "Last updated from sources: `<date>`" |

### 6.3 UI Requirements

- **Welcome line** introducing the assistant.
- **3 example questions** shown on load (e.g., *"What is the expense ratio of HDFC Large Cap Fund?"*, *"What is the ELSS lock-in period?"*, *"What is the minimum SIP for HDFC Mid Cap?"*).
- **Disclaimer note:** *"Facts-only. No investment advice."*
- Input box for free-text queries.
- Response area showing answer + citation link.

---

## 7. Non-Functional Requirements

| Requirement | Detail |
|---|---|
| **Public sources only** | No app back-end screenshots; no third-party blogs |
| **No PII** | Do not accept or store PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers |
| **No performance claims** | Do not compute or compare returns; link to official factsheet if asked |
| **Answer length** | ≤ 3 sentences per answer |
| **Transparency** | Each answer includes `"Last updated from sources: <date>"` |
| **Configurability** | Embedding model, vector DB, and LLM are all config/env-driven |

---

## 8. Configuration Design

### `config.yaml` (or equivalent)
```yaml
embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"

vector_db:
  provider: "chromadb"
  collection_name: "hdfc_mf_faq"
  persist_directory: "./chroma_store"

chunking:
  strategy: "auto"   # AI coding agent decides based on content type
  chunk_size: 512
  chunk_overlap: 64
```

### `.env`
```env
# LLM Provider (groq | gemini | openai | anthropic | mistral)
LLM_PROVIDER=groq

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=qwen/qwen3-8b

# Gemini
GEMINI_API_KEY=your_gemini_api_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key

# Mistral
MISTRAL_API_KEY=your_mistral_api_key
```

---

## 9. Deliverables

| # | Deliverable | Format |
|---|---|---|
| 1 | Working prototype | App / Notebook / ≤ 3-min demo video |
| 2 | Source list | CSV or MD (15–25 URLs used) |
| 3 | README | Setup steps, scope, known limits |
| 4 | Sample Q&A file | 5–10 queries with answers + citation links |
| 5 | Disclaimer snippet | Text used in the UI |

---

## 10. Skills Being Evaluated

| Skill | Description |
|---|---|
| **W1 — Thinking Like a Model** | Identify the exact fact asked; decide answer vs. refuse |
| **W2 — LLMs & Prompting** | Instruction style, concise phrasing, polite safe-refusals, citation wording |
| **W3 — RAG (Only)** | Small-corpus retrieval with accurate citations from AMC/SEBI/AMFI pages |

---

## 11. Architecture Diagram

```
User Query
    │
    ▼
[Query Embedding]  ←── sentence-transformers/all-MiniLM-L6-v2
    │
    ▼
[Vector Retrieval] ←── ChromaDB
    │
    ▼
[Retrieved Chunks + Source URLs]
    │
    ▼
[LLM Generation]  ←── Groq (qwen/qwen3-8b) / Gemini / OpenAI / Anthropic / Mistral
    │
    ▼
[Answer ≤ 3 sentences + 1 Citation Link + Last Updated]
```

---

## 12. Known Constraints & Risks

| Constraint | Notes |
|---|---|
| Groww pages may use JavaScript rendering | May require Selenium/Playwright instead of simple requests |
| Scheme data can change | Scrape timestamp must be shown; consider re-scrape schedule |
| LLM hallucination | Retrieval must be grounded; answers must strictly cite retrieved chunks |
| No advice boundary | Prompt must include explicit system-level refusal instructions |

---

*This PRD is generated from the project problem statement. All scope and constraints are as specified by the team.*
