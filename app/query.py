"""Question answering pipeline for the HDFC mutual fund facts-only demo."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from groq import Groq

from app.embedder import embed_texts
from app.guardrails import check_guardrails

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
COLLECTION_NAME = "hdfc_mf_faqs"
DEFAULT_TOP_K = 4
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(ROOT / "chroma"))


def _get_collection():
    client = _client()
    return client.get_collection(name=COLLECTION_NAME)


def _scheme_hint(question: str) -> str | None:
    q = question.lower()
    patterns = {
        "hdfc large cap": "HDFC Large Cap Fund Direct Growth",
        "large cap": "HDFC Large Cap Fund Direct Growth",
        "hdfc small cap": "HDFC Small Cap Fund Direct Growth",
        "small cap": "HDFC Small Cap Fund Direct Growth",
        "hdfc elss": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "elss": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "hdfc equity": "HDFC Equity Fund Direct Growth",
        "flexi cap": "HDFC Equity Fund Direct Growth",
        "balanced advantage": "HDFC Balanced Advantage Fund Direct Growth",
        "hybrid": "HDFC Balanced Advantage Fund Direct Growth",
    }
    for pattern, scheme in patterns.items():
        if pattern in q:
            return scheme
    return None


def _make_not_found(question: str) -> dict:
    scheme_hint = _scheme_hint(question)
    fallback = "https://www.hdfcfund.com/"
    return {
        "text": "I could not find this fact in the current corpus.",
        "citation_url": scheme_hint and fallback or fallback,
        "last_updated": "not available",
    }


def _pick_citation_url(context_chunks: list[dict]) -> str:
    """Prefer official HDFC/AMFI links when available, otherwise fall back to the first chunk."""
    preferred_hosts = (
        "hdfcfund.com",
        "amfiindia.com",
        "sebi.gov.in",
        "mf.hdfcfund.com",
    )

    for chunk in context_chunks:
        url = (chunk.get("metadata") or {}).get("source_url")
        if not url:
            continue
        if any(host in url.lower() for host in preferred_hosts):
            return url

    for chunk in context_chunks:
        url = (chunk.get("metadata") or {}).get("source_url")
        if url:
            return url

    return "https://www.hdfcfund.com/"


def answer_question(question: str, k: int = DEFAULT_TOP_K, debug: bool = False) -> dict:
    """Answer a user fact question using Chroma retrieval and Groq generation."""
    guard = check_guardrails(question)
    if guard["action"] != "allow":
        return {
            "text": guard["message"],
            "citation_url": guard["citation_url"],
            "last_updated": "not available",
        }

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Create a local .env from .env.example and add the key.")

    model_name = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    collection = _get_collection()
    embedding = embed_texts([question])[0]
    results = collection.query(
        query_embeddings=[embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    if debug:
        print("=== debug retrieval ===")
        for chunk_id, metadata, distance in zip(ids, metadatas, distances):
            print(f"chunk_id={chunk_id} | source_url={metadata.get('source_url')} | distance={distance}")
        print("======================")

    if not documents:
        return _make_not_found(question)

    context_chunks = []
    for doc, metadata in zip(documents, metadatas):
        if not doc:
            continue
        context_chunks.append({"text": doc, "metadata": metadata})

    if not context_chunks:
        return _make_not_found(question)

    gold_context = "\n\n".join(
        f"Source: {chunk['metadata'].get('source_url')}\n{chunk['text']}"
        for chunk in context_chunks[:4]
    )

    client = Groq(api_key=api_key)
    system_prompt = (
        "You are a facts-only mutual fund FAQ assistant. Use only the supplied context. "
        "Answer in no more than 3 sentences. Give exactly one citation URL from the provided source metadata. "
        "Include the line 'Last updated from sources: <date>' at the end of the answer. "
        "Never provide investment advice, compute returns, compare funds, or invent facts. "
        "When the fact is unavailable, say the fact is not in the current corpus."
    )

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{gold_context}"},
        ],
        temperature=0.1,
        max_tokens=220,
    )

    response_text = completion.choices[0].message.content.strip()
    citation_url = _pick_citation_url(context_chunks)
    last_updated = (
        next(
            (
                chunk["metadata"].get("fetched_at")
                for chunk in context_chunks
                if (chunk.get("metadata") or {}).get("fetched_at")
            ),
            "unknown",
        )
    )

    return {
        "text": response_text,
        "citation_url": citation_url,
        "last_updated": last_updated,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HDFC mutual fund FAQ query")
    parser.add_argument("question", help="Question to answer.")
    parser.add_argument("--k", type=int, default=DEFAULT_TOP_K, help="Number of Chroma neighbors to retrieve.")
    parser.add_argument("--debug", action="store_true", help="Print retrieved chunk ids and URLs.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = answer_question(args.question, k=args.k, debug=args.debug)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(result["text"])
    print(f"Citation: {result['citation_url']}")
    print(f"Last updated from sources: {result['last_updated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
