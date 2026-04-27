/**
 * 简历大师 — 前端交互逻辑
 * 功能：采集 JD + 简历文本，构建预览 payload，复制输出
 */

// ---------- 常量（消除 magic number） ----------
const MAX_KEYWORDS = 15;
const MIN_KEYWORD_LEN = 2;
const DEFAULT_BUDGET = {
  bullets: 10,
  chars: 900,
  lineChars: 38,
  lineCount: 2,
};
const MODULE_RATIO = { core: 0.55, projects: 0.25, skills: 0.2 };
const DEFAULT_INDUSTRY = "data_ai";
const DEFAULT_AI_CONFIG = { enabled: false, provider: "openai" };
const API_URL = "http://127.0.0.1:8000/api/generate";
const EXTRACT_API_URL = "http://127.0.0.1:8000/api/extract-inputs";
const MIME_MAP = {
  json: "application/json;charset=utf-8",
  md: "text/markdown;charset=utf-8",
  html: "text/html;charset=utf-8",
  pdf: "application/pdf",
};
const EXT_MAP = { json: "json", md: "md", html: "html", pdf: "pdf" };

let latestOutput = {
  format: "json",
  text: "",
  blob: null,
};

// ---------- 工具函数 ----------
function el(id) {
  return document.getElementById(id);
}

function parseNum(value, fallback) {
  const n = parseInt(value, 10);
  return isNaN(n) ? fallback : n;
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const base64 = result.includes(",") ? result.split(",")[1] : result;
      resolve(base64);
    };
    reader.onerror = () => reject(new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}

async function extractInputs({ jdImageFile = null, resumeFile = null }) {
  const payload = {};
  if (jdImageFile) {
    payload.jd_image_base64 = await fileToBase64(jdImageFile);
  }
  if (resumeFile) {
    payload.resume_file_base64 = await fileToBase64(resumeFile);
    payload.resume_file_name = resumeFile.name || "resume.txt";
  }
  if (!payload.jd_image_base64 && !payload.resume_file_base64) {
    return;
  }

  setStatus("识别中", "generating");
  const resp = await fetch(EXTRACT_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.error || "提取失败");
  }

  if (data.jd_text) {
    el("jdText").value = data.jd_text;
  }
  if (data.resume_text) {
    el("resumeText").value = data.resume_text;
  }
  setStatus("已识别", "done");
}

function setZoneActive(zone, active) {
  zone.classList.toggle("is-active", Boolean(active));
}

function bindResumeDropZone() {
  const zone = el("resumeDropZone");
  const fileInput = el("resumeFileInput");
  const pickBtn = el("pickResumeBtn");

  const onFile = async (file) => {
    if (!file) return;
    try {
      await extractInputs({ resumeFile: file });
    } catch (err) {
      setStatus("简历导入失败", "needs-input");
    }
  };

  zone.addEventListener("dragover", (evt) => {
    evt.preventDefault();
    setZoneActive(zone, true);
  });
  zone.addEventListener("dragleave", () => setZoneActive(zone, false));
  zone.addEventListener("drop", async (evt) => {
    evt.preventDefault();
    setZoneActive(zone, false);
    const file = evt.dataTransfer?.files?.[0];
    await onFile(file);
  });

  pickBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async (evt) => {
    const file = evt.target.files?.[0];
    await onFile(file);
    fileInput.value = "";
  });
}

function bindJdPasteZone() {
  const zone = el("jdPasteZone");
  const readClipboardImage = async (evt) => {
    const items = evt.clipboardData?.items || [];
    for (const item of items) {
      if (item.type && item.type.startsWith("image/")) {
        evt.preventDefault();
        const file = item.getAsFile();
        if (!file) return;
        try {
          await extractInputs({ jdImageFile: file });
        } catch (err) {
          setStatus("JD截图识别失败", "needs-input");
        }
        return;
      }
    }
  };

  zone.addEventListener("paste", readClipboardImage);
  document.addEventListener("paste", async (evt) => {
    if (document.activeElement === zone) {
      return;
    }
    await readClipboardImage(evt);
  });
}

// ---------- 核心逻辑 ----------
function extractKeywords(text) {
  return Array.from(
    new Set(
      text
        .split(/[\s,，。；;：:、\n]+/)
        .map((s) => s.trim())
        .filter((s) => s.length >= MIN_KEYWORD_LEN)
        .slice(0, MAX_KEYWORDS)
    )
  );
}

function checkClarification(resume) {
  const questions = [];
  if (!/\d/.test(resume)) {
    questions.push("简历中缺少数字化结果，请补充具体指标（如获客数量、效率提升等）。");
  }
  if (!/求职意向|目标岗位/.test(resume)) {
    questions.push("请补充求职意向或目标岗位。");
  }
  return questions;
}

function buildMeta(clarification, config) {
  return {
    requires_clarification: clarification.length > 0,
    clarification_questions: clarification,
    ui_mode: "preview",
    page_budget: {
      budgets: {
        total_bullets_budget: config.bullets,
        total_chars_budget: config.chars,
        module_ratio: MODULE_RATIO,
        per_line_limit: {
          max_chars_per_line: config.lineChars,
          max_lines_per_bullet: config.lineCount,
        },
      },
    },
  };
}

function buildPreviewPayload() {
  const jd = el("jdText").value.trim();
  const resume = el("resumeText").value.trim();

  const config = {
    bullets: parseNum(el("budgetBullets").value, DEFAULT_BUDGET.bullets),
    chars: parseNum(el("budgetChars").value, DEFAULT_BUDGET.chars),
    lineChars: parseNum(el("lineChars").value, DEFAULT_BUDGET.lineChars),
    lineCount: parseNum(el("lineCount").value, DEFAULT_BUDGET.lineCount),
  };

  const keywords = extractKeywords(jd);
  const clarification = checkClarification(resume);
  const meta = buildMeta(clarification, config);

  return {
    meta,
    inputs: {
      jd_length: jd.length,
      resume_length: resume.length,
      extracted_keywords: keywords,
    },
    resume: {
      basic: {
        name: "待识别",
        target_role: "待识别",
      },
      core: {
        work_experience: ["预览模式：接入后端 API 生成真实定制结果。"],
      },
      auxiliary: {
        projects: ["预览模式：展示页面结构与预算参数。"],
      },
      skills: {
        掌握: [],
        熟悉: [],
        精通: [],
      },
    },
  };
}

async function requestBackendPayload() {
  const jd = el("jdText").value.trim();
  const resume = el("resumeText").value.trim();
  const format = el("exportFormat").value;
  const config = {
    bullets: parseNum(el("budgetBullets").value, DEFAULT_BUDGET.bullets),
    chars: parseNum(el("budgetChars").value, DEFAULT_BUDGET.chars),
    lineChars: parseNum(el("lineChars").value, DEFAULT_BUDGET.lineChars),
    lineCount: parseNum(el("lineCount").value, DEFAULT_BUDGET.lineCount),
    moduleRatio: MODULE_RATIO,
    industry: DEFAULT_INDUSTRY,
    ai: DEFAULT_AI_CONFIG,
  };

  const resp = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      jd_text: jd,
      resume_text: resume,
      config,
      format,
    }),
  });
  if (!resp.ok) {
    const maybeJson = await resp.json().catch(() => ({}));
    throw new Error(maybeJson.error || "后端请求失败");
  }

  if (format === "json") {
    const data = await resp.json();
    return {
      format,
      data,
      text: JSON.stringify(data, null, 2),
      blob: new Blob([JSON.stringify(data, null, 2)], { type: MIME_MAP.json }),
    };
  }

  if (format === "pdf") {
    const blob = await resp.blob();
    return {
      format,
      data: null,
      text: "[PDF 二进制已生成，可点击下载文件]",
      blob,
    };
  }

  const text = await resp.text();
  return {
    format,
    data: null,
    text,
    blob: new Blob([text], { type: MIME_MAP[format] || "text/plain;charset=utf-8" }),
  };
}

// ---------- UI 状态 ----------
function setStatus(text, state) {
  const tag = el("statusTag");
  tag.textContent = text;
  tag.dataset.status = state || "idle";
}

// ---------- 渲染 ----------
function render(text) {
  el("outputBox").textContent = text;
}

function downloadLatest() {
  if (!latestOutput.blob) return;
  const link = document.createElement("a");
  const url = URL.createObjectURL(latestOutput.blob);
  link.href = url;
  link.download = `customized_resume.${EXT_MAP[latestOutput.format] || "txt"}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function updateCopyButtonLabel() {
  const format = el("exportFormat").value;
  const copyBtn = el("copyBtn");
  copyBtn.textContent = format === "pdf" ? "复制提示" : "复制内容";
}

// ---------- 事件处理 ----------
async function handleSubmit(evt) {
  evt.preventDefault();
  setStatus("生成中", "generating");

  try {
    const response = await requestBackendPayload();
    latestOutput = {
      format: response.format,
      text: response.text,
      blob: response.blob,
    };
    render(response.text);
    setStatus(
      response.data?.meta?.requires_clarification ? "需追问" : "已生成",
      response.data?.meta?.requires_clarification ? "needs-input" : "done"
    );
    return;
  } catch (err) {
    // 后端未启动或报错时，自动降级到预览模式，确保页面可用。
    const payload = buildPreviewPayload();
    payload.meta.backend_error = String(err?.message || err);
    const text = JSON.stringify(payload, null, 2);
    latestOutput = {
      format: "json",
      text,
      blob: new Blob([text], { type: MIME_MAP.json }),
    };
    render(text);
  }

  setStatus("预览模式（后端未连接）", "needs-input");
}

async function copyOutput() {
  const text = latestOutput.text || "";
  if (!text.trim() || text === "{}") return;

  const btn = el("copyBtn");
  try {
    await navigator.clipboard.writeText(text);
    const old = btn.textContent;
    btn.textContent = "已复制";
    setTimeout(() => {
      btn.textContent = old;
    }, 1200);
  } catch (err) {
    // 降级：选中文本
    const range = document.createRange();
    range.selectNode(el("outputBox"));
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
  }
}

// ---------- 初始化 ----------
el("resumeForm").addEventListener("submit", handleSubmit);
el("copyBtn").addEventListener("click", copyOutput);
el("downloadBtn").addEventListener("click", downloadLatest);
el("exportFormat").addEventListener("change", updateCopyButtonLabel);
updateCopyButtonLabel();
bindResumeDropZone();
bindJdPasteZone();