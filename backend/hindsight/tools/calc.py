"""calc tool: safe arithmetic via AST allowlist (no eval of names/calls)."""
from __future__ import annotations

import ast
import json
import operator

from hindsight.tools.registry import ToolSpec

_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    raise ValueError(f"unsupported expression element: {ast.dump(node)[:60]}")


def make_calc_tool() -> ToolSpec:
    def calc(expression: str) -> str:
        try:
            value = _eval(ast.parse(expression, mode="eval"))
            return json.dumps({"value": value})
        except (ValueError, SyntaxError, ZeroDivisionError) as exc:
            return json.dumps({"error": str(exc)})

    return ToolSpec(
        name="calc",
        description="Evaluate a plain arithmetic expression (numbers and + - * / ** % only).",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        fn=calc,
    )
