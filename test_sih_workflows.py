import asyncio
import httpx
from pathlib import Path

API_URL = "http://127.0.0.1:8000/api/v1/workflows/run"

async def test_workflows():
    # Make a dummy PDF for the vision router to see
    dummy_pdf = Path("test_inspection.pdf")
    dummy_pdf.write_text("dummy pdf content")
    
    # We will just test if the endpoint runs (it might fail internal steps, but the orchestrator should work)
    print("Logging in...")
    async with httpx.AsyncClient() as client:
        res = await client.post("http://127.0.0.1:8000/api/v1/auth/login", data={"username": "admin", "password": "password"})
        token = res.json()["access_token"]

    print("Testing Inspection Workflow...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(API_URL, json={
                "workflow_name": "inspection",
                "inputs": {
                    "file_path": str(dummy_pdf),
                    "query": "Review this inspection report."
                }
            }, headers={"Authorization": f"Bearer {token}"}, timeout=60.0)
            
            print(f"Status: {res.status_code}")
            print(res.json())
        except Exception as e:
            print(f"Error: {e}")
            
    print("\nTesting Coding Workflow...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(API_URL, json={
                "workflow_name": "coding",
                "inputs": {
                    "file_path": "data.csv",
                    "query": "Analyze this data."
                }
            }, headers={"Authorization": f"Bearer {token}"}, timeout=60.0)
            
            print(f"Status: {res.status_code}")
            print(res.json())
        except Exception as e:
            print(f"Error: {e}")
            
    dummy_pdf.unlink(missing_ok=True)

if __name__ == "__main__":
    asyncio.run(test_workflows())
