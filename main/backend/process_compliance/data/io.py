from __future__ import annotations

from pathlib import Path

import pandas as pd


def _check_supported(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".xes":
        raise ValueError("XES is not supported yet in this API path. Please provide a CSV file.")
    if suffix != ".csv":
        raise ValueError(f"Unsupported file format: {suffix or '<none>'}. Only CSV is supported.")


def load_event_log(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Event log file not found: {path}")
    _check_supported(p)
    return pd.read_csv(p, encoding="utf-8-sig")


def load_running_trace(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Running trace file not found: {path}")
    _check_supported(p)
    return pd.read_csv(p, encoding="utf-8-sig")

