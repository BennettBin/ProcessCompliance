from __future__ import annotations

from pathlib import Path
import csv
from typing import Any

from .json_utils import read_json, write_json
from .logging import get_logger
from .text_utils import int_to_ordinal_word, split_document, trans_case_to_text


def mkdir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def read_log(csv_file_path: str):
    case_dict = {}
    with open(csv_file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row.get("case")
            if case_id not in case_dict:
                case_dict[case_id] = []
            case_dict[case_id].append(row)
    return list(case_dict.values())


def get_parameters(csv_file_path: str):
    with open(csv_file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        row = next(reader, {})
    out = {}
    for k, v in row.items():
        if v is None:
            out[k] = v
            continue
        try:
            fv = float(v)
            out[k] = int(fv) if fv.is_integer() else fv
        except Exception:
            out[k] = v
    return out


def get_key_by_value(d: dict, value: Any):
    for k, v in d.items():
        if v == value:
            return k
    return None


def csv_to_dict(csv_file_path: str):
    out = {}
    with open(csv_file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "name" in row and "value" in row:
                key = row["name"]
                val = row["value"]
                try:
                    out[key] = float(val)
                except Exception:
                    out[key] = val
            elif len(row) >= 2:
                items = list(row.items())
                key = items[0][1]
                val = items[1][1]
                try:
                    out[key] = float(val)
                except Exception:
                    out[key] = val
    return out


__all__ = [
    "mkdir",
    "get_logger",
    "read_json",
    "write_json",
    "int_to_ordinal_word",
    "split_document",
    "trans_case_to_text",
    "read_log",
    "get_parameters",
    "get_key_by_value",
    "csv_to_dict",
]
