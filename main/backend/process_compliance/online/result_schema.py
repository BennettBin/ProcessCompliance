from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    case_id: Optional[str] = None
    activity: Optional[str] = None
    resource: Optional[str] = None
    role: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class PredictionResult(BaseModel):
    next_activity: Optional[str] = None
    next_activity_confidence: Optional[float] = None
    outcome: Optional[str] = None
    outcome_confidence: Optional[float] = None
    remaining_time: Optional[float] = None
    remaining_time_unit: Literal["seconds", "minutes", "hours", "days"] = "hours"
    debug_raw_text: Optional[str] = None


class RuleEvidence(BaseModel):
    rule_id: Optional[str] = None
    rule_text: Optional[str] = None
    matched: Optional[bool] = None
    confidence: Optional[float] = None
    evidence_text: Optional[str] = None
    source: Literal["rule_vectorstore", "log_vectorstore", "agent", "manual", "unknown"] = "unknown"


class ComplianceResult(BaseModel):
    current_status: Literal["compliant", "non_compliant", "unknown"] = "unknown"
    future_risk: Literal["high", "medium", "low", "unknown"] = "unknown"
    violated_rules: List[RuleEvidence] = Field(default_factory=list)
    risk_rules: List[RuleEvidence] = Field(default_factory=list)
    summary: Optional[str] = None


class AgentDecision(BaseModel):
    agent_name: Optional[str] = None
    decision: Literal["yes", "no", "unknown"] = "unknown"
    confidence: Optional[float] = None
    comment: Optional[str] = None
    raw_response: str = ""


class AgentReview(BaseModel):
    check_agent: Optional[AgentDecision] = None
    predict_agent: Optional[AgentDecision] = None
    summary_agent: Optional[AgentDecision] = None
    rule_check_agent: Optional[AgentDecision] = None
    second_check_agent: Optional[AgentDecision] = None
    debate_rounds: int = 0
    consensus_reached: bool = False


class AnalysisResult(BaseModel):
    run_id: str
    status: Literal["success", "partial_success", "failed"] = "success"
    dataset_name: str
    event_log_path: str
    running_trace_path: str
    current_trace: List[TraceEvent] = Field(default_factory=list)
    prediction: PredictionResult = Field(default_factory=PredictionResult)
    compliance: ComplianceResult = Field(default_factory=ComplianceResult)
    agent_review: AgentReview = Field(default_factory=AgentReview)
    message: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


def parse_prediction_text(raw_text: str, remaining_time_unit: Literal["seconds", "minutes", "hours", "days"] = "hours") -> PredictionResult:
    """Best-effort parser for legacy free-text prediction output."""
    text = raw_text or ""

    def _pick(pattern: str) -> Optional[str]:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        v = m.group(1).strip()
        if v.lower() in {"none", "null", "unknown", ""}:
            return None
        return v

    def _to_float(v: Optional[str]) -> Optional[float]:
        if v is None:
            return None
        try:
            return float(v)
        except Exception:
            return None

    next_activity = _pick(r"next activity.*?is\s+(.+?)\s+and the confidence")
    next_conf = _to_float(_pick(r"next activity.*?confidence.*?([01](?:\.\d+)?)"))
    outcome = _pick(r"predicted outcome.*?is\s+(.+?)\s+and the confidence")
    outcome_conf = _to_float(_pick(r"outcome.*?confidence.*?([01](?:\.\d+)?)"))
    remaining_time = _to_float(_pick(r"remaining execution time.*?is\s+([+-]?\d+(?:\.\d+)?)"))

    return PredictionResult(
        next_activity=next_activity,
        next_activity_confidence=next_conf,
        outcome=outcome,
        outcome_confidence=outcome_conf,
        remaining_time=remaining_time,
        remaining_time_unit=remaining_time_unit,
    )
