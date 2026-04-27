"""Generate customized resume from parsed JD and parsed resume."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from evidence_manager import build_evidence_entries
from layout_validator import normalize_official_names


ACTION_VERBS = ("参与", "承担", "主导", "推进", "协调", "搭建", "优化", "设计", "实现")


def _contains_number(text: str) -> bool:
    return bool(re.search(r"\d", text))


def _match_score(line: str, keywords: List[str]) -> int:
    lowered = line.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in lowered or kw in line:
            score += 1
    return score


def _format_action_object(line: str) -> str:
    if any(line.startswith(v) for v in ACTION_VERBS):
        return line
    return f"参与业务推进，包括{line}"


def _refine_line(line: str, clarification_questions: List[str]) -> str:
    refined = _format_action_object(line)
    if "通过" not in refined:
        refined += "，通过关键路径拆解实现目标交付"
    if "实现" not in refined:
        refined += "，实现阶段性成果"
    if not _contains_number(refined):
        clarification_questions.append(f"请补充可量化结果：{line}")
        refined += "（结果量化待补充）"
    return refined


def experience_classifier(work_lines: List[str], jd_keywords: List[str]) -> Dict[str, List[str]]:
    scored: List[Tuple[int, str]] = [(_match_score(line, jd_keywords), line) for line in work_lines]
    scored.sort(key=lambda x: x[0], reverse=True)

    direct = [line for score, line in scored if score >= 2]
    indirect = [line for score, line in scored if 0 < score < 2]
    standard = [line for score, line in scored if score == 0]
    return {
        "direct_experience": direct,
        "indirect_experience": indirect,
        "standard_capability": standard,
    }


def skill_tier_assessor(skill_lines: List[str], evidence_pool: List[str]) -> Dict[str, List[str]]:
    tiers = {"掌握": [], "熟悉": [], "精通": []}
    evidence_text = " ".join(evidence_pool)
    for item in skill_lines:
        normalized = item.strip("•- ").strip()
        if not normalized:
            continue
        if normalized in evidence_text and re.search(r"\d", evidence_text):
            tiers["熟悉"].append(normalized)
        else:
            tiers["掌握"].append(normalized)

    # 精通必须有明确证据，默认不自动标记精通。
    return tiers


def generate_custom_resume(parsed_jd: Dict[str, object], parsed_resume: Dict[str, object]) -> Dict[str, object]:
    clarification_questions: List[str] = []
    basic = parsed_resume["basic"]
    if not basic.get("name"):
        clarification_questions.append("请补充姓名。")
    if not basic.get("phone"):
        clarification_questions.append("请补充手机号。")
    if not basic.get("target_role"):
        clarification_questions.append("请补充求职意向岗位名称。")

    jd_keywords = [item["keyword"] for item in parsed_jd.get("keyword_weights", [])]
    classified = experience_classifier(parsed_resume["work_experience"], jd_keywords)

    core_lines = []
    for line in classified["direct_experience"] + classified["indirect_experience"]:
        refined = _refine_line(line, clarification_questions)
        core_lines.append(refined)

    auxiliary_projects = [
        _refine_line(line, clarification_questions) for line in parsed_resume["projects"]
    ]
    evidence = build_evidence_entries(parsed_resume["projects"])

    skills = skill_tier_assessor(
        parsed_resume["skills"],
        parsed_resume["work_experience"] + parsed_resume["projects"],
    )

    education_lines = [normalize_official_names(line) for line in parsed_resume["education"]]

    return {
        "meta": {
            "requires_clarification": len(clarification_questions) > 0,
            "clarification_questions": clarification_questions,
            "jd_tone": parsed_jd.get("tone", ""),
        },
        "resume": {
            "basic": {
                "name": basic.get("name", ""),
                "phone": basic.get("phone", ""),
                "email": basic.get("email", ""),
                "target_role": basic.get("target_role", ""),
            },
            "core": {
                "work_experience": core_lines[:8],
                "ordering_rule": "直接经历 > 间接经历 > 标准能力",
            },
            "auxiliary": {
                "projects": auxiliary_projects[:4],
                "education": education_lines[:2],
                "evidence": evidence[:3],
            },
            "skills": skills,
        },
    }
