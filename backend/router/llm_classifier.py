"""
Sovereign AI Workbench — LLM-Based Task Classifier

Uses the active reasoning model to classify ambiguous user inputs
that the keyword classifier can't handle with sufficient confidence.

The LLM receives a structured few-shot prompt and returns a JSON
classification. Falls back to the keyword signal on failure.

Usage:
    from backend.router.llm_classifier import LLMClassifier

    llm_clf = LLMClassifier()
    result = await llm_clf.classify("Analyze the pressure readings and plot a trend")
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from backend.router.routing_policy import ClassificationSignal

logger = logging.getLogger("sovereign.llm_classifier")


# ── Classification Prompt ─────────────────────────────────────────────────────

CLASSIFICATION_SYSTEM_PROMPT = """\
You are a task classification engine for a Sovereign AI system.
You must classify user requests into exactly one task type and select the best model.

Available task types:
- "reasoning": General analysis, summarization, Q&A, document interpretation
- "coding": Writing, debugging, or analyzing code; data processing scripts
- "vision": Image analysis, diagram interpretation, P&ID reading, visual inspection
- "document_reasoning": Analyzing reports, SOPs, manuals, specifications, compliance docs
- "data_analysis": Processing telemetry, sensor data, spreadsheets, statistical analysis

Available models:
- "qwen3-14b": Best for reasoning, summarization, document analysis, general Q&A
- "qwen2.5-coder-7b": Best for code generation, debugging, data scripts, calculations
- "qwen3-vl-8b": Best for image understanding, diagrams, visual inspection

Rules:
1. If the task involves writing, debugging, or running code → coding + qwen2.5-coder-7b
2. If the task involves images, diagrams, photos, drawings → vision + qwen3-vl-8b
3. If the task involves analyzing documents, reports, SOPs → document_reasoning + qwen3-14b
4. If the task involves data/telemetry processing (even if code is needed) → data_analysis + qwen2.5-coder-7b
5. Default to reasoning + qwen3-14b for general questions

Respond ONLY with a JSON object, no other text:
{"task_type": "...", "model": "...", "confidence": 0.XX, "reason": "brief explanation"}"""


CLASSIFICATION_FEW_SHOT = [
    {
        "role": "user",
        "content": 'Classify: "Write Python code to calculate pump efficiency from flow rate and power consumption"',
    },
    {
        "role": "assistant",
        "content": '{"task_type": "coding", "model": "qwen2.5-coder-7b", "confidence": 0.95, "reason": "Explicit request to write Python code for engineering calculation"}',
    },
    {
        "role": "user",
        "content": 'Classify: "Summarize the key findings from inspection report INS-2026-001"',
    },
    {
        "role": "assistant",
        "content": '{"task_type": "document_reasoning", "model": "qwen3-14b", "confidence": 0.92, "reason": "Document summarization task requiring analytical reasoning over an inspection report"}',
    },
    {
        "role": "user",
        "content": 'Classify: "Identify valve V-204 in this P&ID drawing and find its specification"',
    },
    {
        "role": "assistant",
        "content": '{"task_type": "vision", "model": "qwen3-vl-8b", "confidence": 0.93, "reason": "Visual identification task on a P&ID diagram requiring image understanding"}',
    },
    {
        "role": "user",
        "content": 'Classify: "Analyze the temperature sensor data from last month and find anomalies"',
    },
    {
        "role": "assistant",
        "content": '{"task_type": "data_analysis", "model": "qwen2.5-coder-7b", "confidence": 0.90, "reason": "Sensor data analysis requiring statistical processing and likely code generation"}',
    },
]


# ── Valid values ──────────────────────────────────────────────────────────────

VALID_TASK_TYPES = {"reasoning", "coding", "vision", "document_reasoning", "data_analysis", "general"}
VALID_MODELS = {"qwen3-14b", "qwen2.5-coder-7b", "qwen3-vl-8b"}


class LLMClassifier:
    """
    Uses an LLM to classify user requests when keyword matching is ambiguous.

    The classifier:
    1. Builds a few-shot classification prompt
    2. Sends it to the active reasoning model via provider
    3. Parses the JSON response
    4. Validates the output against known task types and models
    5. Returns a ClassificationSignal

    Falls back gracefully on:
    - Provider connection failure
    - Timeout
    - Malformed JSON response
    - Invalid task type or model in response
    """

    async def classify(
        self,
        user_input: str,
        provider: object,
        model_id: str,
        temperature: float = 0.1,
        max_tokens: int = 256,
        timeout_seconds: float = 3.0,
    ) -> Optional[ClassificationSignal]:
        """
        Classify user input using the LLM.

        Args:
            user_input: The user's message to classify
            provider: A BaseProvider instance (active reasoning model's provider)
            model_id: The model ID to use for classification (e.g. "qwen3:14b")
            temperature: Low temperature for deterministic classification
            max_tokens: Short output — just a JSON object
            timeout_seconds: Max time for the LLM call

        Returns:
            ClassificationSignal if successful, None if classification failed
        """
        start = time.time()

        messages = self._build_messages(user_input)

        try:
            # Use the provider's chat method directly
            response = await provider.chat(
                model_id=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                keep_alive="10m",
            )

            duration_ms = round((time.time() - start) * 1000, 2)

            # Parse the JSON response
            signal = self._parse_response(response.content, duration_ms)

            if signal:
                logger.info(
                    "LLM classified '%s...' as %s → %s (%.2f) in %.1fms",
                    user_input[:50],
                    signal.task_type,
                    signal.model,
                    signal.confidence,
                    duration_ms,
                )
            else:
                logger.warning(
                    "LLM classification failed to parse for: '%s...'",
                    user_input[:50],
                )

            return signal

        except Exception as e:
            duration_ms = round((time.time() - start) * 1000, 2)
            logger.warning(
                "LLM classification failed (%.1fms): %s",
                duration_ms,
                e,
            )
            return None

    def _build_messages(self, user_input: str) -> list[dict[str, str]]:
        """Build the few-shot classification prompt."""
        messages = [
            {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
        ]
        messages.extend(CLASSIFICATION_FEW_SHOT)
        messages.append({
            "role": "user",
            "content": f'Classify: "{user_input}"',
        })
        return messages

    def _parse_response(
        self,
        raw_response: str,
        duration_ms: float,
    ) -> Optional[ClassificationSignal]:
        """
        Parse the LLM's JSON response into a ClassificationSignal.

        Handles:
        - Clean JSON
        - JSON wrapped in markdown code blocks
        - JSON with leading/trailing text
        """
        text = raw_response.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        # Try to find JSON object in the text
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            return None

        try:
            data = json.loads(text[json_start:json_end])
        except json.JSONDecodeError:
            return None

        task_type = data.get("task_type", "")
        model = data.get("model", "")
        confidence = data.get("confidence", 0.5)
        reason = data.get("reason", "LLM classification")

        # Validate
        if task_type not in VALID_TASK_TYPES:
            logger.warning("LLM returned invalid task_type: %s", task_type)
            return None

        if model not in VALID_MODELS:
            logger.warning("LLM returned invalid model: %s", model)
            return None

        if not isinstance(confidence, (int, float)):
            confidence = 0.5

        confidence = max(0.0, min(1.0, float(confidence)))

        return ClassificationSignal(
            source="llm",
            task_type=task_type,
            model=model,
            confidence=confidence,
            reason=reason,
            duration_ms=duration_ms,
        )


# Global instance
llm_classifier = LLMClassifier()
