from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from backend.dependencies import get_run_service
from backend.schemas import AnalyzeRequest, AnalyzeResponse, RunListResponse

router = APIRouter(prefix="/api", tags=["runs"])


@router.post("/runs")
async def create_run(req: AnalyzeRequest, run_service=Depends(get_run_service)):
    try:
        run_id = await run_service.create_run(req)
        run_service.launch_run(run_id)
        return {"run_id": run_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "RUN_CREATE_FAILED", "message": "Run creation failed.", "details": {"error": str(e)}},
        )


@router.get("/runs/{run_id}/stream")
async def stream_run_events(
    run_id: str,
    request: Request,
    since: int = Query(0, ge=0),
    run_service=Depends(get_run_service),
):
    try:
        last_event_id = request.headers.get("last-event-id")
        since_seq = since
        if last_event_id is not None:
            try:
                since_seq = max(since_seq, int(last_event_id))
            except ValueError:
                pass
        generator = run_service.stream_events(run_id, since_seq=since_seq)
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "RUN_STREAM_FAILED", "message": "Run stream failed.", "details": {"error": str(e)}},
        )


@router.get("/runs/{run_id}")
def get_run(run_id: str, run_service=Depends(get_run_service)):
    try:
        result = run_service.get_run(run_id)
        if result is not None:
            return {"run_id": run_id, "status": result.status, "result": result.model_dump()}
        state = run_service.get_run_state(run_id)
        if state is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "RUN_NOT_FOUND", "message": f"Run not found: {run_id}", "details": {"run_id": run_id}},
            )
        return {"run_id": run_id, "status": state.status, "result": None, "error": state.error}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "RUN_GET_FAILED", "message": "Get run failed.", "details": {"error": str(e)}},
        )


@router.get("/runs/{run_id}/events")
def get_run_events(run_id: str, run_service=Depends(get_run_service)):
    try:
        events = run_service.get_run_events(run_id)
        state = run_service.get_run_state(run_id)
        return {
            "run_id": run_id,
            "status": state.status if state else "unknown",
            "error": state.error if state else None,
            "events": [e.model_dump() for e in events],
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "RUN_EVENTS_FAILED", "message": "Get run events failed.", "details": {"error": str(e)}},
        )


@router.post("/runs/{run_id}/pause")
async def pause_run(run_id: str, run_service=Depends(get_run_service)):
    ok = await run_service.pause_run(run_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail={"code": "RUN_NOT_FOUND", "message": f"Run not found: {run_id}", "details": {"run_id": run_id}},
        )
    return {"run_id": run_id, "status": "paused"}


@router.post("/runs/{run_id}/resume")
async def resume_run(run_id: str, run_service=Depends(get_run_service)):
    ok = await run_service.resume_run(run_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail={"code": "RUN_NOT_FOUND", "message": f"Run not found: {run_id}", "details": {"run_id": run_id}},
        )
    return {"run_id": run_id, "status": "running"}


@router.get("/runs", response_model=RunListResponse)
def list_runs(run_service=Depends(get_run_service)):
    try:
        return RunListResponse(runs=run_service.list_runs())
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "RUN_LIST_FAILED", "message": "List runs failed.", "details": {"error": str(e)}},
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_now(req: AnalyzeRequest, run_service=Depends(get_run_service)):
    """
    Compatibility endpoint: still available for one-shot behavior.
    Internally uses run creation/start and then waits for completion.
    """
    try:
        run_id = await run_service.create_run(req)
        await run_service.start_run(run_id)
        result = run_service.get_run(run_id)
        if result is None:
            return AnalyzeResponse(run_id=run_id, status="failed", result={"message": "No result generated."})
        return AnalyzeResponse(run_id=run_id, status=result.status, result=result.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "ANALYZE_FAILED", "message": "Analysis failed.", "details": {"error": str(e)}},
        )
