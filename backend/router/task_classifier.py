"""
Sovereign AI Workbench — Task Classifier

Classifies user input into task types to determine which model to route to.

Phase 6 upgrade: Hybrid classification —
  1. Keyword/heuristic classifier (fast path, <1ms)
  2. LLM classifier (fallback for ambiguous inputs)
  3. Weighted scoring with pattern importance
  4. Full routing decision trace for UI and audit

Architecture:
    User Input
        ↓
    Keyword Classifier → confidence ≥ threshold? → YES → use result
                       → NO → LLM Classifier → merge signals → final
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

from backend.api.schemas import TaskType, ModelName
from backend.router.routing_policy import (
    ClassificationSignal,
    RoutingDecision,
    RoutingPolicy,
    default_policy,
)

logger = logging.getLogger("sovereign.task_classifier")


@dataclass
class ClassificationResult:
    """Result of task classification."""
    task_type: TaskType
    model: ModelName
    confidence: float
    reason: str


# ── Category → Model/TaskType Mapping ─────────────────────────────────────────

CATEGORY_MAP = {
    "coding": (TaskType.CODING, ModelName.QWEN25_CODER_7B, "coding"),
    "vision": (TaskType.VISION, ModelName.QWEN3_VL_8B, "vision"),
    "document": (TaskType.DOCUMENT_REASONING, ModelName.QWEN3_14B, "reasoning"),
    "data": (TaskType.DATA_ANALYSIS, ModelName.QWEN25_CODER_7B, "coding"),
}

TASK_TYPE_TO_MODEL_NAME = {
    "reasoning": ModelName.QWEN3_14B,
    "coding": ModelName.QWEN25_CODER_7B,
    "vision": ModelName.QWEN3_VL_8B,
    "document_reasoning": ModelName.QWEN3_14B,
    "data_analysis": ModelName.QWEN25_CODER_7B,
    "general": ModelName.QWEN3_14B,
}

TASK_TYPE_TO_CATEGORY = {
    "reasoning": "reasoning",
    "coding": "coding",
    "vision": "vision",
    "document_reasoning": "reasoning",
    "data_analysis": "coding",
    "general": "reasoning",
}


# ── Weighted Keyword Patterns ─────────────────────────────────────────────────
#
# Each pattern is (regex, weight).
# Higher weight = stronger signal. Base weight is 1.0.
# Explicit language names get weight 2.0; contextual mentions get 1.0.

CODING_PATTERNS: list[tuple[str, float]] = [
    # Explicit language mentions — strong signal (weight 2.0)
    (r"\b(python|javascript|typescript|java|c\+\+|rust|sql|bash|golang|ruby)\b", 2.0),
    # Explicit code verbs — strong signal
    (r"\b(write|create|generate|build|implement|develop)\b.*\b(code|function|class|script|program|algorithm|api|module)\b", 2.0),
    # Debug/fix code — strong signal
    (r"\b(debug|fix|refactor|optimize)\b.*\b(code|function|bug|error|exception)\b", 2.0),
    # Code artifacts
    (r"\b(csv|json|xml|yaml|dataframe|pandas|numpy|matplotlib)\b", 1.5),
    # Computation
    (r"\b(calculate|compute|formula|equation|algorithm)\b", 1.0),
    # Code syntax in the prompt
    (r"\bdef\b|\bclass\b|\bimport\b|\bfor\b.*\bin\b", 1.5),
    # Programming concepts
    (r"\b(variable|loop|array|list|dictionary|function|method|lambda|recursion)\b", 1.0),
]

VISION_PATTERNS: list[tuple[str, float]] = [
    # Direct image references — strong signal
    (r"\b(image|photo|picture|drawing|diagram|schematic|blueprint)\b", 2.0),
    # Engineering drawings
    (r"\b(p&id|pid|piping|instrumentation)\b", 2.0),
    # Visual analysis verbs
    (r"\b(identify|detect|recognize|find|locate|see|look|inspect)\b.*\b(in this|in the|from the)\b.*\b(image|photo|drawing|diagram|picture)\b", 2.5),
    # Equipment in visual context
    (r"\b(valve|pump|pipe|vessel|tank|motor|sensor|gauge)\b.*\b(diagram|drawing|image)\b", 2.0),
    # OCR/scanning
    (r"\b(ocr|scan|scanned)\b", 1.5),
    # Visualization
    (r"\bvisual(ly|ize|ization)?\b", 1.0),
]

DOCUMENT_REASONING_PATTERNS: list[tuple[str, float]] = [
    # Document types — strong signal
    (r"\b(inspection|report|document|manual|specification|sop|procedure)\b", 1.5),
    # Business documents
    (r"\b(approval|note|memo|letter|certificate|compliance)\b", 1.5),
    # Document analysis verbs
    (r"\b(summarize|analyze|review|assess|evaluate)\b.*\b(report|document|inspection|specification)\b", 2.0),
    # Standards and compliance
    (r"\b(csmop|standard|regulation|compliance|audit)\b", 1.5),
    # Document structure
    (r"\b(page|section|paragraph|table|appendix|chapter)\b", 1.0),
    # File formats (as topics, not code tasks)
    (r"\b(docx|pdf|xlsx|pptx|word|excel|powerpoint)\b", 1.0),
]

DATA_ANALYSIS_PATTERNS: list[tuple[str, float]] = [
    # Data types — strong signal
    (r"\b(data|dataset|telemetry|sensor|measurement|reading)\b", 1.5),
    # Statistical concepts
    (r"\b(anomaly|anomalies|outlier|trend|pattern|correlation)\b", 1.5),
    # Statistics
    (r"\b(average|mean|median|standard deviation|variance|statistics)\b", 1.5),
    # Visualization
    (r"\b(chart|graph|plot|visualization|dashboard)\b", 1.0),
    # Engineering measurements
    (r"\b(temperature|pressure|flow|vibration|rpm|efficiency)\b", 1.0),
    # Data file processing
    (r"\b(xlsx|csv|excel|spreadsheet|table)\b.*\b(analyze|process|read)\b", 2.0),
]


def _weighted_score(text: str, patterns: list[tuple[str, float]]) -> tuple[float, list[str]]:
    """
    Calculate weighted match score for a set of patterns.

    Returns:
        (normalized_score, list_of_matched_pattern_descriptions)
    """
    text_lower = text.lower()
    total_weight = sum(w for _, w in patterns)
    if total_weight == 0:
        return 0.0, []

    matched_weight = 0.0
    matched_patterns: list[str] = []

    for pattern, weight in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matched_weight += weight
            matched_patterns.append(pattern)

    return matched_weight / total_weight, matched_patterns


class TaskClassifier:
    """
    Classifies user requests into task types and selects the appropriate model.

    Phase 6: Supports hybrid classification —
    - Fast keyword path for high-confidence matches
    - LLM fallback for ambiguous inputs (when integrated with ModelRouter)

    Classification flow:
    1. Check for explicit vision indicators (images, diagrams)
    2. Score all categories with weighted patterns
    3. Return result with confidence and matched patterns
    """

    def classify(self, user_input: str, has_image: bool = False) -> ClassificationResult:
        """
        Classify a user request using keyword/heuristic matching.

        Args:
            user_input: The user's text input
            has_image: Whether the request includes an image attachment

        Returns:
            ClassificationResult with task type, model, confidence, and reason
        """
        # If an image is attached, vision takes priority
        if has_image:
            return ClassificationResult(
                task_type=TaskType.VISION,
                model=ModelName.QWEN3_VL_8B,
                confidence=0.95,
                reason="Image attachment detected — routing to vision model",
            )

        # Score each category with weighted patterns
        scores = {
            "coding": _weighted_score(user_input, CODING_PATTERNS),
            "vision": _weighted_score(user_input, VISION_PATTERNS),
            "document": _weighted_score(user_input, DOCUMENT_REASONING_PATTERNS),
            "data": _weighted_score(user_input, DATA_ANALYSIS_PATTERNS),
        }

        # Find the highest scoring category
        best_category = max(scores, key=lambda k: scores[k][0])
        best_score, matched = scores[best_category]

        if best_score < 0.1:
            # No strong signal — default to general reasoning
            return ClassificationResult(
                task_type=TaskType.GENERAL,
                model=ModelName.QWEN3_14B,
                confidence=0.5,
                reason="No strong task-specific signals — using general reasoning",
            )

        # Map to task type and model
        task_type, model, _ = CATEGORY_MAP[best_category]
        reason_map = {
            "coding": "Code-related request detected",
            "vision": "Visual analysis request detected",
            "document": "Document reasoning request detected",
            "data": "Data analysis request — routing to coder model for computation",
        }
        reason = reason_map[best_category]

        # Add matched pattern count to reason
        if matched:
            reason += f" ({len(matched)} pattern{'s' if len(matched) != 1 else ''} matched)"

        return ClassificationResult(
            task_type=task_type,
            model=model,
            confidence=min(best_score * 2.5, 0.99),  # Scale up but cap at 0.99
            reason=reason,
        )

    def classify_with_signal(
        self,
        user_input: str,
        has_image: bool = False,
    ) -> ClassificationSignal:
        """
        Classify and return a ClassificationSignal for the routing decision chain.
        """
        start = time.time()
        result = self.classify(user_input, has_image)
        duration_ms = round((time.time() - start) * 1000, 2)

        return ClassificationSignal(
            source="keyword",
            task_type=result.task_type.value,
            model=result.model.value,
            confidence=result.confidence,
            reason=result.reason,
            duration_ms=duration_ms,
        )

    def explain(self, user_input: str) -> dict:
        """
        Return a detailed breakdown of pattern matching scores per category.
        Useful for debugging classification behavior and UI display.

        Returns:
            Dict with per-category scores, matched patterns, and the final decision.
        """
        scores = {}
        for category, patterns in [
            ("coding", CODING_PATTERNS),
            ("vision", VISION_PATTERNS),
            ("document_reasoning", DOCUMENT_REASONING_PATTERNS),
            ("data_analysis", DATA_ANALYSIS_PATTERNS),
        ]:
            score, matched = _weighted_score(user_input, patterns)
            scores[category] = {
                "score": round(score, 4),
                "matched_count": len(matched),
                "total_patterns": len(patterns),
                "matched_patterns": matched,
            }

        result = self.classify(user_input)
        return {
            "input": user_input,
            "category_scores": scores,
            "final_classification": {
                "task_type": result.task_type.value,
                "model": result.model.value,
                "confidence": result.confidence,
                "reason": result.reason,
            },
        }


# Global instance
task_classifier = TaskClassifier()
