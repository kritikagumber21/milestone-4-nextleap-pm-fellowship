"""Ingestion pipeline: Load → Chunk → Embed → Store.

Phase 1 implements Load only (--load-only).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import chromadb

from app.embedder import embed_texts

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SOURCES_CSV = DATA_DIR / "sources.csv"
CHUNKS_TXT = DATA_DIR / "chunks.txt"
CHROMA_DIR = ROOT / "chroma"
COLLECTION_NAME = "hdfc_mf_faqs"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
TIMEOUT_S = 30
RETRY_SLEEP_S = 2

SEED_SOURCES = [
    {
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "scheme_name": "HDFC Large Cap Fund Direct Growth",
        "category": "Large Cap",
        "doc_type": "scheme_page",
        "slug": "hdfc-large-cap-fund-direct-growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "scheme_name": "HDFC Equity Fund Direct Growth",
        "category": "Flexi Cap",
        "doc_type": "scheme_page",
        "slug": "hdfc-equity-fund-direct-growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "scheme_name": "HDFC ELSS Tax Saver Direct Growth",
        "category": "ELSS",
        "doc_type": "scheme_page",
        "slug": "hdfc-elss-tax-saver-fund-direct-plan-growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "scheme_name": "HDFC Small Cap Fund Direct Growth",
        "category": "Small Cap",
        "doc_type": "scheme_page",
        "slug": "hdfc-small-cap-fund-direct-growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
        "scheme_name": "HDFC Balanced Advantage Fund Direct Growth",
        "category": "Hybrid",
        "doc_type": "scheme_page",
        "slug": "hdfc-balanced-advantage-fund-direct-growth",
    },
]

DROP_TAGS = ("script", "style", "noscript", "svg", "nav", "footer", "header")
NOISE_LINE = re.compile(
    r"^(login|sign up|download app|get app|cookie|privacy policy|"
    r"terms and conditions|follow us)$",
    re.I,
)
CHUNK_TARGET_CHARS = 700
CHUNK_OVERLAP_CHARS = 120


def fetch_html(url: str) -> tuple[str | None, str | None]:
    """GET url once, retry once on failure. Returns (html, error)."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    last_error = None
    for attempt in range(2):
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT_S)
            response.raise_for_status()
            return response.text, None
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt == 0:
                time.sleep(RETRY_SLEEP_S)
    return None, last_error


def _json_ld_blocks(soup: BeautifulSoup) -> list[dict]:
    blocks = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, list):
            blocks.extend(item for item in parsed if isinstance(item, dict))
        elif isinstance(parsed, dict):
            blocks.append(parsed)
    return blocks


def _flatten_json(value, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if _skip_json_key(str(key)):
                continue
            path = f"{prefix}.{key}" if prefix else str(key)
            lines.extend(_flatten_json(child, path))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            path = f"{prefix}[{i}]"
            lines.extend(_flatten_json(child, path))
    elif value is None or value == "":
        return lines
    else:
        text = str(value).strip()
        if text:
            lines.append(f"{prefix}: {text}")
    return lines


# Holdings, peer tables, and return series bloat the corpus and are out of FAQ scope.
SKIP_JSON_KEYS = {
    "holdings",
    "historic_fund_expense",
    "peerComparison",
    "peer_comparison",
    "return_stats",
    "simple_return",
    "sip_return",
    "lumpsum_return",
    "stats",
    "stp_details",
    "swp_details",
    "fund_manager_details",
    "investment_date_configs",
    "logo",
    "image",
    "sameAs",
    "@context",
    "@type",
    "meta_title",
    "meta_desc",
    "meta_robots",
}

FACT_FIELDS = (
    ("scheme_name", "Scheme name"),
    ("fund_house", "Fund house"),
    ("amc", "AMC"),
    ("category", "Category"),
    ("sub_category", "Sub-category"),
    ("expense_ratio", "Expense ratio"),
    ("exit_load", "Exit load"),
    ("min_sip_investment", "Minimum SIP"),
    ("min_investment_amount", "Minimum lumpsum"),
    ("mini_additional_investment", "Minimum additional investment"),
    ("sip_multiplier", "SIP multiplier"),
    ("benchmark", "Benchmark"),
    ("benchmark_name", "Benchmark name"),
    ("nfo_risk", "Riskometer"),
    ("launch_date", "Launch date"),
    ("fund_manager", "Fund manager"),
    ("description", "Description"),
    ("isin", "ISIN"),
)


def _skip_json_key(key: str) -> bool:
    return key in SKIP_JSON_KEYS or key.startswith("@")


def _scheme_facts_block(mf: dict) -> str:
    lines = ["SCHEME_FACTS"]
    for key, label in FACT_FIELDS:
        if key in mf and mf[key] not in (None, "", []):
            lines.append(f"{label}: {mf[key]}")
    lock_in = mf.get("lock_in")
    if isinstance(lock_in, dict):
        years = lock_in.get("years")
        months = lock_in.get("months")
        days = lock_in.get("days")
        if any(v not in (None, "", 0) for v in (years, months, days)):
            lines.append(
                f"Lock-in: {years or 0} years, {months or 0} months, {days or 0} days"
            )
        else:
            lines.append("Lock-in: None")
    extra = mf.get("additional_details")
    if isinstance(extra, dict) and extra.get("lock_in_yrs") not in (None, ""):
        lines.append(f"Lock-in years (additional_details): {extra.get('lock_in_yrs')}")
    category_info = mf.get("category_info")
    if isinstance(category_info, dict):
        for ck, cv in category_info.items():
            if cv not in (None, ""):
                lines.append(f"Category info ({ck}): {cv}")
    return "\n".join(lines) if len(lines) > 1 else ""


def _next_data_facts(soup: BeautifulSoup) -> str:
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag:
        return ""
    raw = tag.string or tag.get_text() or ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    page_props = payload.get("props", {}).get("pageProps", {})
    mf = page_props.get("mfServerSideData")
    if not isinstance(mf, dict):
        return ""
    parts: list[str] = []
    summary = _scheme_facts_block(mf)
    if summary:
        parts.append(summary)
    trimmed = {k: v for k, v in mf.items() if not _skip_json_key(str(k))}
    dumped = _flatten_json(trimmed)
    if dumped:
        parts.append("EXTRACTED_JSON_FACTS\n" + "\n".join(dumped))
    return "\n\n".join(parts)


def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(DROP_TAGS):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text("\n", strip=True)
    cleaned: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 2:
            continue
        if NOISE_LINE.match(line):
            continue
        if line.lower() in seen:
            continue
        seen.add(line.lower())
        cleaned.append(line)
    return "\n".join(cleaned)


def extract_document(html: str, url: str) -> tuple[str, str]:
    """Return (title, cleaned_text)."""
    soup = BeautifulSoup(html, "lxml")
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(" ", strip=True)
    if not title:
        title = urlparse(url).path.rsplit("/", 1)[-1]

    parts = [f"SOURCE_URL: {url}", f"PAGE_TITLE: {title}"]
    json_facts = _next_data_facts(soup)
    if json_facts:
        parts.append(json_facts)
    ld = _json_ld_blocks(soup)
    if ld:
        parts.append("JSON_LD\n" + "\n".join(_flatten_json(ld)))
    visible = _visible_text(soup)
    if visible:
        parts.append("VISIBLE_TEXT\n" + visible)
    return title, "\n\n".join(parts).strip() + "\n"


def slug_filename(slug: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-").lower()
    return f"{safe}.txt"


def load_sources() -> list[dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    fetched_at = date.today().isoformat()
    rows: list[dict] = []
    saved = 0
    errors: list[str] = []

    for source in SEED_SOURCES:
        url = source["url"]
        print(f"Fetching {url} ...")
        html, error = fetch_html(url)
        if error or not html:
            msg = f"FAILED {url}: {error}"
            print(msg, file=sys.stderr)
            errors.append(msg)
            rows.append(
                {
                    "url": url,
                    "scheme_name": source["scheme_name"],
                    "category": source["category"],
                    "doc_type": source["doc_type"],
                    "fetched_at": "",
                    "title": f"FETCH_ERROR: {error}",
                }
            )
            continue

        title, text = extract_document(html, url)
        out_path = RAW_DIR / slug_filename(source["slug"])
        out_path.write_text(text, encoding="utf-8")
        saved += 1
        rows.append(
            {
                "url": url,
                "scheme_name": source["scheme_name"],
                "category": source["category"],
                "doc_type": source["doc_type"],
                "fetched_at": fetched_at,
                "title": title,
            }
        )
        print(f"  saved {out_path.relative_to(ROOT)} ({len(text)} chars)")

    fieldnames = ["url", "scheme_name", "category", "doc_type", "fetched_at", "title"]
    with SOURCES_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nLoad summary: {saved}/{len(SEED_SOURCES)} documents saved")
    print(f"Raw dir: {RAW_DIR.relative_to(ROOT)}")
    print(f"Sources: {SOURCES_CSV.relative_to(ROOT)}")
    if errors:
        print(f"Errors: {len(errors)} (see messages above)")
    return rows


def _section_name(text: str) -> str:
    if text.startswith("SCHEME_FACTS"):
        return "scheme_facts"
    if text.startswith("EXTRACTED_JSON_FACTS"):
        return "extracted_json_facts"
    if text.startswith("JSON_LD"):
        return "json_ld"
    if text.startswith("VISIBLE_TEXT"):
        return "visible_text"
    if text.startswith("SOURCE_URL:"):
        return "source_header"
    return "mixed_text"


def _sliding_window(text: str, target_chars: int, overlap: int) -> list[str]:
    if len(text) <= target_chars:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + target_chars)
        if end < len(text):
            boundary = max(
                text.rfind("\n", start, end),
                text.rfind(" ", start, end),
            )
            if boundary > start + max(60, target_chars // 3):
                end = boundary
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break

        next_start = max(start + target_chars - overlap, end - overlap)
        while next_start > start and next_start < len(text) and text[next_start] not in " \n\t":
            next_start -= 1
        start = next_start
    return chunks


def _merge_blocks(blocks: list[str]) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    current_text = ""
    current_section = "mixed_text"

    for block in blocks:
        cleaned = block.strip()
        if not cleaned:
            continue
        section = _section_name(cleaned)
        if not current_text:
            current_text = cleaned
            current_section = section
            continue
        candidate = current_text + "\n\n" + cleaned
        if len(candidate) <= CHUNK_TARGET_CHARS:
            current_text = candidate
            current_section = current_section if current_section != "mixed_text" else section
            continue
        merged.append((current_section, current_text))
        if len(cleaned) <= CHUNK_TARGET_CHARS:
            current_text = cleaned
            current_section = section
        else:
            current_text = ""
            current_section = "mixed_text"
            merged.extend((section, part) for part in _sliding_window(cleaned, CHUNK_TARGET_CHARS, CHUNK_OVERLAP_CHARS))

    if current_text:
        merged.append((current_section, current_text))

    return merged


def chunk_document(source_row: dict, raw_text: str) -> list[dict]:
    """Split a cleaned raw document into scheme-aware chunks with overlap."""
    slug = urlparse(source_row["url"]).path.rstrip("/").split("/")[-1]
    source_slug = slug_filename(slug).removesuffix(".txt")
    section_blocks = [part.strip() for part in re.split(r"\n\s*\n+", raw_text.strip()) if part.strip()]
    chunks: list[dict] = []
    chunk_counter = 0

    for section_name, block in _merge_blocks(section_blocks):
        parts = _sliding_window(block, CHUNK_TARGET_CHARS, CHUNK_OVERLAP_CHARS)
        for part in parts:
            chunk_id = f"{source_slug}-{chunk_counter:04d}"
            chunk_counter += 1
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "source_url": source_row["url"],
                    "scheme_name": source_row["scheme_name"],
                    "category": source_row["category"],
                    "fetched_at": source_row.get("fetched_at", ""),
                    "section": section_name,
                    "text": part.strip(),
                }
            )
    return chunks


def chunk_sources() -> list[dict]:
    """Read raw files and write a readable chunks export for Phase 2."""
    if not SOURCES_CSV.exists():
        raise FileNotFoundError(f"Missing sources CSV: {SOURCES_CSV}")

    all_chunks: list[dict] = []
    with SOURCES_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    for row in rows:
        url = row.get("url", "").strip()
        if not url:
            continue
        slug = urlparse(url).path.rstrip("/").split("/")[-1]
        raw_path = RAW_DIR / slug_filename(slug)
        if not raw_path.exists():
            print(f"Skipping missing file for {url}: {raw_path.name}", file=sys.stderr)
            continue
        raw_text = raw_path.read_text(encoding="utf-8")
        all_chunks.extend(chunk_document(row, raw_text))

    output_path = DATA_DIR / "chunks.txt"
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in all_chunks:
            handle.write(f"--- chunk_id: {chunk['chunk_id']}\n")
            handle.write(f"scheme_name: {chunk['scheme_name']}\n")
            handle.write(f"category: {chunk['category']}\n")
            handle.write(f"source_url: {chunk['source_url']}\n")
            handle.write(f"fetched_at: {chunk['fetched_at']}\n")
            handle.write(f"section: {chunk['section']}\n")
            handle.write("---\n")
            handle.write(chunk["text"].strip())
            handle.write("\n\n")

    print(f"Chunk summary: {len(rows)} docs processed, {len(all_chunks)} chunks written to {output_path.relative_to(ROOT)}")
    return all_chunks


def load_chunks_from_txt(path: Path = CHUNKS_TXT) -> list[dict]:
    """Parse the human-readable chunks export into a list of dict records."""
    if not path.exists():
        raise FileNotFoundError(f"Missing chunk export: {path}")

    text = path.read_text(encoding="utf-8")
    pattern = (
        r"--- chunk_id: (?P<chunk_id>[^\n]+)\n"
        r"scheme_name: (?P<scheme_name>[^\n]+)\n"
        r"category: (?P<category>[^\n]+)\n"
        r"source_url: (?P<source_url>[^\n]+)\n"
        r"fetched_at: (?P<fetched_at>[^\n]+)\n"
        r"section: (?P<section>[^\n]+)\n"
        r"---\n"
        r"(?P<text>.*?)(?=\n--- chunk_id:|\Z)"
    )
    matches = list(re.finditer(pattern, text, flags=re.DOTALL))
    records: list[dict] = []
    for match in matches:
        records.append({
            "chunk_id": match.group("chunk_id").strip(),
            "scheme_name": match.group("scheme_name").strip(),
            "category": match.group("category").strip(),
            "source_url": match.group("source_url").strip(),
            "fetched_at": match.group("fetched_at").strip(),
            "section": match.group("section").strip(),
            "text": match.group("text").strip(),
        })
    return records


def embed_and_store_chunks() -> int:
    """Read chunks.txt, embed them, and store them in a persisted Chroma collection.

    Chroma uses an L2 distance by default; this collection is configured for cosine
    space so retrieval scores align with the embedding model's semantic matching.
    """
    chunk_rows = load_chunks_from_txt(CHUNKS_TXT)
    if not chunk_rows:
        raise ValueError(f"No chunks found in {CHUNKS_TXT}")

    texts = [chunk["text"] for chunk in chunk_rows]
    embeddings = embed_texts(texts)
    if not embeddings:
        raise ValueError("Embedding generation produced no vectors.")

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    except (ValueError, chromadb.errors.NotFoundError):
        pass

    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[chunk["chunk_id"] for chunk in chunk_rows],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {
                "scheme_name": chunk["scheme_name"],
                "category": chunk["category"],
                "source_url": chunk["source_url"],
                "fetched_at": chunk["fetched_at"],
                "section": chunk["section"],
            }
            for chunk in chunk_rows
        ],
    )

    count = collection.count()
    print(f"Collection {COLLECTION_NAME} created at {CHROMA_DIR.relative_to(ROOT)}")
    print(f"Stored {count} chunks with embedding dimension {len(embeddings[0])}")
    return count


def full_ingest() -> int:
    """Run the full Load -> Chunk -> Embed -> Store pipeline."""
    load_sources()
    chunk_sources()
    return embed_and_store_chunks()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HDFC MF FAQ ingestion")
    parser.add_argument(
        "--load-only",
        action="store_true",
        help="Fetch public pages into data/raw/ (Phase 1). No chunk/embed/store.",
    )
    parser.add_argument(
        "--chunk-only",
        action="store_true",
        help="Read cleaned raw files and write data/chunks.txt (Phase 2).",
    )
    parser.add_argument(
        "--embed-store",
        action="store_true",
        help="Read data/chunks.txt and store the MiniLM vectors in Chroma (Phase 3).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.load_only:
        load_sources()
        return 0
    if args.chunk_only:
        chunk_sources()
        return 0
    if args.embed_store:
        embed_and_store_chunks()
        return 0
    full_ingest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
