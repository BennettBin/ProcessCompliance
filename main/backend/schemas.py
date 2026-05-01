from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class AnalyzeRequest(BaseModel):
    event_log_path: str
    running_trace_path: str
    dataset_name: Optional[str] = None
    config_path: Optional[str] = None


class AnalyzeResponse(BaseModel):
    run_id: str
    status: str
    result: Dict[str, Any]


class RunCreateRequest(BaseModel):
    event_log_path: str
    running_trace_path: str
    dataset_name: Optional[str] = None
    config_path: Optional[str] = None


class RunSummary(BaseModel):
    run_id: str
    status: str
    report_path: str


class RunListResponse(BaseModel):
    runs: List[RunSummary] = Field(default_factory=list)


class UploadResponse(BaseModel):
    file_path: str
    filename: str
    size: int


class SettingsPayload(BaseModel):
    dataset: Dict[str, Any] = Field(default_factory=dict)
    paths: Dict[str, Any] = Field(default_factory=dict)
    ollama: Dict[str, Any] = Field(default_factory=dict)
    agent: Dict[str, Any] = Field(default_factory=dict)
    prediction: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)


class SettingsResponse(BaseModel):
    config: Dict[str, Any]
    config_path: str
