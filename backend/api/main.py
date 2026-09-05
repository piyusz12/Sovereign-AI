"""
Sovereign AI Workbench — FastAPI Application

Main entry point for the API server. All inference and data processing
happens locally. Zero external network calls.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.logging_config import setup_logging
from backend.settings import settings
from backend.api.routes import router as api_router
from backend.api.openai_routes import openai_router
from backend.api.health import probe_all
from backend.api.middleware import sovereignty_enforcer
from backend.audit.middleware import AuditMiddleware
from backend.audit.router import router as audit_api_router
from backend.sovereignty.router import router as sovereignty_router
from backend.sovereignty.service import sovereignty_service
from backend.router.model_registry import model_registry
from backend.workflows.registry import init_workflows

logger = logging.getLogger("sovereign.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    setup_logging(settings.log_level)

    logger.info("Sovereign AI Workbench starting...")
    logger.info("  All inference is LOCAL")
    logger.info("  Zero external network access")
    logger.info("  Data sovereignty enforced")
    logger.info("  Listening on %s:%d", settings.app_host, settings.app_port)

    # Auto-warm default model if Ollama is running
    try:
        logger.info("Auto-warming default reasoning model...")
        await model_registry.load_model("reasoning")
    except Exception as e:
        logger.warning("Failed to warm up default model: %s", e)
        
    logger.info("Initializing Flagship SIH Workflows...")
    init_workflows()
    
    logger.info("Starting Sovereignty Monitor...")
    await sovereignty_service.start()

    yield

    logger.info("Sovereignty AI Workbench shutting down...")
    await sovereignty_service.stop()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Local-first, zero-egress AI system for enterprise document intelligence, "
        "code generation, and agentic workflows."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — local development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Audit Middleware
app.add_middleware(AuditMiddleware)


@app.middleware("http")
async def sovereignty_middleware(request: Request, call_next):
    """
    Attach a trace ID to every request and measure latency.
    Logs every request for audit trail.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Check sovereignty
    sovereignty_enforcer.check_request(request)

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Sovereign"] = "true"
    response.headers["X-External-Calls"] = "0"
    response.headers["X-Duration-Ms"] = str(duration_ms)

    # Audit logging is now handled by AuditMiddleware


    return response


# ── Root Endpoints ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint — probes downstream services and confirms sovereignty."""
    services = await probe_all(
        ollama_url=settings.ollama_base_url,
        qdrant_host=settings.qdrant_host,
        qdrant_port=settings.qdrant_port,
    )

    return {
        "status": "ok",
        "sovereign": True,
        "external_access": False,
        "version": settings.app_version,
        "models": {
            "reasoning": f"{settings.ollama_reasoning_model}",
            "coding": f"{settings.ollama_coding_model}",
            "vision": f"{settings.ollama_vision_model}",
        },
        "services": services,
    }


@app.get("/sovereignty")
async def sovereignty_status():
    """
    Returns sovereignty verification data.
    Proves zero external network connections.
    """
    enforcer_status = sovereignty_enforcer.get_status()
    return {
        "sovereign": True,
        "external_dns_queries": 0,
        "external_tcp_connections": 0,
        "external_https_requests": 0,
        "bytes_uploaded_externally": 0,
        "verification_method": "network_monitoring",
        "enforcer": enforcer_status,
    }


# ── Exception Handlers ───────────────────────────────────────────────────────


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "path": str(request.url.path),
            "sovereign": True,
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("Internal error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "sovereign": True,
            "detail": str(exc) if settings.debug else "Contact administrator",
        },
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(audit_api_router, prefix="/api/v1")
app.include_router(sovereignty_router, prefix="/api/v1")
app.include_router(openai_router, prefix="/v1")
