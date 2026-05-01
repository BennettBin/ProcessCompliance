from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers.files import router as files_router
from backend.routers.health import router as health_router
from backend.routers.runs import router as runs_router
from backend.routers.settings import router as settings_router

app = FastAPI(title="ProcessCompliance Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Internal server error.",
            "details": {"error": str(exc)},
        },
    )


app.include_router(health_router)
app.include_router(runs_router)
app.include_router(files_router)
app.include_router(settings_router)
