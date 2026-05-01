from __future__ import annotations

from backend.process_compliance.agents.prompts import SUMMARY_PROMPT


def build_summary_prompt(check_text: str, predict_text: str, question: str) -> str:
    return (
        SUMMARY_PROMPT
        + "\n\nCheck agent output:\n"
        + (check_text or "")
        + "\n\nPredict agent output:\n"
        + (predict_text or "")
        + "\n\nQuestion:\n"
        + (question or "Provide a final summary decision.")
    )


