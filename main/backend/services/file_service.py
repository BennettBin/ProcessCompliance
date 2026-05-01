from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile


class FileService:
    def __init__(self, config):
        self.config = config
        self.upload_dir = Path(config.paths.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> tuple[str, int]:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".csv", ".xes"}:
            raise ValueError("Unsupported file extension. Please upload a .csv file (or .xes if enabled).")

        dst = self.upload_dir / file.filename
        content = await file.read()
        with open(dst, "wb") as f:
            f.write(content)
        return str(dst).replace("\\", "/"), len(content)
