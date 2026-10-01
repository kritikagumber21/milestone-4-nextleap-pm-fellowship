"""Demo runner for the HDFC facts-only RAG app."""

from __future__ import annotations

from app.query import answer_question

DEMO_QUESTIONS = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the minimum SIP for HDFC Small Cap Fund?",
    "What is the lock-in for HDFC ELSS Tax Saver?",
    "Should I buy HDFC Large Cap Fund?",
]


def run_demo(questions: list[str] | None = None) -> None:
    """Print a short demo set for class presentation and smoke testing."""
    sample_questions = questions or DEMO_QUESTIONS

    for question in sample_questions:
        print(f"\n=== QUESTION: {question} ===")
        try:
            result = answer_question(question)
            print(result["text"])
            print(f"Citation: {result['citation_url']}")
            print(f"Last updated from sources: {result['last_updated']}")
        except Exception as exc:  # pragma: no cover - demo runner only
            print(type(exc).__name__, exc)


if __name__ == "__main__":
    run_demo()
