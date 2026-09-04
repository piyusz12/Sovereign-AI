import json
from .database import get_inspection_results

def get_inspection_summary():
    results = get_inspection_results()
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    return {"total_inspections": total, "passed": passed}

# TODO: Add a feature that exports inspection results as CSV,
# identifies equipment with measurements below the configured threshold, 
# and exposes the results through an API endpoint.
