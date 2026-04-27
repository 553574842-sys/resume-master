"""Minimal OpenAI-compatible HTTP client for text/vision tasks."""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from typing import Any, Dict


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default)).strip()


def get_llm_settings() -> Dict[str, str]:
    return {
        "api_base": _env("LLM_API_BASE", "https://api.openai.com/v1"),
        "api_key": _env("LLM_API_KEY", _env("OPENAI_API_KEY")),
        "text_model": _env("LLM_TEXT_MODEL", "gpt-4.1-mini"),
        "vision_model": _env("LLM_VISION_MODEL", "gpt-4.1-mini"),
    }


def has_llm_key() -> bool:
    return bool(get_llm_settings()["api_key"])


def _post_json(url: str, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:  # noqa: S310
        content = resp.read().decode("utf-8")
    return json.loads(content)


def chat_text(system_prompt: str, user_prompt: str) -> str:
    cfg = get_llm_settings()
    if not cfg["api_key"]:
        raise RuntimeError("未检测到 LLM_API_KEY 或 OPENAI_API_KEY。")
    payload = {
        "model": cfg["text_model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    data = _post_json(f"{cfg['api_base']}/chat/completions", cfg["api_key"], payload)
    return data["choices"][0]["message"]["content"].strip()


def vision_ocr(image_bytes: bytes) -> str:
    cfg = get_llm_settings()
    if not cfg["api_key"]:
        raise RuntimeError("未检测到 LLM_API_KEY 或 OPENAI_API_KEY。")
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": cfg["vision_model"],
        "messages": [
            {
                "role": "system",
                "content": "你是OCR助手。请提取图片中的文字，仅输出纯文本，不要解释。",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请提取这张JD截图的完整文本。"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            },
        ],
        "temperature": 0,
    }
    data = _post_json(f"{cfg['api_base']}/chat/completions", cfg["api_key"], payload)
    return data["choices"][0]["message"]["content"].strip()
