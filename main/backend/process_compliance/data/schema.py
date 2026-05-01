from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    valid: bool = False
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    file_path: str = ""
    file_type: str = "csv"
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)

