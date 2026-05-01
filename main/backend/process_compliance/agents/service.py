from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from backend.process_compliance.agents.base import build_agent, invoke_agent_sync, maybe_emit, stream_agent_sync
from backend.process_compliance.agents.check_agent import build_check_prompt
from backend.process_compliance.agents.debate import parse_consensus_confidence
from backend.process_compliance.agents.event_stream import create_agent_event
from backend.process_compliance.agents.predict_agent import build_predict_prompt
from backend.process_compliance.agents.summary_agent import build_summary_prompt
from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.online.result_schema import AgentDecision


class AgentService:
    def __init__(self, config: AppConfig):
        self.config = config
        self._init_error: Optional[str] = None
        try:
            self.check_agent = build_agent(temperature=0.2)
            self.predict_agent = build_agent(temperature=0.2)
            self.summary_agent = build_agent(temperature=0.0)
        except Exception as e:
            # Keep service import/initialization alive; methods will return controlled unknown decisions.
            self._init_error = str(e)
            self.check_agent = None
            self.predict_agent = None
            self.summary_agent = None

    async def _invoke_with_events(
        self,
        *,
        run_id: str,
        agent_name: str,
        thread_id: str,
        prompt: str,
        emit_event=None,
        round_index: Optional[int] = None,
        step_name: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> str:
        step_script = "process_compliance/agents/service.py"
        step_eta = {"check_current_compliance": 10.0, "analyze_future_risk": 10.0, "summarize": 8.0}.get(step_name or "", 8.0)
        base_payload = {"script_file": step_script, "eta_remaining_seconds": step_eta}
        if payload:
            base_payload.update(payload)

        await maybe_emit(
            emit_event,
            create_agent_event(
                run_id=run_id,
                type="agent_started",
                agent_name=agent_name,
                round_index=round_index,
                step_name=step_name,
                payload={**base_payload, "prompt": prompt},
            ),
        )

        final_text = ""
        if self._agent_by_name(agent_name) is None:
            final_text = f"Agent backend unavailable: {self._init_error or 'unknown initialization error'}"
            await maybe_emit(
                emit_event,
                create_agent_event(
                    run_id=run_id,
                    type="agent_message_completed",
                    agent_name=agent_name,
                    round_index=round_index,
                    step_name=step_name,
                    content=final_text,
                    payload={"raw_response": final_text, "script_file": step_script, "eta_remaining_seconds": 0.0},
                ),
            )
            return final_text

        streamed = False
        try:
            for delta, latest_text in stream_agent_sync(
                agent=self._agent_by_name(agent_name),
                thread_id=thread_id,
                prompt=prompt,
            ):
                streamed = True
                final_text = latest_text
                if delta:
                    await maybe_emit(
                        emit_event,
                        create_agent_event(
                            run_id=run_id,
                            type="agent_token",
                            agent_name=agent_name,
                            round_index=round_index,
                            step_name=step_name,
                            partial_content=delta,
                        ),
                    )
        except Exception:
            # streaming not available; fallback to one-shot invoke
            streamed = False

        if not streamed:
            final_text = invoke_agent_sync(
                self._agent_by_name(agent_name),
                thread_id=thread_id,
                prompt=prompt,
            )

        await maybe_emit(
            emit_event,
            create_agent_event(
                run_id=run_id,
                type="agent_message_completed",
                agent_name=agent_name,
                round_index=round_index,
                step_name=step_name,
                content=final_text,
                payload={"raw_response": final_text, "script_file": step_script, "eta_remaining_seconds": 0.0},
            ),
        )
        return final_text

    def _agent_by_name(self, name: str):
        if name == "check_agent":
            return self.check_agent
        if name == "predict_agent":
            return self.predict_agent
        return self.summary_agent

    @staticmethod
    def _to_decision(agent_name: str, raw_text: str) -> AgentDecision:
        try:
            decision, confidence = parse_consensus_confidence(raw_text or "")
            return AgentDecision(
                agent_name=agent_name,
                decision=decision,
                confidence=confidence,
                comment=raw_text,
                raw_response=raw_text or "",
            )
        except Exception:
            return AgentDecision(
                agent_name=agent_name,
                decision="unknown",
                confidence=None,
                comment=raw_text,
                raw_response=raw_text or "",
            )

    async def check_current_compliance(
        self,
        *,
        running_trace_text: str,
        rule_text: str,
        question: str = "Check current compliance.",
        run_id: Optional[str] = None,
        emit_event=None,
        round_index: Optional[int] = None,
    ) -> AgentDecision:
        run_id = run_id or f"run_{uuid4().hex}"
        prompt = build_check_prompt(running_trace_text, rule_text, question)
        raw = await self._invoke_with_events(
            run_id=run_id,
            agent_name="check_agent",
            thread_id=f"{run_id}::check_agent",
            prompt=prompt,
            emit_event=emit_event,
            round_index=round_index,
            step_name="check_current_compliance",
        )
        return self._to_decision("check_agent", raw)

    async def analyze_future_risk(
        self,
        *,
        running_trace_text: str,
        predicted_status_text: str,
        question: str = "Analyze future compliance risk.",
        run_id: Optional[str] = None,
        emit_event=None,
        round_index: Optional[int] = None,
    ) -> AgentDecision:
        run_id = run_id or f"run_{uuid4().hex}"
        prompt = build_predict_prompt(running_trace_text, predicted_status_text, question)
        raw = await self._invoke_with_events(
            run_id=run_id,
            agent_name="predict_agent",
            thread_id=f"{run_id}::predict_agent",
            prompt=prompt,
            emit_event=emit_event,
            round_index=round_index,
            step_name="analyze_future_risk",
        )
        return self._to_decision("predict_agent", raw)

    async def summarize(
        self,
        *,
        check_decision: AgentDecision,
        predict_decision: AgentDecision,
        question: str = "Provide final summary.",
        run_id: Optional[str] = None,
        emit_event=None,
        round_index: Optional[int] = None,
    ) -> AgentDecision:
        run_id = run_id or f"run_{uuid4().hex}"
        prompt = build_summary_prompt(
            check_text=check_decision.raw_response,
            predict_text=predict_decision.raw_response,
            question=question,
        )
        raw = await self._invoke_with_events(
            run_id=run_id,
            agent_name="summary_agent",
            thread_id=f"{run_id}::summary_agent",
            prompt=prompt,
            emit_event=emit_event,
            round_index=round_index,
            step_name="summarize",
        )
        return self._to_decision("summary_agent", raw)

