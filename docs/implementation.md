# Implementation guide (phase-wise)

**Product:** Mutual Fund FAQs — Facts-Only RAG Chatbot  
**Use with:** [PRD.md](./PRD.md), [Architecture.md](./Architecture.md)  
**Version:** 0.1  
**Date:** 1 October 2026

Use this file to drive Cursor **one phase at a time**. Do not ask it to “build the whole RAG app” in a single prompt. Each phase has a copy-paste prompt, files to touch, and a **Done when** checklist. Finish the checklist before starting the next phase.

---

## How to use this with Cursor

1. Open a **new agent chat** per phase (keeps context small).
2. Attach `@docs/PRD.md`, `@docs/Architecture.md`, and this file.
3. Paste **only** that phase’s prompt (section *Cursor prompt*).
4. When the agent says it is done, you run the **Done when** checks yourself (or ask Cursor to verify, then you confirm).
5. Commit after each phase if you are using git (`phase-0-scaffold`, etc.).

**Hard rule for every prompt:** ingestion and query stay separate modules. Never “just call Groq with the five URLs.”

---

## Global constraints (repeat in every phase)

| Rule | Detail |
| --- | --- |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` only (384-d), same model for chunks and questions |
| Vector DB | ChromaDB, persisted to disk; ingest once |
| LLM | Groq; `GROQ_API_KEY` in `.env`; never commit `.env` |
| Corpus | Public pages only; start with five HDFC seed URLs in the PRD |
| Answers | ≤3 sentences, one citation URL, `Last updated from sources:` |
| Policy | No advice, no PII storage, no computed/compared returns |
| Chunking | Do **not** invent chunk size until Phase 1 raw files exist and Phase 2 has written `docs/chunking.md` |

**Seed URLs**

| Category | Scheme | URL |
| --- | --- | --- |
| Large Cap | HDFC Large Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Flexi Cap | HDFC Equity Fund Direct Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| ELSS | HDFC ELSS Tax Saver Direct Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| Small Cap | HDFC Small Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| Hybrid | HDFC Balanced Advantage Fund Direct Growth | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

**Target layout** (create files only when the phase says so)

```
.env.example
.gitignore
requirements.txt
README.md
app/
  ingest.py
  query.py
  embedder.py
  guardrails.py
  ui.py
data/
  sources.csv
  raw/
  chunks.txt
chroma/          # gitignored
docs/
  PRD.md
  Architecture.md
  implementation.md
  chunking.md    # Phase 2
  sample_qa.md   # Phase 6
```

---

## Phase map

| Phase | Name | Pipeline stage | Depends on |
| --- | --- | --- | --- |
| 0 | Scaffold | — | — |
| 1 | Load | Load | 0 |
| 2 | Chunk | Chunk | 1 (raw files on disk) |
| 3 | Embed + store | Embed → Store | 2 (`chunks.txt` + `chunking.md`) |
| 4 | Retrieve + generate | Question → Embed → Retrieve → Groq | 3 (Chroma on disk) + Groq key |
| 5 | Guardrails | Pre-retrieve policy | 4 |
| 6 | Tiny UI + submit pack | UI + README + sample Q&A | 5 |

Do not skip Phase 1 → 2. Chunking must follow real page inspection.

---

## Phase 0 — Scaffold

**Goal:** Empty app that installs, ignores secrets, and does not crawl or call APIs yet.

### Do

- Python project with `requirements.txt` (pin later when you add libs; for now list intended deps: `sentence-transformers`, `chromadb`, `groq`, `python-dotenv`, `beautifulsoup4`, `requests`, `streamlit`, `lxml`).
- `.gitignore`: `.env`, `chroma/`, `__pycache__/`, `.venv/`, maybe `data/raw/` if pages are huge (keep `data/sources.csv` and `data/chunks.txt` committable).
- `.env.example` with `GROQ_API_KEY=`
- Stub files: `app/ingest.py`, `app/query.py`, `app/embedder.py` with a one-line docstring each, `if __name__` that prints “not implemented”.
- Short `README.md` placeholder: product name, “see docs/”, how to create venv (no fake setup that does not work).

### Do not

- Fetch URLs
- Download the MiniLM model in this phase unless you are only adding it to requirements
- Write chunk sizes
- Build Streamlit UI

### Cursor prompt

```
Read @docs/PRD.md @docs/Architecture.md @docs/implementation.md

Implement Phase 0 only (Scaffold).

Create the target layout from implementation.md: .gitignore, .env.example, requirements.txt, README placeholder, and stub modules under app/ (ingest.py, query.py, embedder.py) that print not implemented.

Do not fetch web pages, do not add chunking logic, do not call Groq, do not create Streamlit UI.

Stop when Phase 0 Done when is satisfied. List the files you created.
```

### Done when

- [ ] `python -c "import app"` or running stubs does not error
- [ ] `.env` is gitignored; `.env.example` has `GROQ_API_KEY`
- [ ] No network calls in code
- [ ] README says HDFC facts-only RAG demo and points at `docs/`

---

## Phase 1 — Load (ingestion stage 1)

**Goal:** Five seed pages (and only extra **official** pages you choose) saved locally with metadata. No chunking.

### Do

- `data/sources.csv` columns: `url,scheme_name,category,doc_type,fetched_at,title`
- `data/raw/` one file per source (txt or html) plus a small JSON/sidecar if needed
- `app/ingest.py` CLI: `python -m app.ingest --load-only` (or `python app/ingest.py --load-only`) that:
  - fetches the five seed URLs
  - strips obvious nav/boilerplate if easy; keep the scheme facts
  - writes `fetched_at` as ISO date
- User-Agent string; handle HTTP errors without crashing the whole run
- Print a summary: N docs saved, paths

### Do not

- Chunk, embed, or open Chroma
- Use blogs as extra sources
- Store screenshots or authenticated pages
- Call Groq

**If Groww blocks scraping:** save the HTML you can get, and/or add official HDFC AMC factsheet/KIM URLs to `sources.csv` and load those. Log every URL. Prefer AMC/SEBI/AMFI when the same fact exists.

### Cursor prompt

```
Read @docs/PRD.md @docs/Architecture.md @docs/implementation.md

Implement Phase 1 only (Load).

Fetch the five HDFC seed URLs from the PRD. Save cleaned text under data/raw/ and a data/sources.csv with url, scheme_name, category, doc_type, fetched_at, title.

Add a --load-only path on app/ingest.py. Do not chunk, embed, or write to Chroma. Do not call Groq.

If a page fails, retry once, then record the error and continue. After the run, print how many documents were saved.

Stop when Phase 1 Done when is satisfied. Show me a sample of one raw file (first 40 lines) so I can inspect quality.
```

### You do after Cursor

Open `data/raw/` and skim: do expense ratio, SIP, exit load, riskometer, benchmark, lock-in actually appear? If not, add official factsheet URLs and re-run load **before** Phase 2.

### Done when

- [ ] Five rows minimum in `sources.csv`
- [ ] Matching files in `data/raw/`
- [ ] `fetched_at` filled
- [ ] You can grep raw files for at least: expense, SIP, exit load, lock-in (ELSS)
- [ ] No embeddings / chroma directory required yet

---

## Phase 2 — Chunk (ingestion stage 2)

**Goal:** Document a chunking strategy from **real** raw files, then implement it and dump `data/chunks.txt`.

### Do first (before more code)

Inspect `data/raw/`. Write `docs/chunking.md` with:

- What the pages look like (FAQ blocks vs long tables vs SID walls of text)
- Chunk size (characters or tokens — pick one)
- Overlap
- Why this fits **this** corpus
- Metadata per chunk: `source_url`, `scheme_name`, `category`, `fetched_at`, optional `section`

**Suggested starting point if pages are scheme factsheets / Groww-style sections:** ~500–800 characters, ~100 overlap, split on headings (`##`, `h2`, bold labels) when present, then fall back to sliding window. **Cursor must confirm or revise after reading the files, not copy this blindly.**

### Then implement

- Chunker used by `app/ingest.py --chunk-only` (reads `data/raw/` + `sources.csv`, does not re-fetch unless files missing)
- `data/chunks.txt` human-readable, e.g.

```
--- chunk_id: largecap-0003
scheme_name: HDFC Large Cap Fund
category: Large Cap
source_url: https://...
fetched_at: 2026-10-01
section: Expense ratio
---
<text>
```

### Do not

- Embed or write Chroma yet
- Change load logic except small bugfixes
- Call Groq

### Cursor prompt

```
Read @docs/PRD.md @docs/Architecture.md @docs/implementation.md

Implement Phase 2 only (Chunk).

First inspect every file in data/raw/ and data/sources.csv. Write docs/chunking.md: describe the data, propose chunk size, overlap, and metadata, and explain why it fits. Do not invent a strategy without citing what you saw in the files.

Then implement chunking in the ingest pipeline as --chunk-only. Write all chunks to data/chunks.txt in a readable format with chunk_id and required metadata (source_url, scheme_name, category, fetched_at, optional section).

Do not embed. Do not use Chroma. Do not call Groq.

Stop when Phase 2 Done when is satisfied. Quote the chosen size/overlap in your summary.
```

### Done when

- [ ] `docs/chunking.md` exists and references actual page structure
- [ ] `data/chunks.txt` exists and is readable in an editor
- [ ] Chunks keep scheme identity (Large Cap text is not mixed with ELSS without metadata)
- [ ] You spot-check 3 chunks: they are coherent, not half a word, not an entire 20-page SID as one chunk

---

## Phase 3 — Embed + store (ingestion stages 3–4)

**Goal:** MiniLM embeddings in a **persisted** ChromaDB. Ingest rebuilds the collection from chunks; UI will not ingest later.

### Do

- `app/embedder.py`: load `sentence-transformers/all-MiniLM-L6-v2`, function `embed_texts(list[str]) -> list[list[float]]` (384-d)
- `app/ingest.py` default or `--embed-store`: read `chunks.txt` (or in-memory chunks), embed, upsert into Chroma persist dir `chroma/`
- Collection name e.g. `hdfc_mf_faqs`
- Rebuild collection each full ingest (delete + create) so reruns are not duplicated
- Document cosine vs default distance in a comment or README
- `python app/ingest.py` can run load → chunk → embed → store as the **full** ingest; keep `--load-only` and `--chunk-only` working

### Do not

- Call Groq
- Embed inside the future UI on startup
- Use a different embedding model
- Commit the `chroma/` folder

### Cursor prompt

```
Read @docs/PRD.md @docs/Architecture.md @docs/implementation.md docs/chunking.md

Implement Phase 3 only (Embed + Store).

Use sentence-transformers/all-MiniLM-L6-v2 in app/embedder.py for all embeddings. Read data/chunks.txt, embed each chunk, store in ChromaDB persisted at ./chroma with metadata from each chunk.

Full ingest: Load → Chunk → Embed → Store. Keep --load-only and --chunk-only. Rebuilding the collection must be idempotent (no duplicate chunks on rerun).

Do not call Groq. Do not build the UI. Do not change the embedding model.

After ingest, print collection count and embedding dimension (must be 384).
```

### Done when

- [ ] `chroma/` exists after one ingest
- [ ] Second ingest does not double the count
- [ ] Collection count equals number of chunks (or you document why not)
- [ ] Restarting Python still sees the collection **without** re-embedding if you only query (verify in Phase 4; here at least persist dir is non-empty)
- [ ] First MiniLM download may take time; that is expected

---

## Phase 4 — Retrieve + generate (query pipeline)

**Goal:** CLI or function: question in → grounded answer out. No UI polish, no guardrails yet (optional stub).

### Do

- `app/query.py`:
  1. Embed question with **same** `embedder.py`
  2. Query Chroma top-k (start `k=4`)
  3. If empty / below a similarity threshold → `not_found` + seed URL for named scheme if parsed
  4. Else call Groq with system prompt: facts-only, ≤3 sentences, only use context, one citation from metadata, no advice, no invented numbers
  5. Return structured result: `text`, `citation_url`, `last_updated` (from chunk `fetched_at`)
- Load `.env` via `python-dotenv`
- CLI: `python -m app.query "What is the lock-in for HDFC ELSS Tax Saver?"`
- Print retrieved chunk ids in debug mode (`--debug`) so you can show RAG in class

### Do not

- Streamlit yet
- Re-run ingest on import of `query.py`
- Answer from model memory if retrieval is empty
- Compare or compute returns even if the user asks (minimal: system prompt only; Phase 5 hardens this)

### Cursor prompt

```
Read @docs/PRD.md @docs/Architecture.md @docs/implementation.md

Implement Phase 4 only (Retrieve + Generate).

Add app/query.py. On each question: embed with the same MiniLM embedder, retrieve top-k from the persisted Chroma collection, then Groq using only retrieved chunk text. GROQ_API_KEY from .env.

Answers: max 3 sentences, exactly one citation URL from chunk metadata, line "Last updated from sources: <date>". If retrieval is empty or low-confidence, say the fact is not in the corpus and do not invent numbers.

CLI for one question. --debug prints chunk ids and source URLs.

Do not add Streamlit. Do not run ingest on query. Do not implement full PII/advice guardrails yet (system prompt may mention facts-only).

Test with: expense ratio of HDFC Large Cap, ELSS lock-in, minimum SIP of Small Cap. Show me the three outputs.
```

### You do

Put `GROQ_API_KEY` in `.env` before running. Never paste the key into chat.

### Done when

- [ ] Three in-scope questions return short answers + links
- [ ] `--debug` shows chunks, not just the final sentence
- [ ] Killing and restarting Python still answers **without** ingest
- [ ] Nonsense question yields not-in-corpus, not a hallucinated ratio

---

## Phase 5 — Guardrails

**Goal:** Policy runs **before** retrieve for disallowed intents. Defense in depth in the Groq prompt remains.

### Do

- `app/guardrails.py` → `{action: allow|refuse_advice|refuse_performance|refuse_pii, message, citation_url}`
- Detect:
  - PII: PAN, Aadhaar, account numbers, OTP, email, phone (do not write matches to disk)
  - Advice: should I buy/sell/switch, best fund, for me, allocate
  - Performance: returns, CAGR, outperformed, which is better (performance)
- `query.py` short-circuits on refuse
- Refusal copy: polite, facts-only, **one educational official link** (AMFI/SEBI investor ed or scheme SID/KIM from sources)
- Performance: do not compute; point at factsheet URL if scheme known, else generic official factsheet/AMFI link from `sources.csv`

### Do not

- Store the user message if PII detected (log only “pii_blocked”)
- Soften refusals into partial advice
- Skip retrieval for normal fact questions

### Cursor prompt

```
Read @docs/PRD.md @docs/Architecture.md @docs/implementation.md

Implement Phase 5 only (Guardrails).

Add app/guardrails.py and call it at the start of query.py before embed/retrieve.

Refuse: investment advice, return computation/comparison, and PII (PAN, Aadhaar, account, OTP, email, phone). Do not save PII. Refusals are polite, facts-only, with one official educational or factsheet link.

Keep Phase 4 behaviour for normal factual questions.

Add a few assertions or a tiny script tests/test_guardrails.py for: "should I buy HDFC large cap?", "which fund gave higher returns?", a fake PAN, and "expense ratio of HDFC Large Cap".

Do not build the UI in this phase.
```

### Done when

- [ ] Buy/sell → refusal + link
- [ ] “Which performed better?” → no numbers invented; factsheet pointer
- [ ] PII sample → refusal; nothing written under `data/`
- [ ] Expense-ratio question still works

---

## Phase 6 — Tiny UI + submission pack

**Goal:** Class-demo UI and milestone deliverables.

### Do

- `app/ui.py` Streamlit (or equivalent, keep tiny):
  - Welcome line
  - Persistent: **Facts-only. No investment advice.**
  - Full disclaimer from PRD §6.3
  - 3 clickable example questions (PRD §6.2)
  - Chat input; show answer body, citation, last-updated
  - Calls `query.py` only; **does not ingest on load**
- README (replace placeholder): setup (venv, `pip install`, `.env`, `python app/ingest.py` once, `streamlit run app/ui.py`), AMC + five schemes, known limits (PRD §13), architecture one-liner (two pipelines)
- `docs/sample_qa.md`: 5–10 real queries with **actual** assistant outputs + links (run them; do not fabricate)
- Confirm `data/sources.csv` is the submitted source list
- Disclaimer visible in UI

### Do not

- Auto-ingest on every page refresh
- User accounts, history DB, analytics
- Extra features (dark mode, multi-AMC, streaming) unless leftover time

### Cursor prompt

```
Read @docs/PRD.md @docs/Architecture.md @docs/implementation.md

Implement Phase 6 only (Tiny UI + submit pack).

Build a tiny Streamlit UI in app/ui.py: welcome, three example questions, disclaimer "Facts-only. No investment advice.", chat that calls existing query.py. Do not run ingest on UI load.

Rewrite README with setup, HDFC + five schemes, known limits, and that RAG is Load→Chunk→Embed→Store then Question→Embed→Retrieve→Groq.

Run the query pipeline for 5–10 questions and write docs/sample_qa.md with real answers and citation links (in-scope facts plus at least one advice refusal).

Do not add new product features. Do not commit .env or chroma/.
```

### Done when (demo checklist)

- [ ] UI matches PRD tiny UI
- [ ] Ingest once; restart UI; answers still work
- [ ] `chunks.txt` inspectable
- [ ] Sample Q&A is real output
- [ ] README + sources + disclaimer done
- [ ] `.env` / `chroma/` not in git

---

## Optional Phase 7 — Demo polish (if time)

Only after Phase 6 checklist is green.

- Host Streamlit Cloud / similar **or** record ≤3-min video: show `chunks.txt`, Chroma persist, one fact, one refusal
- Tune `k` and similarity threshold if citations are wrong
- Prefer citing AMC factsheet URL over Groww when both chunks appear
- Add architecture diagram from `Architecture.md` into README

---

## Suggested Cursor workflow (copy)

```
You are implementing a class-demo RAG chatbot.
Follow @docs/implementation.md strictly.
Current phase: PHASE_N_NAME
Do not start the next phase.
Cite @docs/PRD.md and @docs/Architecture.md for product and pipeline rules.
```

Replace `PHASE_N_NAME` with e.g. `Phase 1 Load`.

---

## If the agent drifts

| Symptom | What to say |
| --- | --- |
| Calls Groq with live URLs | “Stop. Query must retrieve from Chroma only.” |
| Chunks in Phase 1 | “Load-only. Chunking is Phase 2 after inspecting data/raw.” |
| New embedding model | “Use all-MiniLM-L6-v2 only.” |
| Ingest on Streamlit start | “UI must read persisted Chroma; ingest is a separate CLI.” |
| Advice-ish answers | “Add/fix Phase 5 guardrails; never recommend buy/sell.” |
| Invents expense ratios | “If retrieval is weak, return not_found; do not use model memory.” |

---

## Phase completion log (for you)

| Phase | Date done | Notes |
| --- | --- | --- |
| 0 Scaffold | | |
| 1 Load | | Raw quality OK? |
| 2 Chunk | | Size / overlap: |
| 3 Embed + store | | Collection count: |
| 4 Retrieve + generate | | Groq model: |
| 5 Guardrails | | |
| 6 UI + submit pack | | |
