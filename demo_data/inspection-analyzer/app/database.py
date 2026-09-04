import json

def get_inspection_results():
    # Mock data for demonstration
    return [
        {"id": "INS-001", "equipment": "Pump-A", "pressure": 110, "status": "PASS"},
        {"id": "INS-002", "equipment": "Valve-B", "pressure": 45, "status": "FAIL"},
        {"id": "INS-003", "equipment": "Pump-C", "pressure": 105, "status": "PASS"},
    ]
