import asyncio
import httpx
from pathlib import Path

API_URL = "http://127.0.0.1:8000/api/v1/workflows/run"
LOGIN_URL = "http://127.0.0.1:8000/api/v1/auth/login"

async def test_pid_workflow():
    print("[*] Logging in as admin...")
    async with httpx.AsyncClient() as client:
        res = await client.post(LOGIN_URL, json={"username": "admin", "password": "admin123"})
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            return
            
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[+] Logged in. Token received.")

    file_path = str(Path("demo_data/vision/pid_sample.jpg").absolute())
    
    print(f"[*] Testing P&ID Vision Workflow with {file_path} ...")
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            res = await client.post(API_URL, json={
                "workflow_name": "pid_vision",
                "inputs": {
                    "file_path": file_path,
                    "query": "Identify valves and equipment in this drawing and find their internal specifications."
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
    asyncio.run(test_pid_workflow())
