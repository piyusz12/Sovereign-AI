"""
Sovereign AI Workbench — Sovereignty Dashboard

Aggregates monitoring data for the sovereignty proof dashboard.
"""

from __future__ import annotations

from monitoring.sovereignty import sovereignty_monitor


def get_dashboard_summary() -> dict:
    """Get a full dashboard summary."""
    data = sovereignty_monitor.get_dashboard_data()
    return {
        **data,
        "display": {
            "External Requests": data["metrics"]["external_requests"],
            "External DNS Queries": data["metrics"]["external_dns_queries"],
            "Cloud AI Requests": data["metrics"]["cloud_ai_requests"],
            "Bytes Uploaded": data["metrics"]["bytes_uploaded_externally"],
            "Local API Calls": f"{data['metrics']['local_api_calls']:,}",
        },
    }
