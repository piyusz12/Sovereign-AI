"""
Minimal tool registry for Phase 11.

The full tool framework (read_file, write_file, search_documents,
inspect_image, create_docx, etc.) is Phase 10 / later phases. As of
Phase 11 only ONE real tool exists end-to-end: the Phase 8/9 code
generate+execute+repair loop. Everything else is registered as a stub so
the graph's routing logic is already correct for tools that don't exist
yet — adding a new tool later means adding one entry here, not touching
the graph.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict

from backend.agent.code_repair_loop import generate_and_verify


@dataclass
class ToolExecution:
    tool_name: str
    success: bool
    output: str
    error: str


def run_async_safely(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Safely execute an asynchronous coroutine in either a synchronous
    environment or from within an already running event loop (e.g. FastAPI / pytest).
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Running event loop exists — offload asyncio.run to a background worker thread
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    else:
        return asyncio.run(coro)


def _run_coding_tool(user_request: str) -> ToolExecution:
    outcome = run_async_safely(generate_and_verify(user_request))
    return ToolExecution(
        tool_name="python_sandbox",
        success=outcome.success,
        output=outcome.stdout,
        error=outcome.stderr,
    )

async def _execute_search(query: str) -> ToolExecution:
    from backend.rag.embedder import embedding_service
    from backend.rag.retriever import hybrid_retriever
    from backend.rag.reranker import reranker_service
    try:
        query_embedding = await embedding_service.embed_text(query)
        candidates = await hybrid_retriever.search(
            query=query,
            query_embedding=query_embedding,
            top_k=10,
        )
        if candidates:
            candidates = await reranker_service.rerank(query, candidates, top_k=3)
            
        if not candidates:
            return ToolExecution("document_reasoning", True, "No relevant documents found.", "")
            
        output = "Found documents:\n\n"
        for i, doc in enumerate(candidates, 1):
            title = doc.get("filename") or doc.get("title") or f"Doc {i}"
            score = doc.get("_rerank_score", 0.0)
            text = doc.get("text", "")
            output += f"--- {title} (Relevance: {score:.2f}) ---\n{text}\n\n"
            
        return ToolExecution("document_reasoning", True, output, "")
    except Exception as e:
        return ToolExecution("document_reasoning", False, "", str(e))

def _run_search_tool(user_request: str) -> ToolExecution:
    return run_async_safely(_execute_search(user_request))

def _run_unsupported_tool(task_type: str) -> Callable[[str], ToolExecution]:
    def _stub(_user_request: str) -> ToolExecution:
        return ToolExecution(
            tool_name=f"unsupported:{task_type}",
            success=False,
            output="",
            error=(
                f"No tool is implemented yet for task_type='{task_type}'. "
                "This lands in a later phase (document_reasoning -> Phase 17 "
                "RAG, vision -> Phase 19)."
            ),
        )

    return _stub


TOOL_REGISTRY: Dict[str, Callable[[str], ToolExecution]] = {
    "coding": _run_coding_tool,
    "document_reasoning": _run_search_tool,
    "vision": _run_unsupported_tool("vision"),
    "general_reasoning": _run_unsupported_tool("general_reasoning"),
}


def get_tool_for_task_type(task_type: str) -> Callable[[str], ToolExecution]:
    return TOOL_REGISTRY.get(task_type, _run_unsupported_tool(task_type))
