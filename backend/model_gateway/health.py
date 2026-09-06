from typing import Dict, Any
from backend.model_gateway.router import model_gateway

async def check_gateway_health() -> Dict[str, Any]:
    """
    Checks the health of the providers configured in the gateway.
    """
    status = {}
    for backend, provider in model_gateway._providers.items():
        try:
            is_alive = await provider.is_running()
            status[backend] = "READY" if is_alive else "UNAVAILABLE"
        except Exception:
            status[backend] = "ERROR"
            
    return status
