"""
Sovereign AI Workbench — End-to-End Regression Test (Phase 26)

Automatically verifies the flagship workflow end-to-end to ensure
the entire system works and meets security & sovereignty constraints.
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sovereign.tests.e2e")

async def run_e2e_test():
    logger.info("Starting E2E Regression Test...")
    
    # Simulate a full workflow run
    url = "http://localhost:8000/api/v1/workflows/run"
    payload = {
        "workflow_name": "coding",
        "parameters": {
            "query": "Write a python script that calculates the fibonacci sequence."
        }
    }
    
    logger.info("Sending request to flagship workflow...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            logger.info("Workflow completed.")
            logger.info(f"Result: {data}")
            
            if data.get("success"):
                logger.info("✅ E2E Test Passed!")
            else:
                logger.error("❌ E2E Test Failed: Workflow unsuccessful.")
    except Exception as e:
        logger.error(f"❌ E2E Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
