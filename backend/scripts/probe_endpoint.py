"""Probe the OpenAI-compatible endpoint: native tools support + JSON stability.

Usage (from repo root, consumes 6-7 metered calls):
    backend/.venv/Scripts/python backend/scripts/probe_endpoint.py
"""
from __future__ import annotations

import json

from hindsight.llm.client import LLMConfig, openai_transport

TOOL = {
    "type": "function",
    "function": {
        "name": "get_price",
        "description": "Get the latest price for a ticker",
        "parameters": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
}

JSON_PROMPT = (
    "Return ONLY a JSON object (no markdown fence, no prose) with keys: "
    '"action" (string, one of "search"|"finish"), "query" (string), '
    '"confidence" (number 0..1). Topic: NVDA earnings preview.'
)


def probe_native_tools(send) -> bool:
    try:
        resp = send(
            {
                "model": LLMConfig.from_env().model,
                "messages": [{"role": "user", "content": "What is the price of NVDA? Use the tool."}],
                "tools": [TOOL],
                "temperature": 0.0,
            }
        )
        calls = resp["choices"][0]["message"].get("tool_calls")
        if not calls:
            print("native tools: NO tool_calls in response")
            return False
        args = json.loads(calls[0]["function"]["arguments"])
        ok = calls[0]["function"]["name"] == "get_price" and "ticker" in args
        print(f"native tools: tool_calls present, well-formed={ok}: {calls[0]}")
        return ok
    except Exception as exc:  # noqa: BLE001 - probe reports everything
        print(f"native tools: FAILED ({type(exc).__name__}: {exc})")
        return False


def probe_json_stability(send, n: int = 5) -> int:
    cfg = LLMConfig.from_env()
    valid = 0
    for i in range(n):
        resp = send(
            {
                "model": cfg.model,
                "messages": [{"role": "user", "content": JSON_PROMPT + f" (attempt {i})"}],
                "temperature": 0.2,
            }
        )
        text = resp["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        try:
            obj = json.loads(text)
            assert obj["action"] in ("search", "finish")
            assert isinstance(obj["confidence"], (int, float))
            valid += 1
            print(f"json attempt {i}: valid")
        except Exception as exc:  # noqa: BLE001
            print(f"json attempt {i}: INVALID ({exc}) raw={text[:120]!r}")
    return valid


def main() -> None:
    cfg = LLMConfig.from_env()
    send = openai_transport(cfg)
    print(f"probing {cfg.base_url} model={cfg.model}\n")
    tools_ok = probe_native_tools(send)
    valid = probe_json_stability(send)
    print(f"\nRESULT: native_tools={tools_ok}, json_valid={valid}/5")
    decision = "native function calling" if tools_ok else "prompt-JSON action format"
    print(f"DECISION for D2 planner: {decision}")
    print("Record this in docs/eval-log.md.")


if __name__ == "__main__":
    main()
