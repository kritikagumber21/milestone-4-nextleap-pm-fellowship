"""Guardrails for facts-only mutual fund FAQ requests."""

from __future__ import annotations

import re

OFFICIAL_EDUCATION_URL = "https://www.amfiindia.com/investor-corner/education"
OFFICIAL_HDFC_URL = "https://www.hdfcfund.com/"

PII_PATTERNS = [
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    r"\b\d{12}\b",
    r"\b(?:aadhaar|aadhar)\b",
    r"\b(?:pan|otp|account number|bank account|ifsc|upi id)\b",
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b",
]

ADVICE_PATTERNS = [
    r"\bshould i (buy|sell|switch|invest in|allocate)\b",
    r"\b(best|top|recommended) fund\b",
    r"\bfor me\b",
    r"\bwhat should i do\b",
    r"\bwhich fund should i buy\b",
    r"\bshould i invest\b",
    r"\bswitch.*fund\b",
]

PERFORMANCE_PATTERNS = [
    r"\breturns?\b",
    r"\bcagr\b",
    r"\b(outperformed|performed better|higher returns?|best performer|which is better)\b",
    r"\bcompare.*fund\b",
    r"\bwhich fund gave.*return\b",
    r"\breturn.*comparison\b",
]


def _contains_pattern(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    for pattern in patterns:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return True
    return False


def _contains_pii(text: str) -> bool:
    for pattern in PII_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def check_guardrails(question: str) -> dict:
    """Return an allow/refuse decision for the incoming user question."""
    if not question or not question.strip():
        return {"action": "allow", "message": "", "citation_url": ""}

    text = question.strip()

    if _contains_pii(text):
        return {
            "action": "refuse_pii",
            "message": "I can’t handle personal financial or identity details. Please ask only about public fund facts from official scheme documents or AMFI education resources.",
            "citation_url": OFFICIAL_EDUCATION_URL,
        }

    if _contains_pattern(text, ADVICE_PATTERNS):
        return {
            "action": "refuse_advice",
            "message": "I can provide fund facts, not investment advice. For official scheme and investor education information, please use the AMFI guidance or the scheme’s official factsheet.",
            "citation_url": OFFICIAL_EDUCATION_URL,
        }

    if _contains_pattern(text, PERFORMANCE_PATTERNS):
        return {
            "action": "refuse_performance",
            "message": "I can answer factual questions, but I do not compute or compare fund performance. Please use the official scheme factsheet or AMFI educational resources for performance information.",
            "citation_url": OFFICIAL_HDFC_URL,
        }

    return {"action": "allow", "message": "", "citation_url": ""}
