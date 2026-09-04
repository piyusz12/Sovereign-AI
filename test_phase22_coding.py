import asyncio
import httpx
import os
from pathlib import Path

API_URL = "http://127.0.0.1:8000/api/v1/workflows/run"

async def test_coding_workflow():
    print("[*] Logging in as admin...")
    async with httpx.AsyncClient() as client:
        res = await client.post("http://127.0.0.1:8000/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            return
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[+] Logged in. Token received.")

    file_path = str(Path("demo_data/telemetry/sensor_data.xlsx").absolute())
    
    print(f"[*] Testing Coding Workflow with {file_path} ...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            res = await client.post(API_URL, json={
                "workflow_name": "coding",
                "inputs": {
                    "file_path": file_path,
                    "query": "Analyze this telemetry data. Calculate the average temperature (excluding negative/error anomalies like -99.9), detect pressure anomalies (e.g., > 200 PSI), and output a JSON summary."
                }
            }, headers=headers)
            
            print(f"Status: {res.status_code}")
            data = res.json()
            print(data)
            
            if data.get("deliverables"):
                print("\n[+] Workflow deliverables:")
                for d in data["deliverables"]:
                    print(f"    - {d}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_coding_workflow())
