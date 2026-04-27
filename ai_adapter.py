"""Optional AI enhancer adapter (skeleton only)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

from llm_client import get_llm_settings

def ai_is_enabled(config: Dict[str, Any] | None) -> bool:
    cfg = config or {}
    ai_cfg = cfg.get("ai") or {}
    return bool(ai_cfg.get("enabled", False))


def ai_provider(config: Dict[str, Any] | None) -> str:
    cfg = config or {}
    ai_cfg = cfg.get("ai") or {}
    provider = str(ai_cfg.get("provider", "openai")).strip().lower()
    return provider or "openai"


def ai_key_exists(provider: str) -> bool:
    llm_key = get_llm_settings().get("api_key", "")
    if llm_key:
        return True
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider == "anthropic":
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    return False


def maybe_enhance_with_ai(
    result: Dict[str, Any],
    parsed_jd: Dict[str, Any],
    parsed_resume: Dict[str, Any],
    config: Dict[str, Any] | None,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Skeleton for future AI refinement.

    Current behavior:
    - AI disabled: no-op
    - AI enabled but no key: no-op with warning
    - AI enabled + key: still no-op with placeholder warning
    """
    warnings: List[str] = []
    if not ai_is_enabled(config):
        return result, warnings

    provider = ai_provider(config)
    if not ai_key_exists(provider):
        warnings.append(f"AI模式已开启，但未检测到{provider} API Key，已回退规则模式。")
        return result, warnings

    # Placeholder for model call: pipeline is now cloud-model ready.
    _ = parsed_jd, parsed_resume
    warnings.append("AI增强模式已连通云端模型配置（当前改写逻辑仍为规则主导）。")
    return result, warnings
