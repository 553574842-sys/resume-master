"""Evidence manager for portfolio-style outputs."""

from __future__ import annotations

import re
from typing import Dict, List


def build_evidence_entries(project_lines: List[str]) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for line in project_lines:
        numbers = re.findall(r"\d+%?|\d+\+\s*万?", line)
        entry = {
            "title": line[:24],
            "data_achievement": "、".join(numbers) if numbers else "待补充可量化结果",
            "background": line,
        }
        entries.append(entry)
    return entries
