# HDFC Mutual Fund FAQ Assistant (RAG Demo)

An intelligent, grounded Retrieval-Augmented Generation (RAG) assistant designed to answer factual questions regarding HDFC Mutual Fund schemes strictly based on public documentation from Groww.in.

---

## Architecture Overview

```
User Query
   │
   ▼
[ Guardrails (PII / Advice / Returns Check) ]
   │
   ├──▶ Passed? ──▶ [ Dense Semantic Search (ChromaDB + all-MiniLM-L6-v2) ]
   │                       │
   │                       ▼
   │                [ Prompt Assembly + Grounding Context ]
   │                       │
   │                       ▼
   │                [ LLM Generation (Groq / Qwen 3.8-27B) ]
   │                       │
   │                       ▼
   │                [ Answer + Citations & Source URLs ]
   │
   └──▶ Failed? ──▶ [ Standard Guardrail Refusal Response ]
```

---

## Features

- **Strict Grounding**: Answers queries strictly from ingested scheme facts and public documents.
- **Safety & Compliance Guardrails**:
  - Automatically redacts/blocks sensitive PII (PAN, Aadhaar, phone numbers, emails).
  - Refuses investment advice or portfolio recommendations, redirecting to certified SEBI Registered Investment Advisors.
  - Refuses speculative return forecasts, referring users to official monthly factsheets.
- **Dual Chunking Strategy**:
  - `table_metric`: Fine-grained key-value fact extraction for metrics (Expense Ratio, Minimum SIP, Exit Load, Benchmark, Lock-in Period, AUM, Fund Manager).
  - `prose_window`: Sliding window (512 tokens, 64 overlap) for descriptive fund information.
- **Persistent Vector Store**: Uses ChromaDB with cosine similarity search.
- **Clean Interactive Web UI**: Built-in responsive web interface with real-time Q&A and suggested queries.

---

## Supported Mutual Fund Schemes

1. HDFC Large Cap Fund
2. HDFC Mid-Cap Opportunities Fund
3. HDFC Flexi Cap Fund
4. HDFC ELSS Tax saver Fund
5. HDFC Mutual Fund AMC Overview

---

## Project Structure

```
├── app/
│   ├── guard.py             # PII and intent safety guardrails
│   ├── orchestrator.py      # Query orchestration pipeline
│   ├── web_ui.py            # Standalone responsive web UI (port 7860)
│   └── ui.py                # Optional Gradio UI
├── pipeline/
│   ├── scraper.py           # Groww data scraper (with Next.js payload parsing)
│   ├── loader.py            # Schema validation and normalization
│   ├── chunker.py           # Dual-strategy chunking
│   ├── embedder.py          # SentenceTransformer vector embedding
│   ├── store.py             # ChromaDB vector DB inspector and validator
│   ├── retriever.py         # Cosine semantic retrieval
│   └── generator.py         # Grounded prompt and LLM response generator
├── llm/
│   ├── base.py              # LLM client interface and fallback logic
│   └── groq_client.py       # Groq API integration (Qwen 3.8-27B)
├── config.yaml              # Global configuration
├── requirements.txt         # Python dependencies
└── test_app.py              # End-to-end evaluation and guardrail test suite
```

---

## Setup & Running

### 1. Installation

```bash
git clone https://github.com/HarshaMdy/FAQ-assistant.git
cd FAQ-assistant
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

### 3. Pipeline Execution

Run the complete pipeline step-by-step:

```bash
# 1. Scrape official Groww scheme pages
python pipeline/scraper.py

# 2. Validate and clean raw data
python pipeline/loader.py

# 3. Chunk documents
python pipeline/chunker.py

# 4. Generate embeddings and store into ChromaDB
python pipeline/embedder.py
```

### 4. Launch the Web Interface

```bash
python app/web_ui.py
```
Open your browser and navigate to: `http://localhost:7860`

### 5. Run Tests

```bash
python test_app.py
```
