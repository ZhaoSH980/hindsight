"""Bounded ReAct planner: native function calling, deterministic dispatch.

The loop is a plain for-range — the LLM decides WHAT to call, never HOW
often the loop spins (spec §3.1: determinism over autonomy)."""
from __future__ import annotations

import json
from typing import Any

from hindsight.agents.prompts import PLANNER_SYSTEM
from hindsight.llm.recording import RecordingLLMClient
from hindsight.tools.registry import ToolRegistry, ToolSpec, safe_call
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder

FINISH_TOOL = ToolSpec(
    name="finish_research",
    description="Call when the gathered evidence is sufficient to write the memo.",
    parameters={
        "type": "object",
        "properties": {"reason": {"type": "string"}},
        "required": ["reason"],
    },
    fn=lambda reason="done": json.dumps({"ok": True, "reason": reason}),
)


def run_planner(
    llm: RecordingLLMClient,
    registry: ToolRegistry,
    user_brief: str,
    max_steps: int,
    temperature: float,
    trace: TraceRecorder,
    ledger: CostLedger,
) -> None:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": user_brief},
    ]
    tools = registry.openai_specs()
    for step in range(max_steps):
        # Snapshot: RecordingLLMClient/ScriptedTransport keep a reference to
        # whatever list we pass. Since `messages` is mutated in place after
        # each call, passing it by reference would let later mutations leak
        # into earlier recorded requests (they'd all end up pointing at the
        # same, fully-grown list). A shallow copy freezes this step's view.
        resp = llm.chat(messages=list(messages), tools=tools, temperature=temperature)
        usage = resp.get("usage") or {}
        ledger.add(
            "planner", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        )
        msg = resp["choices"][0]["message"]
        calls = msg.get("tool_calls") or []
        trace.emit(
            TraceEvent(
                type="plan_step",
                agent="planner",
                payload={
                    "step": step,
                    "thought": msg.get("content") or "",
                    "n_tool_calls": len(calls),
                },
                tokens=usage.get("completion_tokens", 0),
            )
        )
        if not calls:
            break  # model answered in prose; planning ends
        messages.append(
            {"role": "assistant", "content": msg.get("content"), "tool_calls": calls}
        )
        finished = False
        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError as exc:
                args = {}
                result = json.dumps({"error": f"unparseable arguments: {exc}"})
            else:
                result = safe_call(registry, name, args)
            trace.emit(
                TraceEvent(
                    type="tool_call", agent="planner", payload={"tool": name, "args": args}
                )
            )
            trace.emit(
                TraceEvent(
                    type="tool_result",
                    agent="planner",
                    payload={"tool": name, "result": result[:2000]},
                )
            )
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": result}
            )
            if name == "finish_research":
                finished = True
        if finished:
            break
