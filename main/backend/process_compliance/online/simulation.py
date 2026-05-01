from __future__ import annotations

import csv
from typing import Any, Dict, List


def simulate(
    running_trace_path: str,
    compliance_rules_path: str,
    log_path: str,
    func,
) -> None:
    with open(running_trace_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        events: List[Dict[str, Any]] = [dict(row) for row in reader]

    if not events:
        return

    prediction_rows: List[Dict[str, Any]] = []
    index = 0

    while True:
        if index >= len(events):
            break
        index += 1
        occurred_trace: List[Dict[str, Any]] = events[:index]
        compliance_result: Dict[str, Any] = func(compliance_rules_path, occurred_trace)
        if not isinstance(compliance_result, dict):
            raise TypeError("func(compliance_rules_path, occurred_trace) must return Dict[str, Any]")

        row: Dict[str, Any] = {"step": index, "num_events": len(occurred_trace)}
        row.update(compliance_result)
        prediction_rows.append(row)

        fieldnames: List[str] = []
        for r in prediction_rows:
            for key in r.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

        with open(log_path, "w", encoding="utf-8-sig", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(prediction_rows)


def run_system(rules_path: str, running_trace: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Package-native fallback system entry.
    Returns controlled placeholders for compatibility.
    """
    _ = rules_path
    _ = running_trace
    return {
        "final_check_summary": "CONSENSUS: NO\nCONFIDENCE: 0.0\nNo packaged compliance checker configured.",
        "final_predict_summary": "CONSENSUS: NO\nCONFIDENCE: 0.0\nNo packaged predictive analyzer configured.",
    }


__all__ = ["simulate", "run_system"]

