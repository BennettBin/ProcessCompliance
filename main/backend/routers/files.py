from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.dependencies import get_file_service
from backend.schemas import UploadResponse

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_service=Depends(get_file_service),
):
    try:
        saved_path, size = await file_service.save_upload(file)
        return UploadResponse(file_path=saved_path, filename=file.filename, size=size)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "UPLOAD_FAILED", "message": "File upload failed.", "details": {"error": str(e)}},
        )
