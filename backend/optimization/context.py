"""Deterministic, budget-aware prompt construction for local inference.

Static instructions are kept at the beginning of every request, while the
volatile conversation, retrieved evidence and current request are appended at
the end. This ordering preserves reusable prompt prefixes for compatible
runtimes and makes context pressure explicit on an 8 GB GPU.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class PromptBudget:
    """A transparent account of how the input budget was spent."""

    max_input_tokens: int
    static_tokens: int
    history_tokens: int
    retrieved_tokens: int
    user_tokens: int
    dropped_history_messages: int
    dropped_retrieved_documents: int

    @property
    def used_tokens(self) -> int:
        return self.static_tokens + self.history_tokens + self.retrieved_tokens + self.user_tokens


@dataclass(frozen=True)
class PromptBuild:
    """The constructed messages and metadata that describes their reuse."""

    messages: list[dict[str, Any]]
    prefix_key: str
    budget: PromptBudget


class ContextBudgeter:
    """Build deterministic prompts without allowing context to consume VRAM.

    Token estimation intentionally stays dependency-free. It is conservative
    enough to keep the service safe when the exact model tokenizer is not
    available and can later be replaced by a model-specific tokenizer.
    """

    def __init__(self, max_total_tokens: int = 8192, output_reserve_tokens: int = 1024) -> None:
        if max_total_tokens <= output_reserve_tokens:
            raise ValueError("max_total_tokens must exceed output_reserve_tokens")
        self.max_total_tokens = max_total_tokens
        self.output_reserve_tokens = output_reserve_tokens

    @property
    def max_input_tokens(self) -> int:
        return self.max_total_tokens - self.output_reserve_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Conservative local estimate: roughly one token per four characters."""
        return max(0, (len(text or "") + 3) // 4)

    def _truncate(self, text: str, token_budget: int) -> str:
        if token_budget <= 0:
            return ""
        char_budget = token_budget * 4
        if len(text) <= char_budget:
            return text
        suffix = "\n...[truncated for context budget]"
        if char_budget <= len(suffix):
            return text[:char_budget]
        # Retain whole words where possible so retrieved evidence stays legible.
        content_budget = char_budget - len(suffix)
        clipped = text[:content_budget].rsplit(" ", 1)[0].rstrip()
        return f"{clipped or text[:content_budget]}{suffix}"

    def _fit_history(
        self, history: Sequence[dict[str, Any]], remaining_tokens: int
    ) -> tuple[list[dict[str, Any]], int, int]:
        """Keep the newest complete history messages that fit the remaining budget."""
        selected_reversed: list[dict[str, Any]] = []
        used = 0
        for message in reversed(history):
            content = str(message.get("content", ""))
            tokens = self.estimate_tokens(content)
            if tokens > remaining_tokens - used:
                continue
            selected_reversed.append(dict(message))
            used += tokens
        selected = list(reversed(selected_reversed))
        return selected, used, len(history) - len(selected)

    def _fit_retrieved(
        self, documents: Iterable[str], remaining_tokens: int
    ) -> tuple[list[str], int, int]:
        """Keep ranked evidence in input order and trim only the final fitting item."""
        selected: list[str] = []
        used = 0
        dropped = 0
        for document in documents:
            document = str(document or "").strip()
            if not document:
                continue
            tokens = self.estimate_tokens(document)
            # Reserve room for the deterministic evidence label added below.
            label_tokens = 8
            available = remaining_tokens - used
            if available <= 0:
                dropped += 1
                continue
            if tokens + label_tokens <= available:
                selected.append(document)
                used += tokens + label_tokens
                continue
            if not selected:
                selected.append(self._truncate(document, max(available - label_tokens, 0)))
                used += self.estimate_tokens(selected[-1]) + label_tokens
            dropped += 1
        return selected, used, dropped

    def build_messages(
        self,
        *,
        system_prompt: str,
        user_request: str,
        history: Sequence[dict[str, Any]] | None = None,
        retrieved_documents: Iterable[str] | None = None,
        static_context: str = "",
        images: Sequence[str] | None = None,
    ) -> PromptBuild:
        """Construct a stable prefix followed by only the evidence that fits.

        Order is immutable: system instructions, static enterprise context,
        retained conversation, retrieved evidence, then the current request.
        Dynamic IDs, timestamps and tracing data must never be inserted before
        the static prefix.
        """
        history = history or []
        retrieved_documents = retrieved_documents or []
        static_parts = [part.strip() for part in (system_prompt, static_context) if part and part.strip()]
        # A malformed or overgrown policy must not evict the current request.
        # Preserve up to half of the input window for that request before
        # clipping the reusable static prefix.
        requested_user_tokens = self.estimate_tokens(user_request or "")
        user_reserve = min(requested_user_tokens, max(1, self.max_input_tokens // 2))
        static_text = self._truncate(
            "\n\n".join(static_parts),
            self.max_input_tokens - user_reserve,
        )
        static_tokens = self.estimate_tokens(static_text)

        # The current request always wins over stale conversation/evidence.
        user_text = self._truncate(user_request or "", max(self.max_input_tokens - static_tokens, 0))
        user_tokens = self.estimate_tokens(user_text)
        remaining = max(self.max_input_tokens - static_tokens - user_tokens, 0)

        # Allocate evidence before history: citations outrank older chat turns.
        retrieved, retrieved_tokens, dropped_docs = self._fit_retrieved(retrieved_documents, remaining)
        remaining -= retrieved_tokens
        retained_history, history_tokens, dropped_history = self._fit_history(history, remaining)

        messages: list[dict[str, Any]] = []
        if static_text:
            messages.append({"role": "system", "content": static_text})
        messages.extend(retained_history)
        if retrieved:
            evidence = "\n\n".join(
                f"[Retrieved evidence {index}]\n{document}"
                for index, document in enumerate(retrieved, start=1)
            )
            messages.append({"role": "system", "content": evidence})

        user_message: dict[str, Any] = {"role": "user", "content": user_text}
        if images:
            user_message["images"] = list(images)
        messages.append(user_message)

        prefix_key = sha256(static_text.encode("utf-8")).hexdigest()
        return PromptBuild(
            messages=messages,
            prefix_key=prefix_key,
            budget=PromptBudget(
                max_input_tokens=self.max_input_tokens,
                static_tokens=static_tokens,
                history_tokens=history_tokens,
                retrieved_tokens=retrieved_tokens,
                user_tokens=user_tokens,
                dropped_history_messages=dropped_history,
                dropped_retrieved_documents=dropped_docs,
            ),
        )

    def trim_context(
        self,
        system_prompt: str,
        user_request: str,
        retrieved_docs: list[str],
        tool_results: str,
    ) -> tuple[str, str]:
        """Compatibility API for callers from the first optimization phase."""
        build = self.build_messages(
            system_prompt=system_prompt,
            user_request=user_request,
            retrieved_documents=retrieved_docs,
        )
        evidence = next(
            (
                message["content"]
                for message in build.messages
                if message["role"] == "system" and message["content"] != system_prompt
            ),
            "",
        )
        remaining = max(self.max_input_tokens - build.budget.used_tokens, 0)
        return evidence, self._truncate(tool_results or "", remaining)


context_budgeter = ContextBudgeter()
