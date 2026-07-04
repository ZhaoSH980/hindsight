"""Scripted fake LLM transports for agent tests. No network, ever."""
from __future__ import annotations

import json


def content_response(text: str, prompt_tokens: int = 50, completion_tokens: int = 20) -> dict:
    return {
        "choices": [
            {"message": {"role": "assistant", "content": text, "tool_calls": None}}
        ],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


def tool_call_response(name: str, args: dict, call_id: str = "call_1") -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": name, "arguments": json.dumps(args)},
                        }
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 10},
    }


class ScriptedTransport:
    """Returns queued responses in order; records every request it received."""

    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.requests: list[dict] = []

    def __call__(self, request: dict) -> dict:
        self.requests.append(request)
        if not self._responses:
            raise AssertionError("ScriptedTransport exhausted — unexpected extra LLM call")
        return self._responses.pop(0)
