from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable, Optional

from backend.process_compliance.config.loader import load_config

EmitEvent = Optional[Callable[..., Any]]


def build_agent(temperature: float, tools=None, system_prompt=None):
    if tools is None:
        tools = []
    cfg = load_config()
    from langchain_ollama import ChatOllama
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import MemorySaver

    llm = ChatOllama(
        model=cfg.ollama.chat_model,
        temperature=temperature,
    )
    return create_agent(
        model=llm,
        tools=tools,
        checkpointer=MemorySaver(),
        system_prompt=system_prompt,
    )


def build_struct_agent(temperature: float, output_format):
    cfg = load_config()
    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model=cfg.ollama.chat_model,
        temperature=temperature,
    )
    return llm.with_structured_output(output_format)


async def maybe_emit(emit_event: EmitEvent, event) -> None:
    if emit_event is None:
        return
    out = emit_event(event)
    if inspect.isawaitable(out):
        await out


def invoke_agent_sync(agent, thread_id: str, prompt: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
    return result["messages"][-1].content


def stream_agent_sync(agent, thread_id: str, prompt: str):
    config = {"configurable": {"thread_id": thread_id}}
    latest_text = ""
    printed_len = 0
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config,
        stream_mode="values",
    ):
        msg_list = chunk.get("messages", [])
        if not msg_list:
            continue
        maybe_text = getattr(msg_list[-1], "content", "")
        if isinstance(maybe_text, str):
            latest_text = maybe_text
        elif isinstance(maybe_text, list):
            latest_text = "".join(item.get("text", "") for item in maybe_text if isinstance(item, dict))
        else:
            latest_text = str(maybe_text)

        delta = ""
        if len(latest_text) > printed_len:
            delta = latest_text[printed_len:]
            printed_len = len(latest_text)
        yield delta, latest_text


__all__ = ["build_agent", "build_struct_agent", "maybe_emit", "invoke_agent_sync", "stream_agent_sync"]

