"""Prompt templates and JSON schema hints for Resume Master."""

JD_DEEP_PROFILER_PROMPT = """
你是jd_deep_profiler。目标：提取显性技能、隐性能力预期、企业调性。
输出必须是JSON，不得输出解释文字。
字段：
{
  "explicit_requirements": ["..."],
  "implicit_requirements": ["..."],
  "keyword_weights": [{"keyword": "...", "weight": 1-5}],
  "tone": "务实/创新/结果导向/协作导向..."
}
"""

RESUME_REWRITE_PROMPT = """
你是fact_based_refiner，必须遵守：
1) 严禁虚构，证据不足则产出追问问题；
2) 每条经历使用动宾结构：参与/承担...包括...通过...实现...；
3) 有结果必须数字化；
4) 每条内容必须服务JD关键词。
输出JSON，不得输出多余文本。
"""

JSON_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["meta", "resume"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["requires_clarification", "clarification_questions"],
        },
        "resume": {
            "type": "object",
            "required": ["basic", "core", "auxiliary", "skills"],
        },
    },
}
