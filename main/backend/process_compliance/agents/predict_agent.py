from __future__ import annotations

from backend.process_compliance.agents.prompts import PREDICT_PROMPT


def build_predict_prompt(running_trace_text: str, predicted_status_text: str, question: str) -> str:
    return (
        PREDICT_PROMPT
        + "\n\nRunning trace:\n"
        + (running_trace_text or "")
        + "\n\nPredicted status:\n"
        + (predicted_status_text or "")
        + "\n\nQuestion:\n"
        + (question or "Analyze future compliance risk.")
    )


