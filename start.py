"""
Sovereign AI Workbench — Entry Point

Windows-safe startup script.

Usage:
    python start.py
"""

import uvicorn
from backend.settings import settings
from backend.logging_config import setup_logging


def main():
    setup_logging(settings.log_level)

    uvicorn.run(
        "backend.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
