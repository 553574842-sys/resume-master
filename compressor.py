"""Single-page compressor with overall page-budget enforcement."""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Tuple


def _line_score(line: str, jd_keywords: List[str]) -> int:
    score = 0
    lowered = line.lower()
    for kw in jd_keywords:
        if kw.lower() in lowered or kw in line:
            score += 2
    if re.search(r"\d", line):
        score += 1
    if "结果量化待补充" in line:
        score -= 1
    return score


def _truncate_by_char_budget(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip("，。； ") + "…"


def _calc_section_chars(lines: List[str]) -> int:
    return sum(len(line) for line in lines)


def _keep_top_by_score(lines: List[str], jd_keywords: List[str], keep_n: int) -> Tuple[List[str], int]:
    if keep_n < 0:
        keep_n = 0
    scored = sorted(lines, key=lambda ln: _line_score(ln, jd_keywords), reverse=True)
    kept = scored[:keep_n]
    return kept, max(0, len(scored) - len(kept))


def _trim_section_chars(
    lines: List[str],
    section_budget_chars: int,
    max_chars_per_bullet: int,
) -> Tuple[List[str], int]:
    trimmed: List[str] = []
    current = 0
    dropped = 0
    for line in lines:
        normalized = _truncate_by_char_budget(line, max_chars_per_bullet)
        if current + len(normalized) <= section_budget_chars:
            trimmed.append(normalized)
            current += len(normalized)
        else:
            dropped += 1
    return trimmed, dropped


def compress_resume_for_single_page(
    resume: Dict[str, object],
    jd_keywords: List[str],
    max_core_bullets: int = 5,
    max_project_bullets: int = 3,
    max_chars_per_line: int = 38,
    max_lines_per_bullet: int = 2,
    total_bullets_budget: int = 10,
    total_chars_budget: int = 900,
    module_ratio: Dict[str, float] | None = None,
) -> Tuple[Dict[str, object], List[str], Dict[str, Any]]:
    warnings: List[str] = []
    max_chars_per_bullet = max_chars_per_line * max_lines_per_bullet
    ratio = module_ratio or {"core": 0.55, "projects": 0.25, "skills": 0.20}
    ratio_sum = sum(ratio.values())
    if ratio_sum <= 0:
        ratio = {"core": 0.55, "projects": 0.25, "skills": 0.20}
        ratio_sum = 1.0
    ratio = {k: v / ratio_sum for k, v in ratio.items()}

    core = resume.get("core", {})
    auxiliary = resume.get("auxiliary", {})
    skills = resume.get("skills", {})

    raw_core_lines = core.get("work_experience", [])
    raw_project_lines = auxiliary.get("projects", [])

    core_budget_count = min(max_core_bullets, math.floor(total_bullets_budget * ratio.get("core", 0)))
    project_budget_count = min(
        max_project_bullets,
        math.floor(total_bullets_budget * ratio.get("projects", 0)),
    )
    if raw_core_lines and core_budget_count == 0:
        core_budget_count = 1
    if raw_project_lines and project_budget_count == 0:
        project_budget_count = 1

    kept_core, dropped_core = _keep_top_by_score(raw_core_lines, jd_keywords, core_budget_count)
    if dropped_core:
        warnings.append(f"核心经历已按预算裁剪{dropped_core}条。")
    kept_projects, dropped_projects = _keep_top_by_score(
        raw_project_lines, jd_keywords, project_budget_count
    )
    if dropped_projects:
        warnings.append(f"项目经历已按预算裁剪{dropped_projects}条。")

    core_char_budget = math.floor(total_chars_budget * ratio.get("core", 0))
    project_char_budget = math.floor(total_chars_budget * ratio.get("projects", 0))
    skills_char_budget = total_chars_budget - core_char_budget - project_char_budget
    if skills_char_budget < 0:
        skills_char_budget = 0

    core_lines, dropped_core_by_chars = _trim_section_chars(
        kept_core, core_char_budget, max_chars_per_bullet
    )
    if dropped_core_by_chars:
        warnings.append(f"核心经历因字符预算再裁剪{dropped_core_by_chars}条。")

    project_lines, dropped_project_by_chars = _trim_section_chars(
        kept_projects, project_char_budget, max_chars_per_bullet
    )
    if dropped_project_by_chars:
        warnings.append(f"项目经历因字符预算再裁剪{dropped_project_by_chars}条。")

    core["work_experience"] = core_lines
    auxiliary["projects"] = project_lines

    evidence = auxiliary.get("evidence", [])
    auxiliary["evidence"] = evidence[:2]

    for tier in ("掌握", "熟悉", "精通"):
        if tier in skills:
            trimmed_tier = []
            current_chars = 0
            for item in skills[tier]:
                if current_chars + len(item) <= skills_char_budget:
                    trimmed_tier.append(item)
                    current_chars += len(item)
            if len(trimmed_tier) < len(skills[tier]):
                warnings.append(f"技能区{tier}已按字符预算裁剪{len(skills[tier]) - len(trimmed_tier)}项。")
            skills[tier] = trimmed_tier

    resume["core"] = core
    resume["auxiliary"] = auxiliary
    resume["skills"] = skills

    final_core_lines = resume.get("core", {}).get("work_experience", [])
    final_project_lines = resume.get("auxiliary", {}).get("projects", [])
    final_bullet_count = len(final_core_lines) + len(final_project_lines)
    final_char_count = (
        _calc_section_chars(final_core_lines)
        + _calc_section_chars(final_project_lines)
        + _calc_section_chars(resume.get("skills", {}).get("掌握", []))
        + _calc_section_chars(resume.get("skills", {}).get("熟悉", []))
        + _calc_section_chars(resume.get("skills", {}).get("精通", []))
    )
    budget_report = {
        "budgets": {
            "total_bullets_budget": total_bullets_budget,
            "total_chars_budget": total_chars_budget,
            "module_ratio": ratio,
            "per_section_char_budget": {
                "core": core_char_budget,
                "projects": project_char_budget,
                "skills": skills_char_budget,
            },
        },
        "final_usage": {
            "bullets": final_bullet_count,
            "chars": final_char_count,
            "core_chars": _calc_section_chars(final_core_lines),
            "project_chars": _calc_section_chars(final_project_lines),
        },
    }
    return resume, warnings, budget_report
