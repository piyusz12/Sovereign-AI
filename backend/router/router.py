"""
Sovereign AI Workbench — Model Router

Routes classified tasks to the appropriate model, handling model loading/unloading
to respect single-GPU discipline on the RTX 4060 8GB.

Architecture:
    User Request → Task Classifier → Model Router → Provider → Response

Phase 5: Uses provider abstraction — router never imports a specific backend.
Phase 6: Hybrid classification (keyword + LLM), routing decisions with full trace.
Phase 7: Coding-specific system prompts and code generation support.
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator, Optional

from backend.router.model_registry import ModelRegistry, ModelConfig, model_registry
from backend.router.task_classifier import (
    TaskClassifier,
    ClassificationResult,
    task_classifier,
    TASK_TYPE_TO_CATEGORY,
    TASK_TYPE_TO_MODEL_NAME,
)
from backend.router.routing_policy import (
    ClassificationSignal,
    RoutingDecision,
    RoutingPolicy,
    default_policy,
)
from backend.router.llm_classifier import LLMClassifier, llm_classifier
from backend.router.coding import (
    extract_code_blocks,
    get_system_prompt as get_coding_system_prompt,
    CodeGenerationResult,
)
from backend.router.vision import (
    VisionResult,
    get_system_prompt as get_vision_system_prompt,
)
from backend.router.providers.base import BaseProvider, ProviderChatResponse, ProviderStreamChunk
from backend.router.providers.factory import get_provider
from backend.router.session_manager import session_manager, SessionManager
from backend.optimization.context import ContextBudgeter, PromptBuild
from backend.optimization.scheduler import gpu_scheduler
from backend.optimization.telemetry import inference_telemetry, new_metric
from backend.settings import settings

logger = logging.getLogger("sovereign.router")


# ── Category mapping ──────────────────────────────────────────────────────────

TASK_TO_CATEGORY: dict[str, str] = {
    "reasoning": "reasoning",
    "coding": "coding",
    "vision": "vision",
    "document_reasoning": "reasoning",
    "data_analysis": "coding",
    "general": "reasoning",
}


class ModelRouter:
    """
    Routes requests to the appropriate local model.

    The router:
    1. Classifies the task type (keyword-first, LLM fallback)
    2. Selects the model from the registry
    3. Ensures the model is loaded (unloading others if needed)
    4. Gets the correct provider via the factory
    5. Returns the response with full routing decision trace

    All communication is local (localhost only).
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        classifier: Optional[TaskClassifier] = None,
        llm_clf: Optional[LLMClassifier] = None,
        sessions: Optional[SessionManager] = None,
        policy: Optional[RoutingPolicy] = None,
    ):
        self.registry = registry or model_registry
        self.classifier = classifier or task_classifier
        self.llm_clf = llm_clf or llm_classifier
        self.sessions = sessions or session_manager
        self.policy = policy or default_policy
        self.context_budgeter = ContextBudgeter(
            max_total_tokens=settings.inference_context_tokens,
            output_reserve_tokens=settings.inference_output_reserve_tokens,
        )

    def _get_provider(self, model: ModelConfig) -> BaseProvider:
        """Get the appropriate provider for a model."""
        return get_provider(model.provider.value, model.base_url)

    def _category_for_model(self, model_id: Optional[str]) -> Optional[str]:
        """
        Resolve a public model ID, provider tag, or category alias to its registry category.
        Never raises ValueError — falls back gracefully to default category or None for dynamic routing.

        Supports:
        - Auto/dynamic keywords: None, "", "auto", "default", "undefined", "dynamic" -> returns None (triggers classification)
        - Direct category names: "reasoning", "coding", "vision"
        - Full model IDs: "qwen2.5-coder:7b", "qwen3-vl:8b", "qwen3:14b"
        - Base model prefixes: "qwen2.5-coder", "qwen3-vl", "qwen3"
        - Common aliases: "coder", "vl", "code", "chat", "deepseek"
        - Unrecognized names: falls back to default reasoning category with a warning
        """
        if not model_id:
            return None

        raw = model_id.value if hasattr(model_id, "value") else str(model_id)
        normalized = raw.strip().lower()

        # Dynamic / auto keywords imply no forced category (let classifier decide)
        if normalized in ("", "none", "null", "auto", "default", "undefined", "dynamic", "any"):
            return None

        # 1. Exact match against category key
        if normalized in self.registry.models:
            return normalized

        # 2. Exact match against model_id, name, or cleaned name
        for category, model in self.registry.models.items():
            if normalized in {
                model.model_id.lower(),
                model.name.lower(),
                model.name.lower().replace(" (ollama)", ""),
                category.lower(),
            }:
                return category

        # 3. Base model tag match (e.g., 'qwen2.5-coder' matching 'qwen2.5-coder:7b')
        base_normalized = normalized.split(":")[0].replace("-", "").replace(".", "")
        for category, model in self.registry.models.items():
            model_base = model.model_id.lower().split(":")[0].replace("-", "").replace(".", "")
            if base_normalized == model_base:
                return category

        # 4. Keyword heuristic fallback
        if any(kw in normalized for kw in ("coder", "code", "coding", "python", "script", "deepseek")):
            if "coding" in self.registry.models:
                return "coding"
        if any(kw in normalized for kw in ("vision", "vl", "visual", "image", "ocr", "p&id", "llava")):
            if "vision" in self.registry.models:
                return "vision"
        if any(kw in normalized for kw in ("reason", "chat", "general", "qwen", "llama", "deep", "instruct")):
            if "reasoning" in self.registry.models:
                return "reasoning"

        # 5. Safe graceful fallback without raising ValueError
        default_cat = getattr(self.policy, "default_category", "reasoning") or "reasoning"
        logger.warning(
            "Unrecognized model or category '%s'. Gracefully falling back to default '%s'.",
            model_id,
            default_cat,
        )
        return default_cat if default_cat in self.registry.models else "reasoning"

    # ── Classify Only (Phase 6) ───────────────────────────────────────────

    async def classify_only(
        self,
        user_input: str,
        has_image: bool = False,
        use_llm: bool = False,
    ) -> RoutingDecision:
        """
        Classify a user input and return the routing decision WITHOUT running
        inference. Useful for the frontend to preview routing before committing.

        Args:
            user_input: The user's message
            has_image: Whether the request includes an image
            use_llm: Force LLM classification even for high-confidence keyword matches

        Returns:
            RoutingDecision with full classification trace
        """
        start = time.time()

        # Step 1: Keyword classification
        keyword_signal = self.classifier.classify_with_signal(user_input, has_image)

        # Step 2: Decide if LLM classification is needed
        llm_signal = None
        should_use_llm = (
            use_llm
            or self.policy.prefer_llm
            or keyword_signal.confidence < self.policy.llm_threshold
        )

        if should_use_llm:
            llm_signal = await self._try_llm_classify(user_input)

        # Step 3: Merge signals into final decision
        decision = self._merge_signals(keyword_signal, llm_signal, start)
        return decision

    # ── Route (Phase 5 + 6 upgrade) ───────────────────────────────────────

    # ── Route (Phase 5 + 6 upgrade) ───────────────────────────────────────

    async def route(
        self,
        user_input: str,
        has_image: bool = False,
        images: Optional[list[str]] = None,
        force_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Route a user request to the appropriate model with crash-proof auto-failover (non-streaming).

        Args:
            user_input: The user's message
            has_image: Whether the request includes an image (deprecated, use images)
            images: List of base64 encoded images
            force_model: Force a specific model category (or None/auto for dynamic routing)
            system_prompt: Optional system prompt override
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            session_id: Optional session ID for conversational memory

        Returns:
            Dict with response text, classification info, model metadata, and metrics
        """
        start = time.time()
        if images:
            has_image = True

        # Step 1: Classify (or force if an explicit category was requested)
        forced_category = self._category_for_model(force_model) if force_model else None
        if forced_category:
            classification = self.classifier.classify(user_input, has_image)
            category = forced_category
            routing_decision = RoutingDecision(
                task_type=classification.task_type.value,
                model_category=category,
                model_name=classification.model.value,
                confidence=1.0,
                reason=f"Model forced to category '{category}' (input: '{force_model}')",
            )
        else:
            routing_decision = await self.classify_only(user_input, has_image)
            category = routing_decision.model_category

        logger.info(
            "Task classified as '%s' → model category '%s' (confidence: %.2f)",
            routing_decision.task_type,
            category,
            routing_decision.confidence,
        )

        # Dynamic fallback topology: pairs each category with a resilient local backup
        fallback_map = {
            "coding": "reasoning",
            "vision": "reasoning",
            "reasoning": "coding",
        }
        secondary_category = fallback_map.get(
            category, "reasoning" if category != "reasoning" else "coding"
        )

        # Step 2: Load model with dynamic failover
        model = None
        load_error = None
        try:
            model = await self.registry.load_model(category)
        except Exception as e:
            load_error = e
            logger.warning(
                "Primary category '%s' failed to load: %s. Initiating dynamic failover to '%s'...",
                category,
                e,
                secondary_category,
            )
            try:
                model = await self.registry.load_model(secondary_category)
                category = secondary_category
                routing_decision.fallback_occurred = True
                routing_decision.fallback_reason = f"Primary category load failed ({load_error}). Switched to {category}."
                routing_decision.model_category = category
                routing_decision.model_name = model.model_id
            except Exception as e2:
                logger.error("Secondary category '%s' also failed to load: %s", secondary_category, e2)
                load_error = f"{load_error} | Failover load failed: {e2}"

        # Step 3 & 4: Resolve prompt and send to model with dynamic inference failover
        chat_response = None
        inference_error = None
        prompt_build = None
        submitted_at = time.perf_counter()
        execution_started_at = submitted_at

        if model:
            effective_prompt = self._resolve_system_prompt(
                system_prompt, category, model, routing_decision.task_type
            )
            prompt_build = self._build_prompt(user_input, effective_prompt, session_id, images=images)
            provider = self._get_provider(model)

            try:
                submitted_at = time.perf_counter()
                execution_started_at = submitted_at

                async def run_inference():
                    nonlocal execution_started_at
                    execution_started_at = time.perf_counter()
                    return await provider.chat(
                        model_id=model.model_id,
                        messages=prompt_build.messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        keep_alive=model.keep_alive,
                    )

                chat_response = await gpu_scheduler.schedule(
                    task_type=f"inference-{category}", priority=1, coro=run_inference()
                )
            except Exception as err:
                inference_error = err
                logger.warning(
                    "Primary inference with category '%s' (%s) failed: %s. Initiating crash-proof failover to '%s'...",
                    category,
                    model.model_id,
                    err,
                    secondary_category,
                )

                # Dynamic failover to secondary model if primary model failed during inference
                if secondary_category != category:
                    try:
                        backup_model = await self.registry.load_model(secondary_category)
                        backup_prompt = self._resolve_system_prompt(
                            system_prompt, secondary_category, backup_model, routing_decision.task_type
                        )
                        backup_images = images if secondary_category == "vision" else None
                        backup_build = self._build_prompt(
                            user_input, backup_prompt, session_id, images=backup_images
                        )
                        backup_provider = self._get_provider(backup_model)

                        async def run_backup_inference():
                            nonlocal execution_started_at
                            execution_started_at = time.perf_counter()
                            return await backup_provider.chat(
                                model_id=backup_model.model_id,
                                messages=backup_build.messages,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                keep_alive=backup_model.keep_alive,
                            )

                        chat_response = await gpu_scheduler.schedule(
                            task_type=f"inference-{secondary_category}", priority=2, coro=run_backup_inference()
                        )
                        model = backup_model
                        category = secondary_category
                        prompt_build = backup_build
                        routing_decision.fallback_occurred = True
                        routing_decision.fallback_reason = (
                            f"Primary model error ({inference_error}). "
                            f"Crash-proof dynamic router auto-recovered using {backup_model.model_id}."
                        )
                        routing_decision.model_category = category
                        routing_decision.model_name = backup_model.model_id
                        logger.info("Crash-proof dynamic failover succeeded with %s", backup_model.model_id)
                        inference_error = None
                    except Exception as backup_err:
                        logger.error("Secondary failover also failed: %s", backup_err)
                        inference_error = f"{inference_error} | Failover inference failed: {backup_err}"

        duration_ms = round((time.time() - start) * 1000, 2)

        if chat_response:
            response_text = chat_response.content
            m = chat_response.metrics
            queue_wait_ms = round((execution_started_at - submitted_at) * 1000, 2)
            prompt_tokens = m.prompt_eval_count or (prompt_build.budget.used_tokens if prompt_build else 0)
            itl_ms = round(1000 / m.tokens_per_sec, 2) if m.tokens_per_sec else 0.0
            metrics = {
                "tokens_per_sec": m.tokens_per_sec,
                "ttft_ms": m.first_token_ms,
                "itl_ms": itl_ms,
                "total_duration_ms": m.total_duration_ms,
                "eval_count": m.eval_count,
                "prompt_eval_count": prompt_tokens,
                "queue_wait_ms": queue_wait_ms,
                "prefix_key": prompt_build.prefix_key if prompt_build else "",
                "context_budget": prompt_build.budget.__dict__ if prompt_build else {},
                "fallback_occurred": routing_decision.fallback_occurred,
                "fallback_reason": routing_decision.fallback_reason,
            }
            inference_telemetry.record(
                new_metric(
                    model=model.model_id if model else "unknown",
                    task_type=routing_decision.task_type,
                    ttft_ms=m.first_token_ms,
                    itl_ms=itl_ms,
                    tokens_per_second=m.tokens_per_sec,
                    prompt_tokens=prompt_tokens,
                    output_tokens=m.eval_count,
                    queue_wait_ms=queue_wait_ms,
                    total_duration_ms=m.total_duration_ms,
                    prefix_key=prompt_build.prefix_key if prompt_build else "",
                )
            )
        else:
            err_msg = str(inference_error or load_error or "Inference backend unavailable")
            logger.warning("Local inference failed across all available local models: %s", err_msg)
            response_text = (
                f"[Sovereign AI] Local model inference could not be completed ({err_msg}). "
                f"Air-gapped security boundary maintained (zero external egress)."
            )
            metrics = {
                "error": err_msg,
                "fallback_occurred": True,
                "fallback_reason": err_msg,
            }

        # Save to session history if applicable and successful
        if session_id and response_text and not response_text.startswith("[Sovereign AI] Local model inference could not be completed"):
            self.sessions.add_message(session_id, "user", user_input)
            self.sessions.add_message(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "classification": {
                "task_type": routing_decision.task_type,
                "model": routing_decision.model_name,
                "confidence": routing_decision.confidence,
                "reason": routing_decision.reason,
            },
            "routing_decision": routing_decision.to_dict(),
            "model_used": {
                "name": model.name if model else "Sovereign Local Engine",
                "provider": model.provider.value if model else "local",
                "model_id": model.model_id if model else "offline",
                "category": category,
            },
            "metrics": metrics,
            "duration_ms": duration_ms,
        }

    # ── Route Streaming ───────────────────────────────────────────────────

    async def route_stream(
        self,
        user_input: str,
        has_image: bool = False,
        images: Optional[list[str]] = None,
        force_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Route a user request with crash-proof streaming response.

        Yields dicts suitable for SSE:
            {"chunk": "token text", "done": false}
            ...
            {"chunk": "", "done": true, "classification": {...}, "model_used": {...}, "metrics": {...}}
        """
        start = time.time()
        if images:
            has_image = True

        # Step 1: Classify (or force if explicit)
        forced_category = self._category_for_model(force_model) if force_model else None
        if forced_category:
            classification = self.classifier.classify(user_input, has_image)
            category = forced_category
            routing_decision = RoutingDecision(
                task_type=classification.task_type.value,
                model_category=category,
                model_name=classification.model.value,
                confidence=1.0,
                reason=f"Model forced to category '{category}' (input: '{force_model}')",
            )
        else:
            routing_decision = await self.classify_only(user_input, has_image)
            category = routing_decision.model_category

        logger.info(
            "Streaming: task '%s' → model '%s'",
            routing_decision.task_type,
            category,
        )

        fallback_map = {
            "coding": "reasoning",
            "vision": "reasoning",
            "reasoning": "coding",
        }
        secondary_category = fallback_map.get(
            category, "reasoning" if category != "reasoning" else "coding"
        )

        # Step 2: Load model with dynamic failover
        model = None
        try:
            model = await self.registry.load_model(category)
        except Exception as load_err:
            logger.warning("Streaming primary category '%s' load failed: %s. Attempting failover...", category, load_err)
            try:
                model = await self.registry.load_model(secondary_category)
                category = secondary_category
                routing_decision.fallback_occurred = True
                routing_decision.fallback_reason = f"Primary category load failed ({load_err}). Switched to {category}."
            except Exception as backup_load_err:
                logger.error("Streaming backup model load failed: %s", backup_load_err)
                yield {
                    "chunk": f"[Sovereign AI] Local model offline: {backup_load_err}",
                    "done": True,
                    "error": str(backup_load_err),
                }
                return

        # Step 3: Resolve system prompt
        effective_prompt = self._resolve_system_prompt(
            system_prompt, category, model, routing_decision.task_type
        )

        # Step 4: Stream from provider with fail-safe error handling
        prompt_build = self._build_prompt(user_input, effective_prompt, session_id, images=images)
        messages = prompt_build.messages
        provider = self._get_provider(model)
        full_response = []
        queued_at = time.perf_counter()

        try:
            async with gpu_scheduler.exclusive():
                queue_wait_ms = round((time.perf_counter() - queued_at) * 1000, 2)
                async for chunk in provider.chat_stream(
                    model_id=model.model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    keep_alive=model.keep_alive,
                ):
                    if chunk.done:
                        # Final chunk with metrics
                        duration_ms = round((time.time() - start) * 1000, 2)
                        m = chunk.metrics or ProviderStreamChunk().metrics
                        tps = m.tokens_per_sec if m else 0.0
                        eval_count = m.eval_count if m else 0

                        prompt_tokens = m.prompt_eval_count if m else 0
                        prompt_tokens = prompt_tokens or prompt_build.budget.used_tokens
                        itl_ms = round(1000 / tps, 2) if tps else 0.0
                        inference_telemetry.record(
                            new_metric(
                                model=model.model_id,
                                task_type=routing_decision.task_type,
                                ttft_ms=m.first_token_ms if m else 0.0,
                                itl_ms=itl_ms,
                                tokens_per_second=tps,
                                prompt_tokens=prompt_tokens,
                                output_tokens=eval_count,
                                queue_wait_ms=queue_wait_ms,
                                total_duration_ms=m.total_duration_ms if m else duration_ms,
                                prefix_key=prompt_build.prefix_key,
                            )
                        )
                        yield {
                            "chunk": chunk.content,
                            "done": True,
                            "classification": {
                                "task_type": routing_decision.task_type,
                                "model": routing_decision.model_name,
                                "confidence": routing_decision.confidence,
                                "reason": routing_decision.reason,
                            },
                            "routing_decision": routing_decision.to_dict(),
                            "model_used": {
                                "name": model.name,
                                "provider": model.provider.value,
                                "model_id": model.model_id,
                                "category": category,
                            },
                            "metrics": {
                                "tokens_per_sec": tps,
                                "ttft_ms": m.first_token_ms if m else 0.0,
                                "itl_ms": itl_ms,
                                "eval_count": eval_count,
                                "prompt_eval_count": prompt_tokens,
                                "queue_wait_ms": queue_wait_ms,
                                "prefix_key": prompt_build.prefix_key,
                                "context_budget": prompt_build.budget.__dict__,
                                "duration_ms": duration_ms,
                                "fallback_occurred": routing_decision.fallback_occurred,
                            },
                        }

                        if session_id and full_response:
                            self.sessions.add_message(session_id, "user", user_input)
                            self.sessions.add_message(session_id, "assistant", "".join(full_response))

                    else:
                        full_response.append(chunk.content)
                        yield {
                            "chunk": chunk.content,
                            "done": False,
                        }

        except ConnectionError as e:
            logger.error("Streaming connection error: %s", e)
            yield {
                "chunk": f"[Sovereign AI] Local model connection failed: {e}",
                "done": True,
                "error": str(e),
            }
        except Exception as e:
            logger.error("Streaming inference failed: %s", e)
            yield {
                "chunk": f"[Sovereign AI] Streaming inference interrupted: {e}",
                "done": True,
                "error": str(e),
            }

    # ── Code Generation (Phase 7) ─────────────────────────────────────────

    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> CodeGenerationResult:
        """
        Generate code using the coder model (with crash-proof failover to reasoning).

        Forces the coder model regardless of classification, uses the coding
        system prompt, and extracts structured code blocks from the response.

        Args:
            prompt: Description of the code to generate
            language: Target language (default: "python")
            context: Additional context (file contents, requirements, etc.)
            temperature: Lower temperature for more deterministic code
            max_tokens: Maximum tokens to generate

        Returns:
            CodeGenerationResult with extracted code blocks and metadata
        """
        start = time.time()

        # Build the full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nTask:\n{prompt}"

        if language != "python":
            full_prompt += f"\n\nGenerate code in {language}."

        try:
            result = await self.route(
                user_input=full_prompt,
                force_model="coding",
                system_prompt=get_coding_system_prompt(
                    # Use data_analysis prompt if the prompt looks data-heavy
                    "data_analysis" if any(
                        kw in prompt.lower()
                        for kw in ["data", "csv", "xlsx", "telemetry", "sensor", "analyze"]
                    ) else "coding"
                ),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = result.get("response", "")
            model_used = result.get("model_used", {}).get("model_id", "")
            duration_ms = round((time.time() - start) * 1000, 2)

            # Extract code blocks
            blocks = extract_code_blocks(response_text)
            has_valid_blocks = len(blocks) > 0
            is_offline_msg = response_text.startswith("[Sovereign AI] Local model inference could not be completed")

            is_success = has_valid_blocks and not is_offline_msg
            return CodeGenerationResult(
                code_blocks=blocks if has_valid_blocks else [f"# Task: {prompt}\n# Note: Model generation yielded no code block"],
                raw_response=response_text,
                model_used=model_used,
                language=language,
                duration_ms=duration_ms,
                success=is_success,
                error=None if is_success else (result.get("metrics", {}).get("error") or "No executable code block found in response"),
            )

        except Exception as e:
            duration_ms = round((time.time() - start) * 1000, 2)
            logger.error("Code generation failed: %s", e)
            return CodeGenerationResult(
                code_blocks=[f"# Task: {prompt}\n# Execution failed: {e}"],
                raw_response=f"[Error: {e}]",
                model_used="",
                language=language,
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

    # ── Vision Analysis (Phase 8) ─────────────────────────────────────────

    async def analyze_vision(
        self,
        prompt: str,
        images: list[str],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> VisionResult:
        """
        Analyze an image using the vision model.
        Forces the vision category and uses the specialized vision prompt.

        Args:
            prompt: Question or analysis request
            images: List of base64 encoded images
            temperature: Low temperature for factual observation
            max_tokens: Maximum tokens

        Returns:
            VisionResult with analysis text and metadata
        """
        start = time.time()

        # Validate and sanitize images input
        if not images or all(not img.strip() for img in images):
            return VisionResult(
                content="",
                model_used="",
                duration_ms=0.0,
                success=False,
                error="No valid images provided for vision analysis.",
            )

        from backend.router.vision import clean_base64_image, _compress_image

        sanitized_images: list[str] = []
        for raw_img in images:
            if not raw_img or not raw_img.strip():
                continue
            cleaned = clean_base64_image(raw_img)
            try:
                compressed = _compress_image(cleaned)
                sanitized_images.append(compressed)
            except Exception:
                sanitized_images.append(cleaned)

        if not sanitized_images:
            return VisionResult(
                content="",
                model_used="",
                duration_ms=0.0,
                success=False,
                error="No valid images provided for vision analysis.",
            )

        try:
            result = await self.route(
                user_input=prompt,
                images=sanitized_images,
                force_model="vision",
                system_prompt=get_vision_system_prompt(),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = result.get("response", "")
            model_used = result.get("model_used", {}).get("model_id", "")
            duration_ms = round((time.time() - start) * 1000, 2)

            # Detect error responses from the model
            if response_text.startswith("[Error"):
                return VisionResult(
                    content="",
                    model_used=model_used,
                    duration_ms=duration_ms,
                    success=False,
                    error=response_text,
                )

            # Detect empty responses
            if not response_text or not response_text.strip():
                return VisionResult(
                    content="",
                    model_used=model_used,
                    duration_ms=duration_ms,
                    success=False,
                    error="Vision model returned an empty response.",
                )

            return VisionResult(
                content=response_text,
                model_used=model_used,
                duration_ms=duration_ms,
                success=True,
            )

        except Exception as e:
            duration_ms = round((time.time() - start) * 1000, 2)
            logger.error("Vision analysis failed: %s", e)
            return VisionResult(
                content="",
                model_used="",
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

    # ── Internal Helpers ──────────────────────────────────────────────────

    async def _try_llm_classify(
        self,
        user_input: str,
    ) -> Optional[ClassificationSignal]:
        """
        Attempt LLM classification using the active reasoning model.
        Returns None if no reasoning model is available or if the call fails.
        """
        # Get the reasoning model's provider
        reasoning_model = self.registry.get_model("reasoning")
        if not reasoning_model:
            logger.debug("No reasoning model configured — skipping LLM classification")
            return None

        try:
            # Classification must participate in the same lifecycle as the
            # later task. Otherwise an ambiguous coding request can leave the
            # reasoning model resident while the coder tries to load.
            await self.registry.load_model("reasoning")
            provider = self._get_provider(reasoning_model)
            return await gpu_scheduler.schedule(
                task_type="classification",
                priority=3,
                coro=self.llm_clf.classify(
                    user_input=user_input,
                    provider=provider,
                    model_id=reasoning_model.model_id,
                    temperature=self.policy.llm_temperature,
                    max_tokens=self.policy.llm_max_tokens,
                    timeout_seconds=self.policy.llm_timeout_seconds,
                ),
            )
        except Exception as e:
            logger.warning("LLM classification attempt failed: %s", e)
            return None

    def _merge_signals(
        self,
        keyword_signal: ClassificationSignal,
        llm_signal: Optional[ClassificationSignal],
        start_time: float,
    ) -> RoutingDecision:
        """
        Merge keyword and LLM signals into a final routing decision.

        Priority:
        1. If LLM signal exists and has higher confidence → use LLM
        2. Otherwise → use keyword signal
        """
        total_ms = round((time.time() - start_time) * 1000, 2)

        # Determine the winning signal
        if llm_signal and llm_signal.confidence > keyword_signal.confidence:
            winner = llm_signal
            used_llm = True
        else:
            winner = keyword_signal
            used_llm = llm_signal is not None  # LLM was tried but keyword won

        # Map task_type to model category
        category = TASK_TO_CATEGORY.get(winner.task_type, "reasoning")

        return RoutingDecision(
            task_type=winner.task_type,
            model_category=category,
            model_name=winner.model,
            confidence=winner.confidence,
            reason=winner.reason,
            keyword_signal=keyword_signal,
            llm_signal=llm_signal,
            used_llm=used_llm,
            total_classification_ms=total_ms,
            policy_llm_threshold=self.policy.llm_threshold,
            policy_prefer_llm=self.policy.prefer_llm,
        )

    def _resolve_system_prompt(
        self,
        caller_prompt: Optional[str],
        category: str,
        model: ModelConfig,
        task_type: str,
    ) -> str:
        """
        Resolve the system prompt to use, in priority order:
        1. Caller-provided system_prompt
        2. Coding-specific prompt (from coding module) for coding/data_analysis tasks
        3. Model's configured system_prompt
        4. Default reasoning system prompt
        """
        if caller_prompt:
            return caller_prompt

        # Phase 7: Use coding system prompt for coding tasks
        if category == "coding" or task_type in ("coding", "data_analysis"):
            return get_coding_system_prompt(task_type)

        # Phase 8: Use vision system prompt for vision tasks
        if category == "vision" or task_type == "vision":
            # If model config specifies a system prompt, use it (we will populate it via model_registry)
            if model.system_prompt:
                return model.system_prompt
            return get_vision_system_prompt()

        # Use model's configured system prompt
        if model.system_prompt:
            return model.system_prompt

        # Default fallback
        return (
            "You are a Sovereign AI assistant operating entirely on local hardware. "
            "You have access to internal enterprise documents, code execution, and "
            "document generation tools. You must never reference or attempt to access "
            "external services. All your knowledge comes from locally stored documents "
            "and your training data. When you lack internal evidence, say so clearly "
            "rather than fabricating information."
        )

    def _build_messages(
        self,
        user_input: str,
        system_prompt: str,
        session_id: Optional[str] = None,
        images: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Compatibility wrapper for callers that only need provider messages."""
        return self._build_prompt(user_input, system_prompt, session_id, images=images).messages

    def _build_prompt(
        self,
        user_input: str,
        system_prompt: str,
        session_id: Optional[str] = None,
        images: Optional[list[str]] = None,
    ) -> PromptBuild:
        """Build a stable static prefix and context-bounded dynamic suffix."""
        cleaned_images: Optional[list[str]] = None
        if images:
            from backend.router.vision import clean_base64_image
            cleaned_images = [
                cleaned
                for img in images
                if (cleaned := clean_base64_image(img))
            ] or None

        history = self.sessions.get_history(session_id) if session_id else []
        return self.context_budgeter.build_messages(
            system_prompt=system_prompt,
            user_request=user_input,
            history=history,
            images=cleaned_images,
        )


# Global instance
model_router = ModelRouter()
