from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .settings import AppConfig


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_config_path(root: Path) -> Path:
    return root / "configs" / "default.yaml"


def _resolve_path(value: str, root: Path) -> str:
    p = Path(value)
    if p.is_absolute():
        return str(p)
    return str((root / p).resolve())


def _resolve_paths(raw: dict[str, Any], root: Path) -> dict[str, Any]:
    out = dict(raw)

    dataset = dict(out.get("dataset", {}))
    for key in ("event_log_path", "raw_xes_path", "running_trace_path"):
        if key in dataset and isinstance(dataset[key], str):
            dataset[key] = _resolve_path(dataset[key], root)
    out["dataset"] = dataset

    paths = dict(out.get("paths", {}))
    for key in (
        "artifact_dir",
        "knowledge_base_dir",
        "model_dir",
        "processed_feature_dir",
        "run_dir",
        "upload_dir",
    ):
        if key in paths and isinstance(paths[key], str):
            paths[key] = _resolve_path(paths[key], root)
    out["paths"] = paths
    return out


def load_config(config_path: str | None = None) -> AppConfig:
    root = _project_root()
    config_file = Path(config_path) if config_path else _default_config_path(root)
    if not config_file.is_absolute():
        config_file = (root / config_file).resolve()

    if not config_file.exists():
        return AppConfig()

    with open(config_file, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    resolved = _resolve_paths(raw, root)
    return AppConfig(**resolved)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config_dict(config_path: str | None = None) -> dict[str, Any]:
    """
    Load editable config dict (unresolved paths), merged with AppConfig defaults.
    """
    root = _project_root()
    config_file = Path(config_path) if config_path else _default_config_path(root)
    if not config_file.is_absolute():
        config_file = (root / config_file).resolve()

    defaults = AppConfig().model_dump()
    if not config_file.exists():
        return defaults

    with open(config_file, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raw = {}
    return _deep_merge(defaults, raw)


def save_config_dict(config_dict: dict[str, Any], config_path: str | None = None) -> Path:
    """
    Validate and persist YAML config. Stores raw (unresolved) relative values.
    """
    root = _project_root()
    config_file = Path(config_path) if config_path else _default_config_path(root)
    if not config_file.is_absolute():
        config_file = (root / config_file).resolve()

    merged = _deep_merge(AppConfig().model_dump(), config_dict or {})
    validated = AppConfig(**merged).model_dump()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(validated, f, sort_keys=False, allow_unicode=True)
    return config_file
