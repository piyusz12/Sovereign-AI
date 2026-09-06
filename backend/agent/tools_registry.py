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
import base64
import concurrent.futures
import re
from dataclasses import dataclass
from pathlib import Path
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


def _run_coding_tool(user_request: str, context: str = "") -> ToolExecution:
    from backend.security.enforcement import authorize_action, SecurityException
    try:
        authorize_action("agent", "sandbox.execute", metadata={"network_enabled": False})
    except SecurityException as e:
        return ToolExecution("python_sandbox", False, "", f"SECURITY DENY: {e}")

    outcome = run_async_safely(generate_and_verify(user_request, context))
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
    from backend.security.enforcement import authorize_action, SecurityException
    from backend.rag.exceptions import RetrievalServiceError
    
    try:
        authorize_action("agent", "rag.search", metadata={"namespace": "general"})
    except SecurityException as e:
        return ToolExecution("document_reasoning", False, "", f"SECURITY DENY: {e}")

    try:
        query_embedding = await embedding_service.embed_text(query)
        candidates = await hybrid_retriever.search(
            query=query,
            query_embedding=query_embedding,
            top_k=10,
        )
        if candidates:
            candidates = await reranker_service.rerank(query, candidates, top_k=3)
    except RetrievalServiceError as e:
        return ToolExecution("document_reasoning", False, "", str(e))
    except Exception as e:
        return ToolExecution("document_reasoning", False, "", f"Internal retrieval error: {e}")
            
    if not candidates:
        return ToolExecution("document_reasoning", True, "No relevant documents found.", "")
        
    output = "Found documents:\n\n"
    for i, doc in enumerate(candidates, 1):
        title = doc.get("filename") or doc.get("title") or f"Doc {i}"
        score = doc.get("_rerank_score", 0.0)
        text = doc.get("text", "")
        
        # Truncate to prevent context window overflow (800 chars max per doc)
        if len(text) > 800:
            text = text[:800] + "\n... (truncated to save context)"
            
        output += f"--- {title} (Relevance: {score:.2f}) ---\n{text}\n\n"
        
    return ToolExecution("document_reasoning", True, output, "")

def _run_search_tool(user_request: str, context: str = "") -> ToolExecution:
    return run_async_safely(_execute_search(user_request))

def _run_unsupported_tool(task_type: str) -> Callable[[str, str], ToolExecution]:
    def _stub(_user_request: str, _context: str = "") -> ToolExecution:
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


async def _execute_vision_async(query: str, context: str = "") -> ToolExecution:
    from backend.router.vision import analyze_vision
    from backend.security.enforcement import authorize_action, SecurityException
    
    try:
        authorize_action("agent", "inspect_image")
    except SecurityException as e:
        return ToolExecution("vision", False, "", f"SECURITY DENY: {e}")
    
    # Extract file path from query, prioritizing quotes to handle spaces
    quoted_match = re.search(r'["\']([a-zA-Z]:\\[^"\']+|/[^"\']+)["\']', query)
    if quoted_match:
        path_str = quoted_match.group(1)
    else:
        path_match = re.search(r'([a-zA-Z]:\\[^\s]+|/[^\s]+)', query)
        if not path_match:
            return ToolExecution("vision", False, "", "Could not find a valid file path in the request.")
        path_str = path_match.group(1)
        
    image_path = Path(path_str.strip(".,'\""))
    
    if not image_path.exists() or not image_path.is_file():
        return ToolExecution("vision", False, "", f"Image file not found: {image_path}")
        
    try:
        b64_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        
        # Append high-level errors to the prompt if provided
        final_query = query
        if context:
            final_query += f"\n\nNote: Previous attempts failed with the following feedback:\n{context}"
            
        # If the user specifically asks for JSON or structured output
        wants_structured = "json" in final_query.lower() or "structured" in final_query.lower()
            
        result = await analyze_vision(prompt=final_query, image_base64=b64_data, structured=wants_structured)
        
        if result.success:
            return ToolExecution("vision", True, result.content, "")
        else:
            return ToolExecution("vision", False, "", result.error or "Vision analysis failed.")
    except Exception as e:
        return ToolExecution("vision", False, "", str(e))

def _run_vision_tool(user_request: str, context: str = "") -> ToolExecution:
    return run_async_safely(_execute_vision_async(user_request, context))


TOOL_REGISTRY: Dict[str, Callable[[str, str], ToolExecution]] = {
    "coding": _run_coding_tool,
    "document_reasoning": _run_search_tool,
    "vision": _run_vision_tool,
    "general_reasoning": _run_unsupported_tool("general_reasoning"),
}


def get_tool_for_task_type(task_type: str) -> Callable[[str, str], ToolExecution]:
    return TOOL_REGISTRY.get(task_type, _run_unsupported_tool(task_type))
