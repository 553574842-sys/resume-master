"""JD parser + jd_deep_profiler."""

from __future__ import annotations

import re
from typing import Dict, List


SKILL_KEYWORDS = [
    "python",
    "sql",
    "机器学习",
    "深度学习",
    "nlp",
    "llm",
    "fastapi",
    "flask",
    "django",
    "数据分析",
    "项目管理",
    "沟通",
]


def _extract_year_expectations(jd_text: str) -> List[str]:
    years = re.findall(r"(\d+)\s*年", jd_text)
    if not years:
        return []
    return [f"{y}年以上相关经验" for y in sorted(set(years))]


def parse_jd(jd_text: str) -> Dict[str, object]:
    lowered = jd_text.lower()
    explicit = [k for k in SKILL_KEYWORDS if k in lowered or k in jd_text]
    explicit = sorted(set(explicit))

    implicit = _extract_year_expectations(jd_text)
    if "跨部门" in jd_text or "协同" in jd_text:
        implicit.append("跨团队协作能力")
    if "独立" in jd_text or "owner" in lowered:
        implicit.append("独立推进与结果闭环能力")
    if "高压" in jd_text or "快节奏" in jd_text:
        implicit.append("高压环境执行能力")

    tone = "结果导向"
    if "创新" in jd_text:
        tone = "创新导向"
    elif "规范" in jd_text or "流程" in jd_text:
        tone = "规范导向"
    elif "协作" in jd_text:
        tone = "协作导向"

    keyword_weights = [{"keyword": k, "weight": 5} for k in explicit]
    return {
        "explicit_requirements": explicit,
        "implicit_requirements": sorted(set(implicit)),
        "keyword_weights": keyword_weights,
        "tone": tone,
    }
