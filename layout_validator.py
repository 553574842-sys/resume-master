"""Validate 1234 layout, official names, and bullet length limits."""

from __future__ import annotations

from typing import Dict, List, Tuple


OFFICIAL_NAME_MAP = {
    "北邮": "北京邮电大学",
    "北大": "北京大学",
    "清华": "清华大学",
    "人大": "中国人民大学",
}


def normalize_official_names(text: str) -> str:
    normalized = text
    for short, full in OFFICIAL_NAME_MAP.items():
        normalized = normalized.replace(short, full)
    return normalized


def validate_layout(resume_obj: Dict[str, object]) -> Tuple[bool, List[str]]:
    warnings: List[str] = []
    required = ["basic", "core", "auxiliary", "skills"]
    for key in required:
        if key not in resume_obj:
            warnings.append(f"缺少区块: {key}")
    is_valid = not warnings
    return is_valid, warnings


def validate_bullet_line_limits(
    resume_obj: Dict[str, object],
    max_chars_per_line: int = 38,
    max_lines_per_bullet: int = 2,
) -> Tuple[bool, List[str]]:
    violations: List[str] = []
    max_chars_per_bullet = max_chars_per_line * max_lines_per_bullet

    checks = [
        ("core.work_experience", resume_obj.get("core", {}).get("work_experience", [])),
        ("auxiliary.projects", resume_obj.get("auxiliary", {}).get("projects", [])),
    ]
    for section_name, lines in checks:
        for idx, line in enumerate(lines, start=1):
            if len(line) > max_chars_per_bullet:
                violations.append(
                    f"{section_name} 第{idx}条超长（{len(line)}>{max_chars_per_bullet}字符）"
                )

    return len(violations) == 0, violations
