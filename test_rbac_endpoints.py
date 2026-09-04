import asyncio
import json
from httpx import AsyncClient

async def main():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    async with AsyncClient(base_url=base_url) as client:
        # 1. Login as finance_user
        print("[*] Logging in as finance_user...")
        login_resp = await client.post("/auth/login", json={"username": "finance_user", "password": "fin123"})
        if login_resp.status_code != 200:
            print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[+] Logged in. Token received.")
        
        # 2. Test /chat endpoint (should succeed, finance_user has ai.chat)
        print("[*] Testing /chat endpoint (requires ai.chat)...")
        chat_req = {
            "message": "Hello, this is a test.",
            "session_id": "test_session_1"
        }
        chat_resp = await client.post("/chat", json=chat_req, headers=headers)
        print(f"    Status: {chat_resp.status_code}")
        if chat_resp.status_code == 403:
            print("    [!] FAILED: Should be allowed.")
        else:
            print("    [+] PASS (Allowed or expected 503 if ollama is off)")
            
        # 3. Test /code/generate endpoint (should fail, finance_user DOES NOT have agent.execute_code)
        print("[*] Testing /code/generate endpoint (requires agent.execute_code)...")
        code_req = {
            "prompt": "Write a python script",
            "language": "python"
        }
        code_resp = await client.post("/code/generate", json=code_req, headers=headers)
        print(f"    Status: {code_resp.status_code}")
        if code_resp.status_code == 403:
            print("    [+] PASS: Correctly blocked by RBAC Enforcer (HTTP 403).")
        else:
            print(f"    [!] FAILED: Expected 403 Forbidden, got {code_resp.status_code}")
            
if __name__ == "__main__":
    asyncio.run(main())
