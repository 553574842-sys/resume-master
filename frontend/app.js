function el(id) {
  return document.getElementById(id);
}

function buildPreviewPayload() {
  const jd = el("jdText").value.trim();
  const resume = el("resumeText").value.trim();
  const totalBulletsBudget = Number(el("budgetBullets").value || 10);
  const totalCharsBudget = Number(el("budgetChars").value || 900);
  const maxCharsPerLine = Number(el("lineChars").value || 38);
  const maxLinesPerBullet = Number(el("lineCount").value || 2);

  const keywords = Array.from(
    new Set(
      jd
        .split(/[\s,，。；;：:、\n]+/)
        .map((s) => s.trim())
        .filter((s) => s.length >= 2)
        .slice(0, 15)
    )
  );

  const clarification = [];
  if (!/\d/.test(resume)) {
    clarification.push("简历中缺少明显数字化结果，请补充指标。");
  }
  if (!/求职意向|目标岗位/.test(resume)) {
    clarification.push("请补充求职意向或目标岗位。");
  }

  return {
    meta: {
      requires_clarification: clarification.length > 0,
      clarification_questions: clarification,
      ui_mode: "preview",
      page_budget: {
        budgets: {
          total_bullets_budget: totalBulletsBudget,
          total_chars_budget: totalCharsBudget,
          module_ratio: { core: 0.55, projects: 0.25, skills: 0.2 },
          per_line_limit: {
            max_chars_per_line: maxCharsPerLine,
            max_lines_per_bullet: maxLinesPerBullet,
          },
        },
      },
    },
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
        work_experience: ["预览模式：请接入后端 API 生成真实定制结果。"],
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

function setStatus(text) {
  el("statusTag").textContent = text;
}

function render(payload) {
  el("outputBox").textContent = JSON.stringify(payload, null, 2);
}

async function handleSubmit(evt) {
  evt.preventDefault();
  setStatus("生成中");

  const payload = buildPreviewPayload();
  render(payload);

  // 后续可替换成真实接口：
  // const response = await fetch("/api/generate-resume", { method: "POST", body: JSON.stringify(...) })
  setStatus(payload.meta.requires_clarification ? "需追问" : "已生成");
}

async function copyOutput() {
  const text = el("outputBox").textContent || "";
  if (!text.trim()) {
    return;
  }
  await navigator.clipboard.writeText(text);
  const old = el("copyBtn").textContent;
  el("copyBtn").textContent = "已复制";
  setTimeout(() => {
    el("copyBtn").textContent = old;
  }, 1200);
}

el("resumeForm").addEventListener("submit", handleSubmit);
el("copyBtn").addEventListener("click", copyOutput);
