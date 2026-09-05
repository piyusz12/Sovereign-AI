import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.audit.context import (
    current_trace_id,
    current_session_id,
    current_user_id,
    current_role,
)
from backend.audit.service import audit_service


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate a trace ID for this request if not already set
        trace_id = f"WF-{uuid.uuid4().hex[:6].upper()}"
        
        # Set context variables for this request
        trace_token = current_trace_id.set(trace_id)
        
        # We can also attempt to extract user context from the authorization header if we wanted to
        # but that is often better done in the auth dependency to ensure cryptographic verification.
        # However, we can log the API request start
        start_time = time.time()
        
        # Log the API entry
        audit_service.log(
            action="api.request",
            status="started",
            resource_type="endpoint",
            resource_id=request.url.path,
            source_ip=request.client.host if request.client else None,
            metadata={"method": request.method}
        )

        try:
            response = await call_next(request)
            
            # Log the API success
            audit_service.log(
                action="api.response",
                status="success" if response.status_code < 400 else "failure",
                resource_type="endpoint",
                resource_id=request.url.path,
                metadata={
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": round((time.time() - start_time) * 1000, 2)
                }
            )
            return response
            
        except Exception as e:
            # Log unhandled exceptions
            audit_service.log(
                action="api.response",
                status="error",
                resource_type="endpoint",
                resource_id=request.url.path,
                error_code=type(e).__name__,
                metadata={
                    "method": request.method,
                    "error": str(e),
                    "duration_ms": round((time.time() - start_time) * 1000, 2)
                }
            )
            raise e
        finally:
            # Clean up context
            current_trace_id.reset(trace_token)
