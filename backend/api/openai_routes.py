"""
Sovereign AI Workbench — OpenAI Compatible API Routes

Exposes standard OpenAI endpoints (/v1/chat/completions, /v1/models)
so any standard OpenAI client (LangChain, OpenAI Python SDK, curl)
can seamlessly interact with the local router.
"""

import json
import logging
import uuid
import time
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.api.openai_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    ChatCompletionMessage,
    Choice,
    StreamChoice,
    Delta,
    Usage,
    ModelListResponse,
    ModelCard,
)
from backend.router.router import model_router
from backend.router.model_registry import model_registry

logger = logging.getLogger("sovereign.openai_api")

openai_router = APIRouter()


@openai_router.get("/models", response_model=ModelListResponse)
async def list_models():
    """
    OpenAI compatible endpoint to list available models.
    Maps our registry's model IDs to OpenAI ModelCards.
    """
    models = model_registry.list_models()
    return ModelListResponse(
        data=[
            ModelCard(id=m["model_id"])
            for m in models
        ]
    )


@openai_router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest, raw_request: Request):
    """
    OpenAI compatible /v1/chat/completions endpoint.
    Routes through our ModelRouter for single-GPU discipline and classification.
    """
    # Extract the last user message as the primary input for classification
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message provided")
        
    user_input = user_messages[-1].content
    
    # Extract system prompt if present
    system_messages = [m for m in request.messages if m.role == "system"]
    system_prompt = system_messages[-1].content if system_messages else None
    
    # Determine if there's history we should use
    # If the client sent a full history and no session_id is provided, 
    # the router's _build_messages will just use the current prompt.
    # To fully support generic OpenAI clients sending full history,
    # we should ideally pass the exact messages to the provider. 
    # For Phase 5, we rely on our router's _build_messages or session manager.
    
    request_id = f"chatcmpl-{uuid.uuid4().hex}"
    
    if request.stream:
        async def event_generator():
            try:
                # Send the first chunk with role
                init_choice = StreamChoice(
                    index=0,
                    delta=Delta(role="assistant"),
                    finish_reason=None
                )
                init_resp = ChatCompletionStreamResponse(
                    id=request_id,
                    model=request.model,
                    choices=[init_choice]
                )
                yield f"data: {init_resp.model_dump_json(exclude_none=True)}\n\n"
                
                async for chunk_data in model_router.route_stream(
                    user_input=user_input,
                    system_prompt=system_prompt,
                    force_model=request.force_category,
                    temperature=request.temperature or 0.7,
                    max_tokens=request.max_tokens or 4096,
                    session_id=request.session_id,
                ):
                    if chunk_data.get("done"):
                        # Final chunk
                        final_choice = StreamChoice(
                            index=0,
                            delta=Delta(),
                            finish_reason="stop"
                        )
                        final_resp = ChatCompletionStreamResponse(
                            id=request_id,
                            model=chunk_data.get("model_used", {}).get("model_id", request.model),
                            choices=[final_choice]
                        )
                        yield f"data: {final_resp.model_dump_json(exclude_none=True)}\n\n"
                        yield "data: [DONE]\n\n"
                    else:
                        # Content chunk
                        content_choice = StreamChoice(
                            index=0,
                            delta=Delta(content=chunk_data.get("chunk", "")),
                            finish_reason=None
                        )
                        content_resp = ChatCompletionStreamResponse(
                            id=request_id,
                            model=request.model,
                            choices=[content_choice]
                        )
                        yield f"data: {content_resp.model_dump_json(exclude_none=True)}\n\n"
                        
            except Exception as e:
                logger.error("Stream error in OpenAI API: %s", e)
                error_choice = StreamChoice(
                    index=0,
                    delta=Delta(content=f"\n[Error: {e}]"),
                    finish_reason="error"
                )
                error_resp = ChatCompletionStreamResponse(
                    id=request_id,
                    model=request.model,
                    choices=[error_choice]
                )
                yield f"data: {error_resp.model_dump_json(exclude_none=True)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    else:
        # Non-streaming
        try:
            result = await model_router.route(
                user_input=user_input,
                system_prompt=system_prompt,
                force_model=request.force_category,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 4096,
                session_id=request.session_id,
            )
            
            response_text = result.get("response", "")
            metrics = result.get("metrics", {})
            eval_count = metrics.get("eval_count", 0)
            prompt_eval_count = metrics.get("prompt_eval_count", 0)
            model_used = result.get("model_used", {}).get("model_id", request.model)
            
            return ChatCompletionResponse(
                id=request_id,
                model=model_used,
                choices=[
                    Choice(
                        index=0,
                        message=ChatCompletionMessage(content=response_text),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=prompt_eval_count + eval_count
                )
            )
            
        except Exception as e:
            logger.error("Error in OpenAI API chat completion: %s", e)
            raise HTTPException(status_code=500, detail=str(e))
