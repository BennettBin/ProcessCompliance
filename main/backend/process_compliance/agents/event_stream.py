from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


AgentEventType = Literal[
    "run_started",
    "run_completed",
    "run_failed",
    "step_started",
    "step_completed",
    "agent_started",
    "agent_token",
    "agent_message_completed",
    "debate_round_started",
    "debate_round_completed",
    "final_result",
]


class AgentEvent(BaseModel):
    run_id: str
    event_id: str
    timestamp: str
    type: AgentEventType
    agent_name: Optional[str] = None
    round_index: Optional[int] = None
    step_name: Optional[str] = None
    content: Optional[str] = None
    partial_content: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


def create_agent_event(run_id: str, type: str, **kwargs) -> AgentEvent:
    event_type = type
    event_id = kwargs.pop("event_id", f"evt_{uuid4().hex}")
    timestamp = kwargs.pop("timestamp", datetime.now(timezone.utc).isoformat())

    return AgentEvent(
        run_id=run_id,
        event_id=event_id,
        timestamp=timestamp,
        type=event_type,  # validated by AgentEventType
        **kwargs,
    )

