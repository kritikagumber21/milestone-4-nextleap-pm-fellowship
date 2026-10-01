# Product Requirements Document

**Product:** Mutual Fund FAQs — Facts-Only RAG Chatbot  
**Audience:** Class demo (NextLeap / PM School, Module 4)  
**Version:** 0.1  
**Date:** 1 October 2026  
**Status:** Draft for implementation

---

## 1. Summary

Build a small **Retrieval-Augmented Generation (RAG)** FAQ assistant that answers **factual** questions about a fixed set of HDFC mutual fund schemes using **only official public pages**. Every answer must include **one source link**. The product must not give investment advice.

This is a working class-demo prototype: a tiny chat UI on top of a two-stage RAG pipeline (**data ingestion** + **data retrieval / generation**).

---

## 2. Problem

Retail investors and support/content teams repeatedly ask the same scheme facts: expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer, benchmark, and how to download statements.

Today those answers live across factsheets, KIM/SID, FAQs, and fee pages. People either guess from unofficial blogs or get mixed with “should I buy?” advice.

**Job to be done:** “When I have a factual question about an HDFC scheme, give me a short, sourced answer from official public pages — and refuse advice.”

---

## 3. Goals and non-goals

### Goals

| ID | Goal | Success signal |
| --- | --- | --- |
| G1 | Answer in-scope factual queries from retrieved corpus chunks, not from model memory | Sample Q&A file: 5–10 queries with citations |
| G2 | Cite one clear source URL on every answer | 100% of successful answers include a link |
| G3 | Refuse opinion / buy-sell / portfolio questions | Polite facts-only refusal + educational link |
| G4 | Demonstrate the full RAG path on stage, not a black-box chatbot | Ingestion and query pipelines are separable and inspectable |
| G5 | Stay compliant with demo constraints | No PII, no performance claims, public sources only |

### Non-goals (explicit)

- Investment advice, suitability, “best fund,” or buy/sell recommendations
- Return calculation, ranking, or comparison of performance
- Account login, KYC, transactions, or statement generation (only **how to** from public guides)
- Multi-AMC coverage, live price feeds, or real-time NAV dashboards
- User accounts, conversation history across sessions, or analytics
- Screenshots or content from any app back-end
- Third-party blogs as citation sources

---

## 4. Users

| Persona | Need | How the demo serves them |
| --- | --- | --- |
| Retail user comparing schemes | Fast facts (fees, lock-in, SIP min, riskometer) | Short answers + one official link |
| Support / content teammate | Repeat FAQ deflection | Same facts-only replies with citations |
| Instructor / classmates | See RAG stages, not a magic LLM | Chunks on disk, persisted ChromaDB, Groq generation |

---

## 5. Scope

### 5.1 AMC and schemes

**AMC:** HDFC Mutual Fund (via the public scheme pages listed below).

| Category | Scheme (Direct – Growth) | Seed URL |
| --- | --- | --- |
| Large Cap | HDFC Large Cap Fund | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Flexi Cap | HDFC Equity Fund (Flexi Cap) | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| ELSS | HDFC ELSS Tax Saver | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| Small Cap | HDFC Small Cap Fund | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| Hybrid | HDFC Balanced Advantage Fund | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

**Corpus rule:** Those five URLs are the **starting** seed list. The assistant may ingest additional **official public** pages they point to (AMC/SEBI/AMFI factsheets, KIM/SID, scheme FAQs, fee/charges, riskometer/benchmark notes, statement/tax-doc guides). **Do not** use unofficial blogs as sources.

Submit a **source list** (CSV or Markdown) of the URLs actually used (at least the five seeds).

### 5.2 Question types in scope

- Expense ratio
- Exit load
- Minimum SIP / minimum investment
- ELSS lock-in
- Riskometer
- Benchmark
- How to download statements / capital-gains / tax documents (procedural facts from official guides)

### 5.3 Question types out of scope (refuse)

- “Should I buy / sell / switch?”
- Portfolio construction, asset allocation, “best for me”
- Predicted or computed returns; “which fund performed better?”
- Anything requiring PAN, Aadhaar, account numbers, OTP, email, or phone

---

## 6. Product experience

### 6.1 Tiny UI (must-have)

- Welcome line
- **3 example questions** (clickable or copyable)
- Persistent note: **“Facts-only. No investment advice.”**
- Chat input + answer area
- Each answer shows:
  - ≤ **3 sentences** of facts
  - **One citation link**
  - **Last updated from sources:** `<date>`
- Refusal copy for advice/PII/performance asks (polite, facts-only, with a relevant **educational** official link)

### 6.2 Example starter questions (suggested)

1. What is the expense ratio of HDFC Large Cap Fund (Direct Growth)?
2. What is the lock-in for HDFC ELSS Tax Saver?
3. What is the minimum SIP for HDFC Small Cap Fund?

### 6.3 Disclaimer snippet (deliverable)

Use in the UI (and README):

> Facts-only. This assistant summarises publicly available scheme information and is **not investment advice**. It does not recommend buying, selling, or holding any mutual fund. Check the official factsheet / SID / KIM before you act. Sources can change; see “Last updated from sources.”

---

## 7. Functional requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F1 | Load the scoped public pages into a local corpus | P0 |
| F2 | Chunk documents with a documented strategy; write all chunks to a readable `.txt` for inspection | P0 |
| F3 | Embed chunks with `sentence-transformers/all-MiniLM-L6-v2` (384-d, local, no API key) | P0 |
| F4 | Persist embeddings in **ChromaDB on disk** (ingest once; reuse on restart) | P0 |
| F5 | On query: embed the question with the **same** model, retrieve top-k chunks, generate with **Groq** | P0 |
| F6 | Ground answers in retrieved chunks; include **one** source URL | P0 |
| F7 | Cap answers at **3 sentences**; append last-updated line | P0 |
| F8 | Detect and refuse advice, performance-comparison, and PII requests | P0 |
| F9 | If asked for returns: do not compute; point to the official factsheet link | P0 |
| F10 | Do not accept or store PAN, Aadhaar, account numbers, OTPs, emails, or phones | P0 |
| F11 | Groq API key in `.env` only; never commit secrets | P0 |
| F12 | README: setup, AMC + scheme scope, known limits | P0 |
| F13 | Sample Q&A file (5–10 queries with answers + links) | P0 |

---

## 8. RAG architecture (class requirement)

Each stage must be **distinct** in the architecture (code modules and, if useful, a simple diagram in the README). Do not collapse “call the LLM with URLs” into a single step.

### 8.1 Ingestion (offline / run once)

```
Load → Chunk → Embed → Store in Vector DB
```

| Stage | What happens |
| --- | --- |
| **Load** | Fetch / save public pages for the 5 schemes (+ official linked docs). Keep URL + title + fetch date as metadata. |
| **Chunk** | Split into retrieval units. Strategy is **data-driven** (see 8.3). Persist all chunks to a human-readable `.txt`. |
| **Embed** | `sentence-transformers/all-MiniLM-L6-v2` → 384-dimension vectors for every chunk. |
| **Store** | Insert into **ChromaDB**, persisted to disk. |

### 8.2 Query (online / every question)

```
Question → Embed → Retrieve top chunks → LLM (Groq) → Answer
```

| Stage | What happens |
| --- | --- |
| **Question** | User text from the tiny UI. Guardrails: PII, advice, performance. |
| **Embed** | Same MiniLM model as ingestion. |
| **Retrieve** | Top-k similar chunks from ChromaDB (include metadata: source URL, scheme, section). |
| **LLM** | Groq generates a ≤3-sentence facts-only answer **only** from retrieved text. |
| **Answer** | Body + one citation + “Last updated from sources: …” |

### 8.3 Chunking strategy (agent decides before coding)

Before implementation, inspect the loaded pages and **propose** a strategy in writing (README or `docs/chunking.md`):

- Why it fits this data (factsheets / FAQ-style pages vs long SID)
- Chunk size
- Overlap
- Metadata kept on each chunk (at minimum: `source_url`, `scheme_name`, `category`, `fetched_at`; optionally heading / section)

Then implement that strategy and dump chunks to `.txt` so they can be inspected in the demo.

---

## 9. Technical constraints

| Item | Constraint |
| --- | --- |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (local, 384-d) |
| Vector DB | ChromaDB, disk persistence |
| LLM | Groq; key in `.env` |
| Sources | Public pages only; no app back-end screenshots; no third-party blogs as citations |
| Hosting | Working prototype link **or** ≤3-minute demo video if hosting is not possible |

Suggested (not mandated by the brief) stack for a class demo: Python ingestion + retrieval scripts, a small web UI (Streamlit or similar), `python-dotenv` for Groq.

---

## 10. Guardrails and answer policy

1. **Grounding:** If retrieval is empty or low-confidence, say you don’t have that fact in the corpus and link the relevant seed scheme page — do not invent numbers.
2. **Citations:** Exactly one primary link per answer (the best matching official URL from chunk metadata).
3. **Length:** ≤3 sentences of answer text, then citation + last-updated.
4. **Advice:** Refuse; offer a facts-only educational link (e.g. AMFI / SEBI investor education or the scheme’s SID/KIM).
5. **Performance:** Never compute or compare returns; link the official factsheet.
6. **PII:** If the user pastes identifiers, do not store them; tell them the bot cannot use personal data and they should use the AMC’s official channels.

---

## 11. Deliverables (what to submit)

| # | Artifact |
| --- | --- |
| 1 | Working prototype (app/notebook URL) **or** ≤3-min demo video |
| 2 | Source list (CSV/MD) of URLs used (the 5 seeds + any extra official pages) |
| 3 | README: setup, scope (AMC + schemes), known limits |
| 4 | Sample Q&A file (5–10 queries, answers, links) |
| 5 | Disclaimer snippet used in the UI |
| 6 | Inspectable chunks `.txt` (implementation requirement for the RAG demo) |
| 7 | Architecture that separates ingestion vs retrieval stages |

---

## 12. Success criteria (demo checklist)

- [ ] Ingestion can be run once; app restart still answers from persisted ChromaDB
- [ ] Chunks file exists and is readable
- [ ] Same embedding model used for documents and questions
- [ ] In-scope questions (expense ratio, lock-in, SIP, exit load, riskometer/benchmark, statement how-to) return short, cited answers
- [ ] Advice questions are refused
- [ ] Returns questions are not computed; factsheet linked
- [ ] UI shows welcome, 3 examples, and “Facts-only. No investment advice.”
- [ ] No secrets in git; `.env` documented in README

---

## 13. Known limits (to state in README)

- Corpus is **HDFC only**, five Direct-Growth schemes, snapshot of public pages
- Groww scheme pages are **public web pages**; prefer citing AMC/SEBI/AMFI documents when the same fact appears there
- Numbers can go stale after the fetch date
- Retrieval quality depends on chunking; SID/KIM PDFs may be noisier than FAQ/factsheet HTML
- Groq and embedding model can still hallucinate if the prompt is weak — policy is **refuse rather than guess**

---

## 14. Open decisions (implementation)

| Topic | Owner | Notes |
| --- | --- | --- |
| Chunk size / overlap / metadata | Engineering (after inspecting data) | Document before writing ingestion code |
| Top-k and similarity threshold | Engineering | Tune so answers stay grounded |
| Groq model name | Engineering | Pick a current Groq chat model; record in README |
| UI framework | Engineering | Keep the UI tiny |
| Extra official URLs beyond the 5 seeds | Product + eng | Log every URL in the source list |

---

## 15. Out of scope for later (not this demo)

- More AMCs / all HDFC schemes
- Auth, ticket deflection in production CRM
- Streaming tokens, multi-turn memory, or agent tools (web search at query time)
- Automated daily recrawl of factsheets
