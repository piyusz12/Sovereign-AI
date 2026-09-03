"""
Sovereign AI Workbench — Task Classifier

Classifies user input into task types to determine which model to route to.
Initially uses keyword/heuristic classification; upgradeable to LLM-based
classification once a model is available.

This is where the project becomes more than a chatbot — the Dynamic Expertise
Broker concept from the architecture.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from backend.api.schemas import TaskType, ModelName

logger = logging.getLogger("sovereign.task_classifier")


@dataclass
class ClassificationResult:
    """Result of task classification."""
    task_type: TaskType
    model: ModelName
    confidence: float
    reason: str


# ── Keyword Patterns ──────────────────────────────────────────────────────────

CODING_PATTERNS = [
    r"\b(write|create|generate|build|implement|develop|code|program|script)\b.*\b(python|code|function|class|script|program|algorithm|api)\b",
    r"\b(python|javascript|typescript|java|c\+\+|rust|sql|bash)\b",
    r"\b(debug|fix|refactor|optimize)\b.*\b(code|function|bug|error)\b",
    r"\b(csv|json|xml|yaml|dataframe|pandas|numpy|matplotlib)\b",
    r"\b(calculate|compute|formula|equation|algorithm)\b",
    r"\bdef\b|\bclass\b|\bimport\b|\bfor\b.*\bin\b",
]

VISION_PATTERNS = [
    r"\b(image|photo|picture|drawing|diagram|schematic|blueprint)\b",
    r"\b(p&id|pid|piping|instrumentation)\b",
    r"\b(identify|detect|recognize|find|locate|see|look|inspect)\b.*\b(in this|in the|from the)\b.*\b(image|photo|drawing|diagram|picture)\b",
    r"\b(valve|pump|pipe|vessel|tank|motor|sensor|gauge)\b.*\b(diagram|drawing|image)\b",
    r"\b(ocr|scan|scanned)\b",
    r"\bvisual(ly|ize|ization)?\b",
]

DOCUMENT_REASONING_PATTERNS = [
    r"\b(inspection|report|document|manual|specification|sop|procedure)\b",
    r"\b(approval|note|memo|letter|certificate|compliance)\b",
    r"\b(summarize|analyze|review|assess|evaluate)\b.*\b(report|document|inspection|specification)\b",
    r"\b(csmop|standard|regulation|compliance|audit)\b",
    r"\b(page|section|paragraph|table|appendix|chapter)\b",
    r"\b(docx|pdf|xlsx|pptx|word|excel|powerpoint)\b",
]

DATA_ANALYSIS_PATTERNS = [
    r"\b(data|dataset|telemetry|sensor|measurement|reading)\b",
    r"\b(anomaly|anomalies|outlier|trend|pattern|correlation)\b",
    r"\b(average|mean|median|standard deviation|variance|statistics)\b",
    r"\b(chart|graph|plot|visualization|dashboard)\b",
    r"\b(temperature|pressure|flow|vibration|rpm|efficiency)\b",
    r"\b(xlsx|csv|excel|spreadsheet|table)\b.*\b(analyze|process|read)\b",
]


def _match_score(text: str, patterns: list[str]) -> float:
    """Calculate match score for a set of patterns."""
    text_lower = text.lower()
    matches = sum(1 for p in patterns if re.search(p, text_lower, re.IGNORECASE))
    return matches / len(patterns) if patterns else 0.0


class TaskClassifier:
    """
    Classifies user requests into task types and selects the appropriate model.

    Classification flow:
    1. Check for explicit vision indicators (images, diagrams)
    2. Check for coding patterns
    3. Check for document reasoning patterns
    4. Check for data analysis patterns
    5. Default to general reasoning
    """

    def classify(self, user_input: str, has_image: bool = False) -> ClassificationResult:
        """
        Classify a user request.

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

        # Score each category
        scores = {
            "coding": _match_score(user_input, CODING_PATTERNS),
            "vision": _match_score(user_input, VISION_PATTERNS),
            "document": _match_score(user_input, DOCUMENT_REASONING_PATTERNS),
            "data": _match_score(user_input, DATA_ANALYSIS_PATTERNS),
        }

        # Find the highest scoring category
        best_category = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best_category]

        if best_score < 0.1:
            # No strong signal — default to general reasoning
            return ClassificationResult(
                task_type=TaskType.GENERAL,
                model=ModelName.QWEN3_14B,
                confidence=0.5,
                reason="No strong task-specific signals — using general reasoning",
            )

        # Map to task type and model
        classification_map = {
            "coding": (TaskType.CODING, ModelName.QWEN25_CODER_7B, "Code-related request detected"),
            "vision": (TaskType.VISION, ModelName.QWEN3_VL_8B, "Visual analysis request detected"),
            "document": (
                TaskType.DOCUMENT_REASONING,
                ModelName.QWEN3_14B,
                "Document reasoning request detected",
            ),
            "data": (
                TaskType.DATA_ANALYSIS,
                ModelName.QWEN25_CODER_7B,
                "Data analysis request — routing to coder model for computation",
            ),
        }

        task_type, model, reason = classification_map[best_category]

        return ClassificationResult(
            task_type=task_type,
            model=model,
            confidence=min(best_score * 3, 0.99),  # Scale up but cap at 0.99
            reason=reason,
        )


# Global instance
task_classifier = TaskClassifier()
