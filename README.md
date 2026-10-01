# Mutual Fund FAQs — Facts-Only RAG Chatbot

A class-demo HDFC mutual fund FAQ assistant that answers only in-scope factual questions from a local corpus of public scheme pages.

## Product scope

- AMC: HDFC Mutual Fund
- Schemes covered: HDFC Large Cap Fund Direct Growth, HDFC Equity Fund Direct Growth, HDFC ELSS Tax Saver Fund Direct Plan Growth, HDFC Small Cap Fund Direct Growth, HDFC Balanced Advantage Fund Direct Growth
- Policy: facts-only; no investment advice; no PII storage; no computed or compared returns

See the docs folder for the PRD, architecture, and implementation plan: `docs/PRD.md`, `docs/Architecture.md`, and `docs/implementation.md`.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.ingest --load-only
python3 -m app.ingest --chunk-only
python3 -m app.ingest --embed-store
```

Create a local `.env` from `.env.example` and add your `GROQ_API_KEY`.

## Architecture

The project follows two pipelines:

- Ingestion: Load → Chunk → Embed → Store
- Query: Question → Embed → Retrieve → Groq

## Run the demo

```bash
python3 -m app.query "What is the expense ratio of HDFC Large Cap Fund?"
python3 -m app.demo
streamlit run app/ui.py
```

## Demo polish

Use the demo runner to quickly validate a few in-scope questions before showing the UI:

```bash
python3 -m app.demo
```

It prints a short Q&A checklist for expense ratio, SIP, ELSS lock-in, and a refusal case. This makes the live demo easier to present in class without retyping questions.

## Known limits

- Public scheme facts only; no advice, no personalized allocation, no return computation
- Answers are grounded in fetched corpus chunks and may be incomplete outside the loaded sources
- Sources can change, so the app displays the date from the retrieved source metadata

## Disclaimer

> Facts-only. This assistant summarises publicly available scheme information and is not investment advice. It does not recommend buying, selling, or holding any mutual fund. Check the official factsheet / SID / KIM before you act. Sources can change; see “Last updated from sources.”
