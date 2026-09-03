"""
Sovereign AI Workbench — Calculator Tool

Safe mathematical calculations without arbitrary code execution.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

from backend.tools.base import BaseTool, ToolPermission

# Safe operators for expression evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def safe_eval(expression: str) -> float:
    """
    Safely evaluate a mathematical expression.
    Only allows basic arithmetic and math functions.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid expression: {e}")

    return _eval_node(tree.body)


def _eval_node(node: ast.expr) -> float:
    """Recursively evaluate an AST node."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant: {node.value}")

    elif isinstance(node, ast.BinOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return op(left, right)

    elif isinstance(node, ast.UnaryOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op(_eval_node(node.operand))

    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func = SAFE_FUNCTIONS.get(node.func.id)
            if func is None:
                raise ValueError(f"Unsupported function: {node.func.id}")
            args = [_eval_node(arg) for arg in node.args]
            return float(func(*args))

    elif isinstance(node, ast.Name):
        val = SAFE_FUNCTIONS.get(node.id)
        if val is not None and isinstance(val, (int, float)):
            return float(val)
        raise ValueError(f"Unknown variable: {node.id}")

    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


class CalculatorTool(BaseTool):
    """Safe mathematical calculator."""

    def __init__(self):
        super().__init__(
            name="calculate",
            description="Evaluate a mathematical expression safely",
            permission=ToolPermission(
                name="calculate",
                allowed_roles=["admin", "engineering", "finance", "procurement", "hr", "operations"],
            ),
        )

    async def _run(self, expression: str, **kwargs) -> Any:
        result = safe_eval(expression)
        return {"expression": expression, "result": result}
