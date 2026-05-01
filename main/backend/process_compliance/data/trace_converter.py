from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.process_compliance.online.result_schema import TraceEvent
from backend.process_compliance.utils import trans_case_to_text


def _int_to_ordinal_word(number: int) -> str:
    ordinals = {
        1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
        6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
    }
    if number in ordinals:
        return ordinals[number]
    return str(number)


def _fallback_trace_to_text(case: List[Dict[str, Any]]) -> str:
    case_id = case[0].get("case", "unknown_case") if case else "unknown_case"
    text = "The trace of the event log with case number '{}' is as follows: ".format(case_id)
    for i, event in enumerate(case):
        text += (
            "The {} event was completed by '{}' for Activity '{}', taking {} days; ".format(
                _int_to_ordinal_word(i + 1),
                event.get("org:resource", "unknown_resource"),
                event.get("concept:name", "unknown_activity"),
                event.get("executionTimeD", 0),
            )
        )
    return text


def dataframe_to_trace_events(df: pd.DataFrame) -> List[TraceEvent]:
    events: List[TraceEvent] = []
    if df is None or df.empty:
        return events

    for _, row in df.iterrows():
        row_dict: Dict[str, Any] = {str(k): row[k] for k in df.columns}
        case_id = str(row_dict.get("case")) if row_dict.get("case") is not None else None
        activity = str(row_dict.get("concept:name")) if row_dict.get("concept:name") is not None else None
        resource = str(row_dict.get("org:resource")) if row_dict.get("org:resource") is not None else None
        role = str(row_dict.get("org:role")) if row_dict.get("org:role") is not None else None

        execution_time_val = row_dict.get("executionTimeD")
        try:
            execution_time = float(execution_time_val) if execution_time_val is not None else None
        except Exception:
            execution_time = None

        timestamp_val = row_dict.get("time:timestamp")
        timestamp = str(timestamp_val) if timestamp_val is not None else None

        events.append(
            TraceEvent(
                case_id=case_id,
                activity=activity,
                resource=resource,
                role=role,
                execution_time=execution_time,
                timestamp=timestamp,
                raw=row_dict,
            )
        )

    return events


def running_trace_to_text(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "Running trace is empty."

    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        r: Dict[str, Any] = {str(k): row[k] for k in df.columns}
        if "case" not in r or r.get("case") is None:
            r["case"] = "unknown_case"
        if "org:resource" not in r or r.get("org:resource") is None:
            r["org:resource"] = "unknown_resource"
        if "concept:name" not in r or r.get("concept:name") is None:
            r["concept:name"] = "unknown_activity"
        if "executionTimeD" not in r or r.get("executionTimeD") is None:
            r["executionTimeD"] = 0
        records.append(r)

    try:
        return trans_case_to_text(records)
    except Exception:
        return _fallback_trace_to_text(records)

