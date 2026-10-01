# Chunking strategy for the HDFC mutual fund corpus

## What the raw pages actually look like

We inspected the saved files in `data/raw/` for all five schemes. Each source contains a similar structure:

- A page-level header with `SOURCE_URL` and `PAGE_TITLE`
- A `SCHEME_FACTS` section with machine-readable fund facts such as `Expense ratio`, `Exit load`, `Minimum SIP`, `Benchmark`, `Riskometer`, and `Lock-in`
- An `EXTRACTED_JSON_FACTS` section with many key/value pairs from the site's JSON payload
- A `JSON_LD` section with FAQ and schema markup
- A `VISIBLE_TEXT` section containing page copy and long FAQ text

This is not a narrative article. It is a structured fact page, with repeated schema blocks and FAQ text mixed in. A single giant chunk would dilute the important scheme facts and make retrieval noisy.

## Choice of chunk size and overlap

We used a char-based chunk size of 700 characters with a 120-character overlap.

Why this fits this corpus:

- The important facts are short, high-signal lines such as `Expense ratio: 1.03`, `Minimum SIP: 100`, and `Lock-in: 3 years, 0 months, 0 days`.
- The documents are dominated by repeated JSON and FAQ metadata, so the chunk boundary should be section-aware rather than purely sentence-based.
- A chunk of around 700 characters retains enough context to include a complete fact block, while the overlap prevents splitting adjacent facts across boundaries.

## Section-aware chunking rules

We chunk by the real document structure instead of blindly splitting on pure character count:

1. Keep `SCHEME_FACTS` together as a top-level fact block.
2. Keep `EXTRACTED_JSON_FACTS` together as a separate block.
3. Keep `JSON_LD` and `VISIBLE_TEXT` as separate sections.
4. If a block is still too long, fall back to a sliding window with 700/120 settings.

This preserves scheme identity and avoids mixing large-cap, ELSS, or small-cap facts into one chunk.

## Metadata kept per chunk

Each chunk includes:

- `chunk_id`
- `scheme_name`
- `category`
- `source_url`
- `fetched_at`
- `section`

This makes the retrieval stage able to cite the correct scheme and source while still preserving the section context used in the page.

## Result

The chunk export is written to `data/chunks.txt` and is intended to be human-readable. It is section-aware, scheme-aware, and appropriately small for retrieval with the MiniLM embedding model.
