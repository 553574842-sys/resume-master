"""Resume parser for plain text resume input."""

from __future__ import annotations

import re
from typing import Dict, List


SECTION_MAP = {
    "工作经历": "work_experience",
    "项目经历": "projects",
    "教育背景": "education",
    "技能": "skills",
    "个人信息": "basic",
}


def _parse_basic_info(text: str) -> Dict[str, str]:
    data = {"name": "", "phone": "", "email": "", "target_role": ""}
    phone = re.search(r"(1[3-9]\d{9})", text)
    email = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
    if phone:
        data["phone"] = phone.group(1)
    if email:
        data["email"] = email.group(1)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        data["name"] = lines[0].lstrip("\ufeff")
    role_match = re.search(r"(求职意向|目标岗位)[:：]\s*(.+)", text)
    if role_match:
        data["target_role"] = role_match.group(2).strip()
    return data


def parse_resume(resume_text: str) -> Dict[str, object]:
    sections: Dict[str, List[str]] = {v: [] for v in SECTION_MAP.values()}
    current = None
    for raw in resume_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in SECTION_MAP:
            current = SECTION_MAP[line]
            continue
        if current:
            sections[current].append(line)

    return {
        "basic": _parse_basic_info(resume_text),
        "work_experience": sections["work_experience"],
        "projects": sections["projects"],
        "education": sections["education"],
        "skills": sections["skills"],
    }
