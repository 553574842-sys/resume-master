"""Industry lexicon and semantic matching helpers (lightweight skeleton)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Dict, List


INDUSTRY_LEXICON: Dict[str, Dict[str, List[str]]] = {
    "data_ai": {
        "python": ["python", "py"],
        "sql": ["sql", "mysql", "postgresql"],
        "machine_learning": ["机器学习", "ml", "建模"],
        "llm": ["llm", "大模型", "prompt", "rag"],
        "data_analysis": ["数据分析", "指标体系", "ab测试"],
    },
    "backend": {
        "api_design": ["api", "接口设计", "restful"],
        "service_governance": ["服务治理", "熔断", "限流"],
        "database": ["数据库", "mysql", "redis"],
        "observability": ["监控", "告警", "可观测性"],
    },
    "product_ops": {
        "growth": ["增长", "转化率", "留存"],
        "funnel": ["漏斗", "路径分析", "埋点"],
        "campaign": ["活动策划", "campaign", "运营"],
    },
}


def _tokenize(text: str) -> List[str]:
    return [tok for tok in re.split(r"[\s,，。；;：:、\n]+", text.lower()) if tok]


def _collect_semantic_terms(jd_keywords: List[str], industry: str) -> List[str]:
    lexicon = INDUSTRY_LEXICON.get(industry, {})
    terms = set(jd_keywords)
    for kw in jd_keywords:
        lowered = kw.lower()
        for canonical, aliases in lexicon.items():
            if lowered == canonical or lowered in aliases or kw in aliases:
                terms.add(canonical)
                terms.update(aliases)
    return sorted(terms)


def _fuzzy_overlap_score(text: str, semantic_terms: List[str]) -> float:
    tokens = _tokenize(text)
    if not tokens or not semantic_terms:
        return 0.0
    max_score = 0.0
    for token in tokens:
        for term in semantic_terms:
            ratio = SequenceMatcher(None, token, term.lower()).ratio()
            if ratio > max_score:
                max_score = ratio
    return max_score


def semantic_match_report(
    parsed_jd: Dict[str, object],
    parsed_resume: Dict[str, object],
    industry: str = "data_ai",
) -> Dict[str, object]:
    jd_keywords = [item["keyword"] for item in parsed_jd.get("keyword_weights", [])]
    semantic_terms = _collect_semantic_terms(jd_keywords, industry)
    lines = (parsed_resume.get("work_experience", []) or []) + (parsed_resume.get("projects", []) or [])

    line_scores = []
    for line in lines:
        direct_hits = [kw for kw in jd_keywords if kw.lower() in line.lower() or kw in line]
        fuzzy_score = _fuzzy_overlap_score(line, semantic_terms)
        line_scores.append(
            {
                "line": line,
                "direct_hits": direct_hits,
                "semantic_score": round(fuzzy_score, 3),
            }
        )

    high_alignment = [item for item in line_scores if item["semantic_score"] >= 0.8 or item["direct_hits"]]
    low_alignment = [item for item in line_scores if item["semantic_score"] < 0.45 and not item["direct_hits"]]
    return {
        "industry": industry,
        "semantic_terms_count": len(semantic_terms),
        "semantic_terms_preview": semantic_terms[:20],
        "high_alignment_count": len(high_alignment),
        "low_alignment_count": len(low_alignment),
        "low_alignment_samples": [item["line"] for item in low_alignment[:3]],
    }
