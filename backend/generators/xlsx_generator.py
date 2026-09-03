"""
Sovereign AI Workbench — XLSX Generator

Generate Excel spreadsheets from data analysis results.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("sovereign.generators.xlsx")


class XlsxGenerator:
    """Generate formatted Excel spreadsheets."""

    def __init__(self, output_dir: str = "./data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_analysis_report(
        self, title: str, data: list[dict], summary: dict | None = None
    ) -> str:
        """Generate an analysis report spreadsheet."""
        try:
            import pandas as pd

            df = pd.DataFrame(data)
            filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = self.output_dir / filename

            with pd.ExcelWriter(str(filepath), engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)
                if summary:
                    pd.DataFrame([summary]).to_excel(writer, sheet_name="Summary", index=False)

            logger.info("Generated XLSX: %s", filepath)
            return str(filepath)

        except ImportError:
            logger.error("pandas/openpyxl not installed")
            return ""


# Global instance
xlsx_generator = XlsxGenerator()
