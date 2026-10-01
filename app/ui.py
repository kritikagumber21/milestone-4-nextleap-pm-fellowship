"""Tiny Streamlit UI for the HDFC mutual fund facts-only RAG demo."""

from __future__ import annotations

import streamlit as st

from app.query import answer_question

DISCLAIMER = (
    "Facts-only. This assistant summarises publicly available scheme information and is "
    "not investment advice. It does not recommend buying, selling, or holding any mutual "
    "fund. Check the official factsheet / SID / KIM before you act. Sources can change; "
    "see \"Last updated from sources.\""
)

EXAMPLE_QUESTIONS = [
    "What is the expense ratio of HDFC Large Cap Fund (Direct Growth)?",
    "What is the lock-in for HDFC ELSS Tax Saver?",
    "What is the minimum SIP for HDFC Small Cap Fund?",
]

st.set_page_config(page_title="HDFC Fund FAQs", page_icon="📘")

st.title("HDFC Mutual Fund FAQs")
st.caption("Facts-only. No investment advice.")

st.write(DISCLAIMER)

for question in EXAMPLE_QUESTIONS:
    if st.button(question, key=f"example-{question}"):
        st.session_state["question"] = question

question = st.text_input(
    "Ask a question about a scheme fact",
    value=st.session_state.get("question", ""),
)

if st.button("Ask") and question.strip():
    try:
        result = answer_question(question)
    except RuntimeError as exc:
        st.warning(str(exc))
    else:
        st.markdown(f"**Answer:** {result['text']}")
        st.write(f"**Citation:** {result['citation_url']}")
        st.write(f"**Last updated from sources:** {result['last_updated']}")
