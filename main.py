"""CLI entry for Resume Master tool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_adapter import maybe_enhance_with_ai
from authenticity_validator import validate_authenticity
from compressor import compress_resume_for_single_page
from jd_parser import parse_jd
from layout_validator import validate_bullet_line_limits, validate_layout
from resume_generator import generate_custom_resume
from resume_parser import parse_resume
from semantic_matcher import semantic_match_report
from text_extractor import extract_text


def run(
    jd_path: Path,
    resume_path: Path,
    out_path: Path,
    max_chars_per_line: int,
    max_lines_per_bullet: int,
    total_bullets_budget: int,
    total_chars_budget: int,
    module_ratio: dict[str, float],
    industry: str,
    ai_enabled: bool,
    ai_provider: str,
) -> int:
    jd_text = extract_text(jd_path)
    resume_text = extract_text(resume_path)

    parsed_jd = parse_jd(jd_text)
    parsed_resume = parse_resume(resume_text)
    result = generate_custom_resume(parsed_jd, parsed_resume)
    ai_cfg = {"ai": {"enabled": ai_enabled, "provider": ai_provider}}
    result, ai_warnings = maybe_enhance_with_ai(result, parsed_jd, parsed_resume, ai_cfg)
    jd_keywords = [item["keyword"] for item in parsed_jd.get("keyword_weights", [])]

    compressed_resume, compress_warnings, budget_report = compress_resume_for_single_page(
        result["resume"],
        jd_keywords=jd_keywords,
        max_chars_per_line=max_chars_per_line,
        max_lines_per_bullet=max_lines_per_bullet,
        total_bullets_budget=total_bullets_budget,
        total_chars_budget=total_chars_budget,
        module_ratio=module_ratio,
    )
    result["resume"] = compressed_resume

    is_valid, warnings = validate_layout(result["resume"])
    result["meta"]["layout_valid"] = is_valid
    result["meta"]["layout_warnings"] = warnings
    result["meta"]["compression_warnings"] = compress_warnings
    result["meta"]["page_budget"] = budget_report

    line_limit_valid, line_limit_violations = validate_bullet_line_limits(
        result["resume"],
        max_chars_per_line=max_chars_per_line,
        max_lines_per_bullet=max_lines_per_bullet,
    )
    result["meta"]["line_limit_valid"] = line_limit_valid
    result["meta"]["line_limit_violations"] = line_limit_violations
    result["meta"]["semantic_match"] = semantic_match_report(parsed_jd, parsed_resume, industry=industry)
    result["meta"]["authenticity_check"] = validate_authenticity(parsed_resume, result["resume"])
    result["meta"]["ai"] = {
        "enabled": ai_enabled,
        "provider": ai_provider,
        "warnings": ai_warnings,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成: {out_path}")
    if result["meta"]["requires_clarification"]:
        print("存在待追问信息，请先补充后再投递。")
    if not line_limit_valid:
        print("存在超出2行长度的条目，已在输出meta中标注。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="简历大师 CLI")
    parser.add_argument("--jd", required=True, help="JD文本文件路径")
    parser.add_argument("--resume", required=True, help="原始简历文件路径（txt/md/docx/pdf）")
    parser.add_argument(
        "--out",
        default="output/customized_resume.json",
        help="输出JSON文件路径",
    )
    parser.add_argument(
        "--max-chars-per-line",
        type=int,
        default=38,
        help="每行字符预算，用于2行硬校验与压缩。",
    )
    parser.add_argument(
        "--max-lines-per-bullet",
        type=int,
        default=2,
        help="每条最大行数，默认2行。",
    )
    parser.add_argument(
        "--total-bullets-budget",
        type=int,
        default=10,
        help="整页总条数预算（核心+项目）。",
    )
    parser.add_argument(
        "--total-chars-budget",
        type=int,
        default=900,
        help="整页总字符预算（核心+项目+技能）。",
    )
    parser.add_argument(
        "--module-ratio",
        default="core=0.55,projects=0.25,skills=0.20",
        help="模块占比，格式: core=0.55,projects=0.25,skills=0.20",
    )
    parser.add_argument(
        "--industry",
        default="data_ai",
        help="行业词库类型（如 data_ai/backend/product_ops）。",
    )
    parser.add_argument(
        "--ai-enabled",
        action="store_true",
        help="是否开启可选AI模式（未配置Key会自动回退规则模式）。",
    )
    parser.add_argument(
        "--ai-provider",
        default="openai",
        help="AI提供方标识（openai/anthropic），用于读取对应环境变量。",
    )
    args = parser.parse_args()

    ratio = {}
    for part in args.module_ratio.split(","):
        key, value = part.split("=", 1)
        ratio[key.strip()] = float(value.strip())

    return run(
        Path(args.jd),
        Path(args.resume),
        Path(args.out),
        args.max_chars_per_line,
        args.max_lines_per_bullet,
        args.total_bullets_budget,
        args.total_chars_budget,
        ratio,
        args.industry,
        args.ai_enabled,
        args.ai_provider,
    )


if __name__ == "__main__":
    raise SystemExit(main())
