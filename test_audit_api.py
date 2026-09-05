import asyncio
import httpx

API_URL = "http://127.0.0.1:8000/api/v1/audit/events"
LOGIN_URL = "http://127.0.0.1:8000/api/v1/auth/login"

async def test_audit_endpoints():
    print("[*] Logging in as admin to test audit...")
    async with httpx.AsyncClient() as client:
        res = await client.post(LOGIN_URL, json={"username": "admin", "password": "admin123"})
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            return
            
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[+] Logged in. Token received.")

    print(f"[*] Fetching Audit Events...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.get(API_URL, headers=headers)
            print(f"Status: {res.status_code}")
            data = res.json()
            
            total = data.get("total", 0)
            events = data.get("events", [])
            print(f"[+] Found {total} audit events.")
            
            if events:
                print("\n[*] Sample Event:")
                for k, v in events[0].items():
                    print(f"    {k}: {v}")
                    
                trace_id = events[0].get("trace_id")
                if trace_id:
                    print(f"\n[*] Fetching Workflow Trace {trace_id}...")
                    res_trace = await client.get(f"http://127.0.0.1:8000/api/v1/audit/workflows/{trace_id}", headers=headers)
                    print(f"Status: {res_trace.status_code}")
                    if res_trace.status_code == 200:
                        trace_data = res_trace.json()
                        print(f"[+] Found {trace_data.get('total')} events in this trace.")
                        for e in trace_data.get("events", []):
                            print(f"    - {e['timestamp']} | {e['action']} | {e['status']} | {e.get('resource_id', '')}")
                    else:
                        print(f"Failed to fetch trace: {res_trace.text}")
            else:
                print("[-] No events found yet. Run the workflow first.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_audit_endpoints())
