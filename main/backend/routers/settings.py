from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.dependencies import refresh_run_service_config
from backend.process_compliance.config.loader import load_config_dict, save_config_dict
from backend.schemas import SettingsPayload, SettingsResponse

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
def get_settings(config_path: Optional[str] = Query(default=None)):
    try:
        cfg = load_config_dict(config_path)
        root = Path(__file__).resolve().parents[2]
        p = Path(config_path) if config_path else (root / "configs" / "default.yaml")
        if not p.is_absolute():
            p = (root / p).resolve()
        return SettingsResponse(config=cfg, config_path=str(p))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "SETTINGS_GET_FAILED", "message": "Load settings failed.", "details": {"error": str(e)}},
        )


@router.put("/settings", response_model=SettingsResponse)
def update_settings(payload: SettingsPayload, config_path: Optional[str] = Query(default=None)):
    try:
        saved_path = save_config_dict(payload.model_dump(), config_path=config_path)
        refresh_run_service_config(config_path=config_path)
        cfg = load_config_dict(str(saved_path))
        return SettingsResponse(config=cfg, config_path=str(saved_path))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "SETTINGS_UPDATE_FAILED", "message": "Save settings failed.", "details": {"error": str(e)}},
        )
