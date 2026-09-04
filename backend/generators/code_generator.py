"""
Sovereign AI Workbench — Code Package Generator

Generate a compressed ZIP package containing working code, 
requirements, README, and basic tests.
"""

from __future__ import annotations

import logging
import zipfile
import io
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("sovereign.generators.code")


class CodeGenerator:
    """Generate and package source code into a ZIP deliverable."""

    def __init__(self, output_dir: str = "./data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_code_package(self, title: str, files: dict[str, str]) -> str:
        """
        Generate a ZIP file containing the provided source code files.
        
        Args:
            title: Project title
            files: Dictionary mapping relative file paths to their string content.
                   (e.g. {"main.py": "print('hello')", "requirements.txt": "requests"})
        """
        try:
            filename = f"code_package_{title.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            filepath = self.output_dir / filename
            
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                for relative_path, content in files.items():
                    # Ensure paths are safe and relative
                    safe_path = Path(relative_path).as_posix()
                    if safe_path.startswith('/'):
                        safe_path = safe_path[1:]
                    
                    zf.writestr(safe_path, content)
                    
            logger.info("Generated Code Package: %s", filepath)
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to generate code package: {e}")
            return ""


# Global instance
code_generator = CodeGenerator()
