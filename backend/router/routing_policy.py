"""
Sovereign AI Workbench — Routing Policy

Configurable routing policies and structured routing decisions.
The policy controls when the classifier escalates from keyword matching
to LLM-based classification, default fallback categories, and timing limits.

RoutingDecision captures the full decision chain (keyword result,
LLM result if used, final decision, timing) for UI visibility and audit.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RoutingPolicy:
    """
    Controls how the task router selects a model.

    Attributes:
        llm_threshold: Keyword confidence below this triggers LLM classification.
                       Set to 1.0 to always use LLM; 0.0 to never use LLM.
        default_category: Fallback model category when classification is uncertain.
        max_classification_time_ms: Maximum time for the full classification pipeline.
        prefer_llm: If True, always attempt LLM classification (keyword is just a hint).
        llm_temperature: Temperature for the classification LLM call.
        llm_max_tokens: Max tokens for the classification LLM call.
        llm_timeout_seconds: Timeout for the LLM classification call.
    """
    llm_threshold: float = 0.6
    default_category: str = "reasoning"
    max_classification_time_ms: float = 5000.0
    prefer_llm: bool = False
    llm_temperature: float = 0.1
    llm_max_tokens: int = 256
    llm_timeout_seconds: float = 3.0


@dataclass
class ClassificationSignal:
    """A single classification signal from one source (keyword or LLM)."""
    source: str  # "keyword" or "llm"
    task_type: str
    model: str
    confidence: float
    reason: str
    duration_ms: float = 0.0


@dataclass
class RoutingDecision:
    """
    Full trace of a routing decision for audit and UI display.

    Captures every signal that contributed to the final routing choice,
    plus timing information and the applied policy.
    """
    # Final decision
    task_type: str
    model_category: str
    model_name: str
    confidence: float
    reason: str

    # Signal chain
    keyword_signal: Optional[ClassificationSignal] = None
    llm_signal: Optional[ClassificationSignal] = None
    used_llm: bool = False

    # Timing
    total_classification_ms: float = 0.0

    # Policy applied
    policy_llm_threshold: float = 0.6
    policy_prefer_llm: bool = False

    def to_dict(self) -> dict:
        """Serialize for API response."""
        result = {
            "task_type": self.task_type,
            "model_category": self.model_category,
            "model_name": self.model_name,
            "confidence": self.confidence,
            "reason": self.reason,
            "used_llm": self.used_llm,
            "total_classification_ms": self.total_classification_ms,
            "policy": {
                "llm_threshold": self.policy_llm_threshold,
                "prefer_llm": self.policy_prefer_llm,
            },
        }
        if self.keyword_signal:
            result["keyword_signal"] = {
                "source": self.keyword_signal.source,
                "task_type": self.keyword_signal.task_type,
                "model": self.keyword_signal.model,
                "confidence": self.keyword_signal.confidence,
                "reason": self.keyword_signal.reason,
                "duration_ms": self.keyword_signal.duration_ms,
            }
        if self.llm_signal:
            result["llm_signal"] = {
                "source": self.llm_signal.source,
                "task_type": self.llm_signal.task_type,
                "model": self.llm_signal.model,
                "confidence": self.llm_signal.confidence,
                "reason": self.llm_signal.reason,
                "duration_ms": self.llm_signal.duration_ms,
            }
        return result


# Default global policy
default_policy = RoutingPolicy()
