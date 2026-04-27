"""Minimal HTTP API server for Resume Master frontend integration."""

from __future__ import annotations

import json
import base64
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from typing import Any, Dict

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from ai_adapter import maybe_enhance_with_ai
from authenticity_validator import validate_authenticity
from compressor import compress_resume_for_single_page
from jd_parser import parse_jd
from layout_validator import validate_bullet_line_limits, validate_layout
from resume_generator import generate_custom_resume
from resume_parser import parse_resume
from semantic_matcher import semantic_match_report
from text_extractor import extract_text_from_bytes, extract_text_from_image_bytes


DEFAULT_CONFIG: Dict[str, Any] = {
    "bullets": 10,
    "chars": 900,
    "lineChars": 38,
    "lineCount": 2,
    "moduleRatio": {"core": 0.55, "projects": 0.25, "skills": 0.20},
    "industry": "data_ai",
    "ai": {"enabled": False, "provider": "openai"},
}


def _normalize_format(value: Any) -> str:
    supported = {"json", "md", "html", "pdf"}
    fmt = str(value or "json").strip().lower()
    return fmt if fmt in supported else "json"


def _safe_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _skills_lines(skills: Dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for tier in ("精通", "熟悉", "掌握"):
        items = skills.get(tier, [])
        if items:
            lines.append(f"{tier}: {', '.join(items)}")
    return lines


def _resume_markdown(result: Dict[str, Any]) -> str:
    resume = result.get("resume", {})
    basic = resume.get("basic", {})
    core = resume.get("core", {})
    auxiliary = resume.get("auxiliary", {})
    skills = resume.get("skills", {})
    meta = result.get("meta", {})

    lines = [
        f"# {basic.get('name') or '候选人'}",
        "",
        f"- 目标岗位: {basic.get('target_role') or '未填写'}",
        f"- 手机: {basic.get('phone') or '未填写'}",
        f"- 邮箱: {basic.get('email') or '未填写'}",
        "",
        "## 核心经历",
    ]
    for item in core.get("work_experience", []):
        lines.append(f"- {item}")

    lines.extend(["", "## 项目经历"])
    for item in auxiliary.get("projects", []):
        lines.append(f"- {item}")

    education = auxiliary.get("education", [])
    if education:
        lines.extend(["", "## 教育背景"])
        for item in education:
            lines.append(f"- {item}")

    skill_lines = _skills_lines(skills)
    if skill_lines:
        lines.extend(["", "## 技能"])
        for item in skill_lines:
            lines.append(f"- {item}")

    clarifications = meta.get("clarification_questions", [])
    if clarifications:
        lines.extend(["", "## 待补充信息"])
        for question in clarifications:
            lines.append(f"- {question}")

    return "\n".join(lines) + "\n"


def _resume_html(result: Dict[str, Any]) -> str:
    resume = result.get("resume", {})
    basic = resume.get("basic", {})
    core = resume.get("core", {})
    auxiliary = resume.get("auxiliary", {})
    skills = resume.get("skills", {})
    meta = result.get("meta", {})

    def list_to_html(items: list[str]) -> str:
        if not items:
            return "<p>暂无内容</p>"
        return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"

    skill_lines = _skills_lines(skills)
    clarifications = meta.get("clarification_questions", [])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>定制简历</title>
  <style>
    body {{ font-family: "Microsoft YaHei", Arial, sans-serif; color: #1a1c20; margin: 32px; line-height: 1.7; }}
    h1 {{ margin: 0 0 8px; }}
    h2 {{ margin: 20px 0 8px; font-size: 18px; border-bottom: 1px solid #e2e4e8; padding-bottom: 4px; }}
    p {{ margin: 4px 0; }}
    ul {{ margin: 8px 0 0 18px; padding: 0; }}
    li {{ margin-bottom: 6px; }}
  </style>
</head>
<body>
  <h1>{escape(basic.get("name") or "候选人")}</h1>
  <p><strong>目标岗位:</strong> {escape(basic.get("target_role") or "未填写")}</p>
  <p><strong>手机:</strong> {escape(basic.get("phone") or "未填写")}</p>
  <p><strong>邮箱:</strong> {escape(basic.get("email") or "未填写")}</p>

  <h2>核心经历</h2>
  {list_to_html(core.get("work_experience", []))}

  <h2>项目经历</h2>
  {list_to_html(auxiliary.get("projects", []))}

  <h2>教育背景</h2>
  {list_to_html(auxiliary.get("education", []))}

  <h2>技能</h2>
  {list_to_html(skill_lines)}

  <h2>待补充信息</h2>
  {list_to_html(clarifications)}
</body>
</html>
"""


def _wrap_text_for_pdf(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def _resume_pdf_bytes(result: Dict[str, Any]) -> bytes:
    resume = result.get("resume", {})
    basic = resume.get("basic", {})
    core = resume.get("core", {})
    auxiliary = resume.get("auxiliary", {})
    skills = resume.get("skills", {})
    meta = result.get("meta", {})

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    left = 48
    y = height - 48
    line_height = 18
    max_text_width = width - left * 2
    font_name = "STSong-Light"

    def add_line(text: str, size: int = 12) -> None:
        nonlocal y
        wrapped = _wrap_text_for_pdf(text, font_name, size, max_text_width)
        pdf.setFont(font_name, size)
        for part in wrapped:
            if y <= 50:
                pdf.showPage()
                y = height - 48
                pdf.setFont(font_name, size)
            pdf.drawString(left, y, part)
            y -= line_height

    def add_section(title: str, items: list[str]) -> None:
        add_line(title, size=13)
        if items:
            for item in items:
                add_line(f"- {item}")
        else:
            add_line("- 暂无内容")
        add_line("")

    add_line(basic.get("name") or "候选人", size=16)
    add_line(f"目标岗位: {basic.get('target_role') or '未填写'}")
    add_line(f"手机: {basic.get('phone') or '未填写'}")
    add_line(f"邮箱: {basic.get('email') or '未填写'}")
    add_line("")
    add_section("核心经历", core.get("work_experience", []))
    add_section("项目经历", auxiliary.get("projects", []))
    add_section("教育背景", auxiliary.get("education", []))
    add_section("技能", _skills_lines(skills))
    add_section("待补充信息", meta.get("clarification_questions", []))

    pdf.save()
    return buf.getvalue()


def build_custom_resume(jd_text: str, resume_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    merged_config = {
        **DEFAULT_CONFIG,
        **(config or {}),
    }
    module_ratio = merged_config.get("moduleRatio") or DEFAULT_CONFIG["moduleRatio"]

    parsed_jd = parse_jd(jd_text)
    parsed_resume = parse_resume(resume_text)
    result = generate_custom_resume(parsed_jd, parsed_resume)
    result, ai_warnings = maybe_enhance_with_ai(
        result,
        parsed_jd=parsed_jd,
        parsed_resume=parsed_resume,
        config=merged_config,
    )
    jd_keywords = [item["keyword"] for item in parsed_jd.get("keyword_weights", [])]

    compressed_resume, compress_warnings, budget_report = compress_resume_for_single_page(
        result["resume"],
        jd_keywords=jd_keywords,
        max_chars_per_line=_safe_int(merged_config.get("lineChars"), 38),
        max_lines_per_bullet=_safe_int(merged_config.get("lineCount"), 2),
        total_bullets_budget=_safe_int(merged_config.get("bullets"), 10),
        total_chars_budget=_safe_int(merged_config.get("chars"), 900),
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
        max_chars_per_line=_safe_int(merged_config.get("lineChars"), 38),
        max_lines_per_bullet=_safe_int(merged_config.get("lineCount"), 2),
    )
    result["meta"]["line_limit_valid"] = line_limit_valid
    result["meta"]["line_limit_violations"] = line_limit_violations
    industry = str(merged_config.get("industry") or "data_ai")
    result["meta"]["semantic_match"] = semantic_match_report(parsed_jd, parsed_resume, industry=industry)
    result["meta"]["authenticity_check"] = validate_authenticity(parsed_resume, result["resume"])
    result["meta"]["ai"] = {
        "enabled": bool((merged_config.get("ai") or {}).get("enabled", False)),
        "provider": str((merged_config.get("ai") or {}).get("provider", "openai")),
        "warnings": ai_warnings,
    }
    return result


class ResumeAPIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code: int = 200, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _write_json(self, payload: Dict[str, Any], status_code: int = 200) -> None:
        self._set_headers(status_code)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _write_bytes(self, payload: bytes, content_type: str, status_code: int = 200) -> None:
        self._set_headers(status_code, content_type=content_type)
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._set_headers(204)

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/api/generate", "/api/extract-inputs"}:
            self._write_json({"error": "Not Found"}, 404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._write_json({"error": "Invalid JSON body"}, 400)
            return

        if self.path == "/api/extract-inputs":
            self._handle_extract_inputs(data)
            return

        jd_text = (data.get("jd_text") or "").strip()
        resume_text = (data.get("resume_text") or "").strip()
        config = data.get("config") or {}
        export_format = _normalize_format(data.get("format"))

        if not jd_text or not resume_text:
            self._write_json({"error": "jd_text and resume_text are required"}, 400)
            return

        try:
            result = build_custom_resume(jd_text, resume_text, config)
            if export_format == "json":
                self._write_json(result, 200)
            elif export_format == "md":
                self._write_bytes(
                    _resume_markdown(result).encode("utf-8"),
                    "text/markdown; charset=utf-8",
                    200,
                )
            elif export_format == "html":
                self._write_bytes(
                    _resume_html(result).encode("utf-8"),
                    "text/html; charset=utf-8",
                    200,
                )
            else:
                self._write_bytes(
                    _resume_pdf_bytes(result),
                    "application/pdf",
                    200,
                )
        except Exception as exc:  # noqa: BLE001
            self._write_json({"error": "Generation failed", "detail": str(exc)}, 500)

    def _handle_extract_inputs(self, data: Dict[str, Any]) -> None:
        jd_image_base64 = data.get("jd_image_base64") or ""
        resume_file_base64 = data.get("resume_file_base64") or ""
        resume_file_name = data.get("resume_file_name") or "resume.txt"
        result = {
            "jd_text": "",
            "resume_text": "",
            "warnings": [],
        }

        try:
            if jd_image_base64:
                image_bytes = base64.b64decode(jd_image_base64)
                result["jd_text"] = extract_text_from_image_bytes(image_bytes)
            if resume_file_base64:
                file_bytes = base64.b64decode(resume_file_base64)
                result["resume_text"] = extract_text_from_bytes(resume_file_name, file_bytes)
        except Exception as exc:  # noqa: BLE001
            self._write_json({"error": "Extract failed", "detail": str(exc)}, 500)
            return

        if not result["jd_text"] and jd_image_base64:
            result["warnings"].append("未从JD截图识别到有效文本，请尝试更清晰截图。")
        if not result["resume_text"] and resume_file_base64:
            result["warnings"].append("未从简历文件提取到有效文本，请检查文件格式。")
        self._write_json(result, 200)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ResumeAPIHandler)
    print("Resume API running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
