import asyncio
from httpx import AsyncClient
import os

async def main():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # We will test docx, xlsx, pptx locally since we have a direct dependency
    # on the generator files.
    # To test the API we need a valid JWT token with report.create permission
    
    async with AsyncClient(base_url=base_url) as client:
        # 1. Login as admin user
        print("[*] Logging in as admin...")
        login_resp = await client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        if login_resp.status_code != 200:
            print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[+] Logged in. Token received.")
        
        # 2. Test DOCX Generation
        print("[*] Testing /generate DOCX...")
        docx_req = {
            "request_type": "report",
            "output_format": "docx",
            "source_data": {
                "title": "Test Report",
                "sections": [{"title": "Overview", "content": "This is a test document."}]
            }
        }
        docx_resp = await client.post("/generate", json=docx_req, headers=headers)
        print(f"    Status: {docx_resp.status_code}")
        if docx_resp.status_code == 200:
            print(f"    [+] PASS: {docx_resp.json()}")
        else:
            print(f"    [!] FAIL: {docx_resp.text}")
            
        # 3. Test XLSX Generation
        print("[*] Testing /generate XLSX...")
        xlsx_req = {
            "request_type": "analysis",
            "output_format": "xlsx",
            "source_data": {
                "title": "Test Analysis",
                "data": [{"Metric": "Accuracy", "Value": 99.9}]
            }
        }
        xlsx_resp = await client.post("/generate", json=xlsx_req, headers=headers)
        print(f"    Status: {xlsx_resp.status_code}")
        if xlsx_resp.status_code == 200:
            print(f"    [+] PASS: {xlsx_resp.json()}")
        else:
            print(f"    [!] FAIL: {xlsx_resp.text}")
            
        # 4. Test PPTX Generation
        print("[*] Testing /generate PPTX...")
        pptx_req = {
            "request_type": "report",
            "output_format": "pptx",
            "source_data": {
                "title": "Test Presentation",
                "slides": [{"title": "Agenda", "content": "1. Testing", "bullets": ["A", "B"]}]
            }
        }
        pptx_resp = await client.post("/generate", json=pptx_req, headers=headers)
        print(f"    Status: {pptx_resp.status_code}")
        if pptx_resp.status_code == 200:
            print(f"    [+] PASS: {pptx_resp.json()}")
        # 5. Test ZIP Generation
        print("[*] Testing /generate ZIP...")
        zip_req = {
            "request_type": "code_package",
            "output_format": "zip",
            "source_data": {
                "title": "Test Package",
                "files": {
                    "main.py": "print('hello world')",
                    "requirements.txt": "requests"
                }
            }
        }
        zip_resp = await client.post("/generate", json=zip_req, headers=headers)
        print(f"    Status: {zip_resp.status_code}")
        if zip_resp.status_code == 200:
            print(f"    [+] PASS: {zip_resp.json()}")
        else:
            print(f"    [!] FAIL: {zip_resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
