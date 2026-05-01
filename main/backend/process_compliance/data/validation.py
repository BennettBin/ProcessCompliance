from __future__ import annotations

from pathlib import Path
from typing import Iterable, Set

import pandas as pd

from .io import load_event_log, load_running_trace
from .schema import ValidationResult

REQUIRED_COLUMNS_COMMON: Set[str] = {"case", "concept:name"}
OPTIONAL_COLUMNS: Set[str] = {"org:resource", "org:role"}


def _normalize_columns(columns: Iterable[str]) -> Set[str]:
    return {str(c).lstrip("\ufeff").strip() for c in columns}


def _validate_csv(path: str, kind: str) -> ValidationResult:
    p = Path(path)
    result = ValidationResult(file_path=str(p), file_type="csv")

    if not p.exists():
        result.errors.append(f"{kind} file does not exist: {path}")
        return result

    if p.suffix.lower() == ".xes":
        result.errors.append(f"{kind} format .xes is not supported yet. Please upload CSV first.")
        return result
    if p.suffix.lower() != ".csv":
        result.errors.append(f"{kind} format is not supported: {p.suffix or '<none>'}. Only CSV is supported.")
        return result

    try:
        df = load_running_trace(path) if kind == "running_trace" else load_event_log(path)
    except Exception as e:
        result.errors.append(f"Failed to read {kind}: {e}")
        return result

    result.row_count = int(len(df))
    result.columns = [str(c) for c in df.columns]
    norm = _normalize_columns(df.columns)

    missing = sorted(REQUIRED_COLUMNS_COMMON - norm)
    if missing:
        result.errors.append(f"Missing required columns: {', '.join(missing)}")

    missing_optional = sorted(OPTIONAL_COLUMNS - norm)
    if missing_optional:
        result.warnings.append(
            "Missing optional columns: "
            + ", ".join(missing_optional)
            + ". The system will continue with fallback values."
        )

    if kind == "running_trace" and result.row_count == 0:
        result.errors.append("Running trace is empty.")

    result.valid = len(result.errors) == 0
    return result


def validate_event_log(path: str) -> ValidationResult:
    return _validate_csv(path, kind="event_log")


def validate_running_trace(path: str) -> ValidationResult:
    return _validate_csv(path, kind="running_trace")

