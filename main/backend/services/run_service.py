from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from backend.schemas import AnalyzeRequest, RunSummary
from backend.process_compliance.agents.event_stream import AgentEvent, create_agent_event
from backend.process_compliance.online.result_schema import AnalysisResult
from backend.process_compliance.online.runner import OnlineMonitoringService


@dataclass
class RunState:
    run_id: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    events: List[AgentEvent] = field(default_factory=list)
    status: str = "created"
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
    request: Optional[AnalyzeRequest] = None
    paused: bool = False
    next_seq: int = 1
    stream_connected: bool = False


class RunService:
    def __init__(self, config):
        self.config = config
        self.run_root = Path(config.paths.run_dir)
        self.run_root.mkdir(parents=True, exist_ok=True)
        self.monitor = OnlineMonitoringService(config)
        self._runs: Dict[str, RunState] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._lock = threading.Lock()

    def update_config(self, config) -> None:
        self.config = config
        self.run_root = Path(config.paths.run_dir)
        self.run_root.mkdir(parents=True, exist_ok=True)
        self.monitor = OnlineMonitoringService(config)

    async def create_run(self, request: AnalyzeRequest) -> str:
        run_id = f"run_{uuid4().hex}"
        state = RunState(run_id=run_id, status="queued", request=request)
        with self._lock:
            self._runs[run_id] = state
        return run_id

    async def start_run(self, run_id: str) -> None:
        state = self._runs.get(run_id)
        if state is None or state.request is None:
            return
        # Give frontend a short window to attach SSE/polling subscription,
        # so users can see events progressively instead of full replay.
        waited = 0.0
        while waited < 3.0:
            current = self._runs.get(run_id)
            if current is None:
                return
            if current.stream_connected:
                break
            await asyncio.sleep(0.05)
            waited += 0.05

        state.status = "running"

        async def _emit(event: AgentEvent):
            await self.emit_event(run_id, event)

        async def _wait_if_paused():
            while True:
                current = self._runs.get(run_id)
                if current is None or not current.paused:
                    break
                await asyncio.sleep(0.25)

        try:
            req = state.request
            result = await self.monitor.analyze(
                event_log_path=req.event_log_path,
                running_trace_path=req.running_trace_path,
                dataset_name=req.dataset_name,
                run_id=run_id,
                emit_event=_emit,
                wait_if_paused=_wait_if_paused,
            )
            state.result = result
            state.status = result.status
            if result.status == "failed":
                state.error = result.message
        except Exception as e:
            state.status = "failed"
            state.error = str(e)
            failed = create_agent_event(
                run_id=run_id,
                type="run_failed",
                step_name="pipeline",
                content=f"Run crashed: {e}",
            )
            await self.emit_event(run_id, failed)

    def launch_run(self, run_id: str) -> None:
        # Launch background execution in current event loop, independent from FastAPI BackgroundTasks.
        if run_id in self._tasks:
            t = self._tasks[run_id]
            if not t.done():
                return
        task = asyncio.create_task(self.start_run(run_id), name=f"run:{run_id}")
        self._tasks[run_id] = task

    async def emit_event(self, run_id: str, event: AgentEvent) -> None:
        state = self._runs.get(run_id)
        if state is None:
            return
        # Assign monotonic sequence for lossless replay/resume.
        payload = dict(event.payload or {})
        if "event_seq" not in payload:
            payload["event_seq"] = state.next_seq
            state.next_seq += 1
        event.payload = payload
        state.events.append(event)
        await state.queue.put(event)
        self._persist_event(run_id, event)

    async def stream_events(self, run_id: str, since_seq: int = 0) -> AsyncGenerator[str, None]:
        state = self._runs.get(run_id)
        if state is None:
            err = create_agent_event(
                run_id=run_id,
                type="run_failed",
                step_name="stream",
                content=f"run_id not found: {run_id}",
            )
            yield f"data: {err.model_dump_json()}\n\n"
            return
        state.stream_connected = True

        # Replay all events that happened before this stream connection.
        replay_idx = 0
        while replay_idx < len(state.events):
            event = state.events[replay_idx]
            replay_idx += 1
            seq = int((event.payload or {}).get("event_seq", 0))
            if seq <= since_seq:
                continue
            yield f"id: {seq}\n"
            yield f"data: {event.model_dump_json()}\n\n"
            if event.type in {"run_completed", "run_failed"}:
                return

        # Continue streaming new events.
        # Send periodic heartbeat comments to keep SSE connection alive during long steps.
        while True:
            try:
                event: AgentEvent = await asyncio.wait_for(state.queue.get(), timeout=10.0)
            except asyncio.TimeoutError:
                # SSE comment frame (ignored by EventSource onmessage) as keepalive.
                yield ": keepalive\n\n"
                continue
            seq = int((event.payload or {}).get("event_seq", 0))
            if seq <= since_seq:
                continue
            yield f"id: {seq}\n"
            yield f"data: {event.model_dump_json()}\n\n"
            if event.type in {"run_completed", "run_failed"}:
                break

    def get_run(self, run_id: str) -> Optional[AnalysisResult]:
        state = self._runs.get(run_id)
        if state and state.result is not None:
            return state.result
        report = self.run_root / run_id / "final_report.json"
        if report.exists():
            try:
                with open(report, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                return AnalysisResult(**obj)
            except Exception:
                return None
        return None

    def get_run_state(self, run_id: str) -> Optional[RunState]:
        return self._runs.get(run_id)

    def get_run_events(self, run_id: str) -> List[AgentEvent]:
        state = self._runs.get(run_id)
        if state is not None:
            state.stream_connected = True
            return list(state.events)
        events_file = self.run_root / run_id / "agent_events.jsonl"
        if not events_file.exists():
            return []
        out: List[AgentEvent] = []
        with open(events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(AgentEvent.model_validate_json(line))
                except Exception:
                    continue
        return out

    async def pause_run(self, run_id: str) -> bool:
        state = self._runs.get(run_id)
        if state is None:
            return False
        state.paused = True
        await self.emit_event(
            run_id,
            create_agent_event(run_id=run_id, type="step_started", step_name="paused", content="Run paused by user."),
        )
        return True

    async def resume_run(self, run_id: str) -> bool:
        state = self._runs.get(run_id)
        if state is None:
            return False
        state.paused = False
        await self.emit_event(
            run_id,
            create_agent_event(run_id=run_id, type="step_completed", step_name="paused", content="Run resumed by user."),
        )
        return True

    def list_runs(self) -> List[RunSummary]:
        runs: List[RunSummary] = []

        # in-memory runs
        for run_id, state in self._runs.items():
            report_path = str(self.run_root / run_id / "final_report.json")
            runs.append(RunSummary(run_id=run_id, status=state.status, report_path=report_path))

        # filesystem fallback runs
        memory_ids = {r.run_id for r in runs}
        for p in sorted(self.run_root.glob("run_*")):
            if not p.is_dir() or p.name in memory_ids:
                continue
            report = p / "final_report.json"
            status = "unknown"
            if report.exists():
                try:
                    with open(report, "r", encoding="utf-8") as f:
                        obj = json.load(f)
                    status = obj.get("status", "unknown")
                except Exception:
                    status = "unknown"
            runs.append(RunSummary(run_id=p.name, status=status, report_path=str(report)))
        return runs

    def _persist_event(self, run_id: str, event: AgentEvent) -> None:
        run_dir = self.run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        events_path = run_dir / "agent_events.jsonl"
        with open(events_path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

