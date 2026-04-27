"""Authenticity validator with lightweight evidence-chain checks."""

from __future__ import annotations

import re
from typing import Dict, List


PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")
ABS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:万|w|k|千|人|次|单|个)")


def _extract_metrics(line: str) -> List[str]:
    metrics = [m.group(0) for m in PERCENT_PATTERN.finditer(line)]
    metrics.extend(m.group(0) for m in ABS_PATTERN.finditer(line))
    return metrics


def _suspicious_metric_warnings(line: str) -> List[str]:
    warnings: List[str] = []
    for match in PERCENT_PATTERN.finditer(line):
        try:
            value = float(match.group(1))
        except ValueError:
            continue
        if value >= 200:
            warnings.append(f"高增幅声明待核验: {match.group(0)} | {line}")
    if "100%" in line and ("提升" in line or "增长" in line):
        warnings.append(f"满额增长声明待核验: {line}")
    return warnings


def validate_authenticity(
    parsed_resume: Dict[str, object],
    generated_resume: Dict[str, object],
) -> Dict[str, object]:
    source_lines = (parsed_resume.get("work_experience", []) or []) + (parsed_resume.get("projects", []) or [])
    output_lines = (generated_resume.get("core", {}).get("work_experience", []) or []) + (
        generated_resume.get("auxiliary", {}).get("projects", []) or []
    )

    source_text = " ".join(source_lines)
    unsupported_claims: List[str] = []
    suspicious_metrics: List[str] = []
    missing_evidence_metrics: List[str] = []

    for line in output_lines:
        suspicious_metrics.extend(_suspicious_metric_warnings(line))
        if line not in source_text and ("提升" in line or "增长" in line or "降低" in line):
            unsupported_claims.append(f"可能缺少原文证据支撑: {line}")
        metrics = _extract_metrics(line)
        if metrics and line not in source_text:
            missing_evidence_metrics.append(f"数值指标未在原文找到直接证据: {line}")

    return {
        "risk_level": "high" if suspicious_metrics else ("medium" if unsupported_claims else "low"),
        "unsupported_claims": unsupported_claims[:5],
        "suspicious_metrics": suspicious_metrics[:5],
        "missing_evidence_metrics": missing_evidence_metrics[:5],
        "needs_manual_review": bool(suspicious_metrics or unsupported_claims or missing_evidence_metrics),
    }
