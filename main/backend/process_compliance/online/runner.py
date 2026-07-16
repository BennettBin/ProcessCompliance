from __future__ import annotations

import asyncio
import inspect
import json
import time
from pathlib import Path
from typing import Any, Callable, List, Optional
from uuid import uuid4

from backend.process_compliance.agents.event_stream import AgentEvent, create_agent_event
from backend.process_compliance.agents.service import AgentService
from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.data.io import load_running_trace
from backend.process_compliance.data.trace_converter import dataframe_to_trace_events, running_trace_to_text
from backend.process_compliance.data.validation import validate_event_log, validate_running_trace
from backend.process_compliance.knowledge.service import KnowledgeService
from backend.process_compliance.feature_learning.pipeline import main as build_knowledge_files
from backend.process_compliance.models.service import ModelService
from backend.process_compliance.online.result_schema import (
    AnalysisResult,
    AgentReview,
    ComplianceResult,
    PredictionResult,
)
from backend.process_compliance.prediction.service import PredictionService


class OnlineMonitoringService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.prediction_service = PredictionService(config)
        self.knowledge_service = KnowledgeService(config)
        self.model_service = ModelService(config)
        self.agent_service = AgentService(config)

    async def _emit(self, cb: Optional[Callable[..., Any]], event: AgentEvent, sink: List[AgentEvent]) -> None:
        sink.append(event)
        if cb is None:
            return
        out = cb(event)
        if inspect.isawaitable(out):
            await out

    @staticmethod
    def _map_current_status(decision: str) -> str:
        if decision == "yes":
            return "compliant"
        if decision == "no":
            return "non_compliant"
        return "unknown"

    @staticmethod
    def _map_future_risk(decision: str, confidence: Optional[float]) -> str:
        if decision == "unknown":
            return "unknown"
        if decision == "yes":
            if confidence is None:
                return "medium"
            if confidence >= 0.75:
                return "high"
            if confidence >= 0.45:
                return "medium"
            return "low"
        # decision == "no" means no predicted violation risk
        return "low"

    async def analyze(
        self,
        event_log_path: str,
        running_trace_path: str,
        dataset_name: str | None = None,
        run_id: str | None = None,
        emit_event=None,
        wait_if_paused=None,
    ) -> AnalysisResult:
        run_id = run_id or f"run_{uuid4().hex}"
        ds_name = dataset_name or self.config.dataset.name
        events: List[AgentEvent] = []
        step_started_at: dict[str, float] = {}

        step_scripts = {
            "model_preparation": "backend/process_compliance/models/service.py",
            "knowledge_base_preparation": "backend/process_compliance/feature_learning/pipeline.py",
            "data_validation": "backend/process_compliance/data/validation.py",
            "prediction": "backend/process_compliance/prediction/service.py",
            "retrieval": "backend/process_compliance/knowledge/service.py",
            "check_agent": "backend/process_compliance/agents/service.py",
            "predict_agent": "backend/process_compliance/agents/service.py",
            "summary_agent": "backend/process_compliance/agents/service.py",
            "final_result": "backend/process_compliance/online/runner.py",
        }
        default_secs = {
            "model_preparation": 20.0,
            "knowledge_base_preparation": 12.0,
            "data_validation": 2.0,
            "prediction": 6.0,
            "retrieval": 4.0,
            "check_agent": 10.0,
            "predict_agent": 10.0,
            "summary_agent": 8.0,
            "final_result": 1.0,
        }
        elapsed_real: dict[str, float] = {}
        visual_step_delay_seconds = 0.35

        def remaining_eta(current_step: Optional[str] = None) -> float:
            order = [
                "model_preparation",
                "knowledge_base_preparation",
                "data_validation",
                "prediction",
                "retrieval",
                "check_agent",
                "predict_agent",
                "summary_agent",
                "final_result",
            ]
            total = 0.0
            for s in order:
                if s in elapsed_real:
                    continue
                if current_step is not None and s == current_step and s in step_started_at:
                    total += max(default_secs[s] - (time.time() - step_started_at[s]), 0.0)
                else:
                    total += default_secs[s]
            return round(total, 2)

        await self._emit(
            emit_event,
            create_agent_event(
                run_id=run_id,
                type="run_started",
                step_name="pipeline",
                payload={
                    "dataset_name": ds_name,
                    "event_log_path": event_log_path,
                    "running_trace_path": running_trace_path,
                },
            ),
            events,
        )

        prediction = PredictionResult()
        current_trace = []
        trace_text = ""
        agent_review = AgentReview()
        compliance = ComplianceResult(current_status="unknown", future_risk="unknown")

        try:
            async def _wait():
                if wait_if_paused is None:
                    return
                out = wait_if_paused()
                if inspect.isawaitable(out):
                    await out

            # 0) model preparation
            await _wait()
            await self._emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="step_started",
                    step_name="model_preparation",
                    payload={
                        "script_file": step_scripts["model_preparation"],
                        "step_elapsed_seconds": 0.0,
                        "eta_remaining_seconds": remaining_eta("model_preparation"),
                    },
                ),
                events,
            )
            await asyncio.sleep(visual_step_delay_seconds)
            step_started_at["model_preparation"] = time.time()
            model_prepare = self.model_service.ensure_models_ready(ds_name)
            await self._emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="step_completed",
                    step_name="model_preparation",
                    payload={
                        "script_file": step_scripts["model_preparation"],
                        "step_elapsed_seconds": round(time.time() - step_started_at.get("model_preparation", time.time()), 2),
                        "eta_remaining_seconds": remaining_eta(),
                        "model_dir": model_prepare.model_dir,
                        "model_ready": model_prepare.ready,
                        "model_trained": model_prepare.trained,
                        "missing_models": model_prepare.missing_files,
                        "warnings": model_prepare.warnings,
                    },
                ),
                events,
            )
            await asyncio.sleep(visual_step_delay_seconds)
            elapsed_real["model_preparation"] = round(
                time.time() - step_started_at.get("model_preparation", time.time()), 2
            )

            # 0.5) knowledge base preparation
            await _wait()
            await self._emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="step_started",
                    step_name="knowledge_base_preparation",
                    payload={
                        "script_file": step_scripts["knowledge_base_preparation"],
                        "step_elapsed_seconds": 0.0,
                        "eta_remaining_seconds": remaining_eta("knowledge_base_preparation"),
                    },
                ),
                events,
            )
            await asyncio.sleep(visual_step_delay_seconds)
            step_started_at["knowledge_base_preparation"] = time.time()

            knowledge_dir = Path(self.config.paths.knowledge_base_dir)
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            rules_txt = knowledge_dir / f"declare_rules_{ds_name}.txt"
            log_info_txt = knowledge_dir / f"log_info_{ds_name}.txt"
            knowledge_built = False
            knowledge_warning = None

            if not (rules_txt.exists() and log_info_txt.exists()):
                try:
                    build_knowledge_files(data_name=ds_name, knowledge_base_dir=str(knowledge_dir))
                    knowledge_built = True
                except Exception as e:
                    knowledge_warning = f"Knowledge file build failed: {e}"

            # Build vectorstores if missing.
            self.knowledge_service.build_if_missing(ds_name)

            await self._emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="step_completed",
                    step_name="knowledge_base_preparation",
                    payload={
                        "script_file": step_scripts["knowledge_base_preparation"],
                        "step_elapsed_seconds": round(
                            time.time() - step_started_at.get("knowledge_base_preparation", time.time()), 2
                        ),
                        "eta_remaining_seconds": remaining_eta(),
                        "knowledge_base_dir": str(knowledge_dir),
                        "rules_txt_exists": rules_txt.exists(),
                        "log_info_txt_exists": log_info_txt.exists(),
                        "knowledge_files_built": knowledge_built,
                        "warning": knowledge_warning,
                    },
                ),
                events,
            )
            await asyncio.sleep(visual_step_delay_seconds)
            elapsed_real["knowledge_base_preparation"] = round(
                time.time() - step_started_at.get("knowledge_base_preparation", time.time()), 2
            )

            # 1) data validation
            await _wait()
            await self._emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="step_started",
                    step_name="data_validation",
                    payload={
                        "script_file": step_scripts["data_validation"],
                        "step_elapsed_seconds": 0.0,
                        "eta_remaining_seconds": remaining_eta("data_validation"),
                    },
                ),
                events,
            )
            await asyncio.sleep(visual_step_delay_seconds)
            step_started_at["data_validation"] = time.time()

            event_log_valid = validate_event_log(event_log_path)
            running_valid = validate_running_trace(running_trace_path)
            if not event_log_valid.valid or not running_valid.valid:
                err_msg = "; ".join(event_log_valid.errors + running_valid.errors)
                result = AnalysisResult(
                    run_id=run_id,
                    status="failed",
                    dataset_name=ds_name,
                    event_log_path=event_log_path,
                    running_trace_path=running_trace_path,
                    current_trace=[],
                    prediction=prediction,
                    compliance=compliance,
                    agent_review=agent_review,
                    message=f"Validation failed: {err_msg}",
                    meta={
                        "event_log_validation": event_log_valid.model_dump(),
                        "running_trace_validation": running_valid.model_dump(),
                    },
                )
                await self._emit(
                    emit_event,
                    create_agent_event(
                        run_id=run_id,
                        type="step_completed",
                        step_name="data_validation",
                        payload={
                            "valid": False,
                            "script_file": step_scripts["data_validation"],
                            "step_elapsed_seconds": round(time.time() - step_started_at.get("data_validation", time.time()), 2),
                            "eta_remaining_seconds": remaining_eta(),
                        },
                    ),
                    events,
                )
                elapsed_real["data_validation"] = round(
                    time.time() - step_started_at.get("data_validation", time.time()), 2
                )
                await self._emit(
                    emit_event,
                    create_agent_event(
                        run_id=run_id,
                        type="run_failed",
                        step_name="data_validation",
                        content=result.message,
                    ),
                    events,
                )
                self._save_outputs(run_id, result, events)
                return result

            df_trace = load_running_trace(running_trace_path)
            all_trace_events = dataframe_to_trace_events(df_trace)
            total_events = len(all_trace_events)
            if total_events == 0:
                raise ValueError("running_trace has no events after header.")
            current_trace = []
            trace_text = ""

            await self._emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="step_completed",
                    step_name="data_validation",
                    payload={
                        "valid": True,
                        "trace_events": total_events,
                        "script_file": step_scripts["data_validation"],
                        "step_elapsed_seconds": round(time.time() - step_started_at.get("data_validation", time.time()), 2),
                        "eta_remaining_seconds": remaining_eta(),
                    },
                ),
                events,
            )
            await asyncio.sleep(visual_step_delay_seconds)
            elapsed_real["data_validation"] = round(
                time.time() - step_started_at.get("data_validation", time.time()), 2
            )

            # Simulate running trace as unknown future events: process one event each iteration.
            for idx in range(total_events):
                await _wait()
                current_trace = all_trace_events[: idx + 1]
                prefix_df = df_trace.iloc[: idx + 1].copy()
                trace_text = running_trace_to_text(prefix_df)
                progress_payload = {
                    "trace_progress": {"current_event_index": idx + 1, "total_events": total_events},
                    "running_trace_text": trace_text,
                }

                # 2) prediction
                await _wait()
                await self._emit(
                    emit_event,
                    create_agent_event(
                        run_id=run_id,
                        type="step_started",
                        step_name="prediction",
                        payload={
                            "script_file": step_scripts["prediction"],
                            "step_elapsed_seconds": 0.0,
                            "eta_remaining_seconds": remaining_eta("prediction"),
                            **progress_payload,
                        },
                    ),
                    events,
                )
                await asyncio.sleep(visual_step_delay_seconds)
                step_started_at["prediction"] = time.time()
                prediction = self.prediction_service.predict(prefix_df)
                await self._emit(
                    emit_event,
                    create_agent_event(
                        run_id=run_id,
                        type="step_completed",
                        step_name="prediction",
                        payload={
                            "script_file": step_scripts["prediction"],
                            "step_elapsed_seconds": round(time.time() - step_started_at.get("prediction", time.time()), 2),
                            "eta_remaining_seconds": remaining_eta(),
                            **progress_payload,
                        },
                    ),
                    events,
                )
                await asyncio.sleep(visual_step_delay_seconds)
                elapsed_real["prediction"] = round(
                    time.time() - step_started_at.get("prediction", time.time()), 2
                )

                # 3) retrieval
                await _wait()
                await self._emit(
                    emit_event,
                    create_agent_event(
                        run_id=run_id,
                        type="step_started",
                        step_name="retrieval",
                        payload={
                            "script_file": step_scripts["retrieval"],
                            "step_elapsed_seconds": 0.0,
                            "eta_remaining_seconds": remaining_eta("retrieval"),
                            **progress_payload,
                        },
                    ),
                    events,
                )
                await asyncio.sleep(visual_step_delay_seconds)
                step_started_at["retrieval"] = time.time()
                rules = self.knowledge_service.search_rules(trace_text, top_k=5)
                logs = self.knowledge_service.search_log_info(trace_text, top_k=5)
                await self._emit(
                    emit_event,
                    create_agent_event(
                        run_id=run_id,
                        type="step_completed",
                        step_name="retrieval",
                        payload={
                            "rules": len(rules),
                            "log_infos": len(logs),
                            "script_file": step_scripts["retrieval"],
                            "step_elapsed_seconds": round(time.time() - step_started_at.get("retrieval", time.time()), 2),
                            "eta_remaining_seconds": remaining_eta(),
                            **progress_payload,
                        },
                    ),
                    events,
                )
                await asyncio.sleep(visual_step_delay_seconds)
                elapsed_real["retrieval"] = round(
                    time.time() - step_started_at.get("retrieval", time.time()), 2
                )

                # 4) agent checks with debate rounds (event-level simulation)
                for round_index in range(1, max(1, int(self.config.agent.max_rounds)) + 1):
                    await _wait()
                    await self._emit(
                        emit_event,
                        create_agent_event(
                            run_id=run_id,
                            type="debate_round_started",
                            step_name="debate",
                            round_index=round_index,
                            payload=progress_payload,
                        ),
                        events,
                    )
                    await asyncio.sleep(visual_step_delay_seconds)

                    check_decision = await self.agent_service.check_current_compliance(
                        running_trace_text=trace_text,
                        rule_text="\n".join([r.rule_text or "" for r in rules]),
                        run_id=run_id,
                        round_index=round_index,
                        emit_event=lambda e: self._emit(emit_event, e, events),
                    )
                    predict_decision = await self.agent_service.analyze_future_risk(
                        running_trace_text=trace_text,
                        predicted_status_text=prediction.model_dump_json(),
                        run_id=run_id,
                        round_index=round_index,
                        emit_event=lambda e: self._emit(emit_event, e, events),
                    )
                    summary_decision = await self.agent_service.summarize(
                        check_decision=check_decision,
                        predict_decision=predict_decision,
                        run_id=run_id,
                        round_index=round_index,
                        emit_event=lambda e: self._emit(emit_event, e, events),
                    )

                    await self._emit(
                        emit_event,
                        create_agent_event(
                            run_id=run_id,
                            type="debate_round_completed",
                            step_name="debate",
                            round_index=round_index,
                            payload={
                                "summary_decision": summary_decision.decision,
                                "summary_confidence": summary_decision.confidence,
                                **progress_payload,
                            },
                        ),
                        events,
                    )
                    await asyncio.sleep(visual_step_delay_seconds)

                    # Stop early when summary reaches explicit yes/no with enough confidence
                    if summary_decision.decision in {"yes", "no"} and (
                        summary_decision.confidence is None
                        or summary_decision.confidence >= float(self.config.agent.debate_threshold)
                    ):
                        break

            agent_review = AgentReview(
                check_agent=check_decision,
                predict_agent=predict_decision,
                summary_agent=summary_decision,
                debate_rounds=0,
                consensus_reached=summary_decision.decision in {"yes", "no"},
            )

            compliance = ComplianceResult(
                current_status=self._map_current_status(check_decision.decision),
                future_risk=self._map_future_risk(predict_decision.decision, predict_decision.confidence),
                violated_rules=rules if check_decision.decision == "no" else [],
                risk_rules=rules if predict_decision.decision == "yes" else [],
                summary=summary_decision.raw_response,
            )

            result = AnalysisResult(
                run_id=run_id,
                status="success",
                dataset_name=ds_name,
                event_log_path=event_log_path,
                running_trace_path=running_trace_path,
                current_trace=current_trace,
                prediction=prediction,
                compliance=compliance,
                agent_review=agent_review,
                meta={
                    "retrieved_rules": len(rules),
                    "retrieved_log_infos": len(logs),
                },
            )

            self._save_outputs(run_id, result, events)
            await self._emit(
                emit_event,
                create_agent_event(run_id=run_id, type="final_result", content=result.model_dump_json()),
                events,
            )
            await asyncio.sleep(visual_step_delay_seconds)
            await self._emit(
                emit_event,
                create_agent_event(run_id=run_id, type="run_completed", step_name="pipeline"),
                events,
            )
            return result

        except Exception as e:
            result = AnalysisResult(
                run_id=run_id,
                status="failed",
                dataset_name=ds_name,
                event_log_path=event_log_path,
                running_trace_path=running_trace_path,
                current_trace=current_trace,
                prediction=prediction,
                compliance=compliance,
                agent_review=agent_review,
                message=f"Pipeline failed: {e}",
            )
            self._save_outputs(run_id, result, events)
            await self._emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="run_failed",
                    step_name="pipeline",
                    content=result.message,
                ),
                events,
            )
            return result

    def _save_outputs(self, run_id: str, result: AnalysisResult, events: List[AgentEvent]) -> None:
        run_dir = Path(self.config.paths.run_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        report_path = run_dir / "final_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

        if events:
            events_path = run_dir / "agent_events.jsonl"
            with open(events_path, "w", encoding="utf-8") as f:
                for e in events:
                    f.write(e.model_dump_json() + "\n")

