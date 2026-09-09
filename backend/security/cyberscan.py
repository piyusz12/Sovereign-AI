"""
Sovereign AI: Isolated CyberScan Agent & AI Code Security Scanner
Scans source code, MCP tool specifications, and RAG pipelines for prompt injection attack vectors,
command injection, path traversals, weak cryptography, and permission leakages with exact line attribution.
"""

import os
import re
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class VulnerabilityFinding:
    finding_id: str
    file_path: str
    line_number: int
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    category: str  # "PROMPT_INJECTION", "SHELL_EXECUTION", "PATH_TRAVERSAL", "WEAK_CRYPTO", "INSECURE_AUTH"
    snippet: str
    description: str
    remediation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CyberScanReport:
    scan_id: str
    timestamp: float
    scanned_target: str
    files_scanned: int
    findings_count: int
    severity_breakdown: Dict[str, int]
    findings: List[VulnerabilityFinding]
    compliance_score: float  # 0 to 100
    sovereign_posture: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp,
            "scanned_target": self.scanned_target,
            "files_scanned": self.files_scanned,
            "findings_count": self.findings_count,
            "severity_breakdown": self.severity_breakdown,
            "findings": [f.to_dict() for f in self.findings],
            "compliance_score": self.compliance_score,
            "sovereign_posture": self.sovereign_posture
        }


class CyberScanAgent:
    """
    Automated security auditor for sovereign AI repositories and generated code.
    """

    PATTERNS = [
        (
            r"(?i)(ignore\s+all\s+previous\s+instructions|system\s+prompt\s+override|disregard\s+guidelines)",
            "PROMPT_INJECTION",
            "CRITICAL",
            "Direct Prompt Injection attempt detected.",
            "Enforce strict input boundaries and filter against prompt injection heuristics before LLM context injection."
        ),
        (
            r"subprocess\.(Popen|call|run)\([^)]*shell\s*=\s*True",
            "SHELL_EXECUTION",
            "HIGH",
            "Insecure subprocess invocation with shell=True detected.",
            "Pass arguments as an explicit array of strings without shell=True to prevent command injection."
        ),
        (
            r"(?i)(password|secret|api_key|token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]",
            "INSECURE_AUTH",
            "HIGH",
            "Hardcoded credential or secret detected in source code.",
            "Store secrets in environment variables or sovereign hardware keystores."
        ),
        (
            r"hashlib\.(md5|sha1)\(",
            "WEAK_CRYPTO",
            "MEDIUM",
            "Collision-vulnerable hashing algorithm (MD5/SHA1) detected.",
            "Upgrade to cryptographic SHA-256 or SHA-384."
        ),
        (
            r"\.\./\.\./",
            "PATH_TRAVERSAL",
            "HIGH",
            "Unsanitized relative path traversal pattern detected.",
            "Use os.path.abspath and verify path resides within allowed workspace sandbox."
        ),
    ]

    def __init__(self):
        pass

    def scan_code_snippet(self, code: str, file_label: str = "snippet.py") -> List[VulnerabilityFinding]:
        """
        Scans a single string of code or prompt against sovereign security rules.
        """
        findings: List[VulnerabilityFinding] = []
        lines = code.splitlines()

        for idx, line in enumerate(lines, 1):
            for regex, category, severity, desc, remed in self.PATTERNS:
                if re.search(regex, line):
                    fid = f"VULN-{category[:4]}-{int(time.time()*1000)%10000}-{len(findings)+1}"
                    findings.append(VulnerabilityFinding(
                        finding_id=fid,
                        file_path=file_label,
                        line_number=idx,
                        severity=severity,
                        category=category,
                        snippet=line.strip()[:100],
                        description=desc,
                        remediation=remed
                    ))

        return findings

    def run_repository_scan(self, target_dir: str, max_files: int = 100) -> CyberScanReport:
        """
        Performs a deep sovereign vulnerability audit across repository source files.
        """
        all_findings: List[VulnerabilityFinding] = []
        scanned_count = 0

        target_exts = {".py", ".ts", ".tsx", ".js", ".cpp", ".hpp", ".json", ".md"}

        for root, dirs, files in os.walk(target_dir):
            # Skip hidden, build, and node_modules
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "dist", "build", "target", "__pycache__")]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in target_exts:
                    scanned_count += 1
                    full_path = os.path.join(root, f)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                            rel_path = os.path.relpath(full_path, target_dir)
                            findings = self.scan_code_snippet(content, rel_path)
                            all_findings.extend(findings)
                    except Exception as e:
                        logger.warning(f"Error scanning {full_path}: {e}")

                    if scanned_count >= max_files:
                        break
            if scanned_count >= max_files:
                break

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in all_findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1

        # Compliance score: starts at 100, deducted per finding
        deductions = (
            (severity_counts["CRITICAL"] * 25.0) +
            (severity_counts["HIGH"] * 10.0) +
            (severity_counts["MEDIUM"] * 3.0) +
            (severity_counts["LOW"] * 1.0)
        )
        compliance_score = max(0.0, round(100.0 - deductions, 1))

        posture = (
            "SOVEREIGN_CERTIFIED" if compliance_score >= 90 
            else ("ACTION_REQUIRED" if compliance_score >= 70 else "VULNERABILITY_BREACH")
        )

        scan_id = f"SCAN-{int(time.time())}"

        return CyberScanReport(
            scan_id=scan_id,
            timestamp=time.time(),
            scanned_target=target_dir,
            files_scanned=scanned_count,
            findings_count=len(all_findings),
            severity_breakdown=severity_counts,
            findings=all_findings,
            compliance_score=compliance_score,
            sovereign_posture=posture
        )


cyberscan_agent = CyberScanAgent()
