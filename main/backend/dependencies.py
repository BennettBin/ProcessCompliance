from __future__ import annotations

from typing import Optional

from backend.process_compliance.config.loader import load_config
from backend.process_compliance.online.runner import OnlineMonitoringService

from backend.services.file_service import FileService
from backend.services.run_service import RunService

_RUN_SERVICE_SINGLETON = None


def get_config(config_path: Optional[str] = None):
    return load_config(config_path)


def get_online_monitoring_service(config_path: Optional[str] = None) -> OnlineMonitoringService:
    cfg = get_config(config_path)
    return OnlineMonitoringService(cfg)


def get_file_service(config_path: Optional[str] = None) -> FileService:
    cfg = get_config(config_path)
    return FileService(cfg)


def get_run_service(config_path: Optional[str] = None) -> RunService:
    global _RUN_SERVICE_SINGLETON
    if _RUN_SERVICE_SINGLETON is None:
        cfg = get_config(config_path)
        _RUN_SERVICE_SINGLETON = RunService(cfg)
    return _RUN_SERVICE_SINGLETON


def refresh_run_service_config(config_path: Optional[str] = None) -> RunService:
    global _RUN_SERVICE_SINGLETON
    cfg = get_config(config_path)
    if _RUN_SERVICE_SINGLETON is None:
        _RUN_SERVICE_SINGLETON = RunService(cfg)
    else:
        _RUN_SERVICE_SINGLETON.update_config(cfg)
    return _RUN_SERVICE_SINGLETON

