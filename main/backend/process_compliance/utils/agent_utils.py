from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver

TZ = ZoneInfo("America/New_York")

CONSENSUS_RE = re.compile(r"CONSENSUS:\s*(YES|NO)\b", re.IGNORECASE)
CONF_RE = re.compile(r"CONFIDENCE:\s*([01](?:\.\d+)?)", re.IGNORECASE)


def ensure_json_file(path: str) -> None:
    if not os.path.exists(path):
        init_data = {"threads": {}}
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(init_data, f, ensure_ascii=False, indent=2)


def load_log(path: str) -> dict:
    ensure_json_file(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"threads": {}}
        if "threads" not in data or not isinstance(data["threads"], dict):
            data["threads"] = {}
        return data
    except json.JSONDecodeError:
        return {"threads": {}}


def atomic_write_json(path: str, data: dict) -> None:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def append_record(path: str, thread_id: str, record: Dict[str, Any]) -> None:
    data = load_log(path)
    threads = data.setdefault("threads", {})
    turns = threads.setdefault(thread_id, [])
    turns.append(record)
    atomic_write_json(path, data)


def now_ts() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_thread_records(path: str, thread_id: str) -> List[Dict[str, Any]]:
    data = load_log(path)
    threads = data.get("threads", {})
    records = threads.get(thread_id, [])
    return records if isinstance(records, list) else []


def build_agent(temperature: float, tools=None, system_prompt=None):
    if tools is None:
        tools = []
    llm = ChatOllama(model="qwen3:8b", temperature=temperature)
    return create_agent(
        model=llm,
        tools=tools,
        checkpointer=MemorySaver(),
        system_prompt=system_prompt,
    )


def build_struct_agent(temperature: float, output_format):
    llm = ChatOllama(model="qwen3:8b", temperature=temperature)
    return llm.with_structured_output(output_format)


def agent_invoke(agent, thread_id: str, messages: List[Dict[str, str]]) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": messages}, config=config)
    return result["messages"][-1].content


def parse_consensus(txt: str) -> Tuple[bool, Optional[float]]:
    m = CONSENSUS_RE.search(txt)
    consensus = (m.group(1).upper() == "YES") if m else False
    c = CONF_RE.search(txt)
    conf = float(c.group(1)) if c else None
    return consensus, conf


def format_history_for_bootstrap(
    records: List[Dict[str, Any]],
    max_items: int = 40,
    max_chars: int = 12000,
) -> str:
    if not records:
        return ""
    recent = records[-max_items:]
    lines = []
    for message in recent:
        speaker = message.get("speaker", "unknown")
        content = message.get("content", "")
        rtype = message.get("type", "")
        if not content:
            continue
        tag = speaker
        if rtype == "final_answer":
            tag = "final(system)"
        elif rtype == "user_question":
            tag = "user"
        elif speaker == "check_agent":
            tag = "check_agent"
        elif speaker == "predict_agent":
            tag = "predict_agent"
        elif speaker == "summary_checker":
            tag = "summary_checker"
        lines.append(f"[{tag}] {content}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[-max_chars:]
    return text


def bootstrap_agent_from_json(
    agent,
    agent_thread_id: str,
    history_text: str,
    agent_name: str,
) -> None:
    if not history_text.strip():
        return
    system_msg = f"""
    You are {agent_name}. Below is a replay of this user's previous conversations.
    Please treat this as a past conversation and maintain consistency in your subsequent responses.
    If the user mentions 'just now/before/we talked', prioritize this history.

    === History Begins ===
    {history_text}
    === History Ends ===
    """
    _ = agent_invoke(
        agent,
        agent_thread_id,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": "Please reply only with: ACK"},
        ],
    )

