from __future__ import annotations

from backend.process_compliance.agents.prompts import CHECK_PROMPT


def build_check_prompt(running_trace_text: str, rule_text: str, question: str) -> str:
    return (
        CHECK_PROMPT
        + "\n\nCompliance rule:\n"
        + (rule_text or "")
        + "\n\nRunning trace:\n"
        + (running_trace_text or "")
        + "\n\nQuestion:\n"
        + (question or "Check current compliance.")
    )


