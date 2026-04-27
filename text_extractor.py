"""Unified text extraction for txt/md/docx/pdf inputs."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET

from llm_client import has_llm_key, vision_ocr


def _read_plain_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as zf:
        xml_bytes = zf.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for p in root.findall(".//w:p", ns):
        texts = [node.text or "" for node in p.findall(".//w:t", ns)]
        if texts:
            paragraphs.append("".join(texts).strip())
    return "\n".join([p for p in paragraphs if p])


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "解析PDF需要安装pypdf: pip install pypdf"
        ) from exc

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return _read_plain_text(path)
    if ext == ".docx":
        return _read_docx_text(path)
    if ext == ".pdf":
        return _read_pdf_text(path)
    raise ValueError(f"暂不支持的文件类型: {ext}")


def extract_text_from_bytes(file_name: str, file_bytes: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        return extract_text(Path(tmp.name))


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    if not has_llm_key():
        raise RuntimeError("未配置云端大模型API Key，无法进行截图OCR。")
    text = vision_ocr(image_bytes)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
