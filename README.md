# Resume Master

## 🚀 概述

**Resume Master** 是一款专为求职场景设计的智能简历定制工具。通过结合职位描述（JD）与原始简历，利用AI与规则引擎生成结构化、符合预算控制的定制化简历，帮助求职者提升简历匹配度。

## ✨ 核心功能

### 🎯 智能定制与压缩

- **一键定制**：智能提取JD关键词，自动重排经历内容，生成结构化简历
- **单页预算控制**：支持配置总条目数、总字符数、每行字符数及每条行数，确保简历精炼有力
- **真实性约束**：自动检测并提示缺少量化结果的内容，提供可疑数值与证据不足的风险提醒

### 📎 多模态输入输出

- **输入支持**：支持JD截图云端OCR（需Vision模型）及简历文件拖拽导入（txt/md/docx/pdf）
- **导出格式**：支持JSON、Markdown、HTML、PDF四种格式

### 🔍 辅助分析

- **语义匹配报告**：内置行业词库与轻量语义匹配统计分析
- **可选AI模式**：可开启云端模型辅助生成，未配置Key时自动回退至规则模式

## 🏗️ 架构设计

### 交互层

- `frontend_2.0` - Web前端界面
- `main.py` - CLI批处理工具

### 服务层

- `api_server.py` - HTTP API入口

### 核心处理模块

- **提取模块**：`text_extractor.py`（文本提取）、`jd_parser.py`（JD解析）、`resume_parser.py`（简历解析）
- **生成与校验**：`resume_generator.py`（生成）、`compressor.py`（压缩）、`layout_validator.py`（布局校验）、`authenticity_validator.py`（真实性校验）
- **AI适配**：`llm_client.py`（云端模型调用）、`ai_adapter.py`（AI模式适配）

## ⚙️ 快速开始

### 环境配置

```
# 安装依赖
pip install -r requirements.txt

# 可选配置
# 配置环境变量以使用截图OCR或AI模式
# LLM_API_KEY、LLM_API_BASE等
```

### 启动方式

```
# 启动API服务
python api_server.py
# 默认地址：http://127.0.0.1:8000

# 前端交互
# 直接打开 frontend_2.0/index.html

# CLI批处理
# 通过命令行参数指定输入输出及配置
# 如：--jd, --resume, --out等
```

### API接口说明

#### 生成简历

**POST** `/api/generate`

**参数**：

- `jd_text`：职位描述文本
- `resume_text`：原始简历文本
- `format`：输出格式（json/md/html/pdf）
- `config`：预算与行业配置

#### 输入提取

**POST** `/api/extract-inputs`

**参数**：

- `jd_image_base64`：JD截图Base64编码
- `resume_file_base64`：简历文件Base64编码

## ⚠️ 注意事项

### 依赖说明

- **API Key依赖**：不配置Key仍可运行文本生成主流程，但截图OCR功能将不可用
- **AI模式定位**：AI仅作为"可选骨架"，主改写逻辑由规则引擎主导

### 使用限制

- **免责声明**：输出内容仅作编辑辅助，用户需自行复核内容的真实性与合规性

## 💡 技术优势

Resume Master通过将**规则引擎**（预算控制、真实性校验）与**AI能力**（OCR、语义匹配）相结合，为求职者提供了一套高效、可控的简历优化方案。既保证了内容的合规性，又提升了定制化效率，是求职过程中的得力助手。

---

# Resume Master

## 🚀 Overview

**Resume Master** is an intelligent resume customization tool designed for job-seeking scenarios. By combining job descriptions (JD) with original resumes, it leverages AI and rule engines to generate structured, budget-controlled customized resumes, helping job seekers improve resume match rates.

## ✨ Core Features

### 🎯 Intelligent Customization and Compression

- **One-click Customization**: Smartly extracts JD keywords, automatically rearranges experience content, and generates structured resumes
- **Single-page Budget Control**: Supports configuration of total entries, total characters, characters per line, and lines per entry to ensure concise and powerful resumes
- **Authenticity Constraints**: Automatically detects and alerts on content lacking quantitative results, providing risk alerts for suspicious values and insufficient evidence

### 📎 Multi-modal Input/Output

- **Input Support**: Supports JD screenshot cloud OCR (requires Vision model) and resume file drag-and-drop import (txt/md/docx/pdf)
- **Export Formats**: Supports JSON, Markdown, HTML, and PDF

### 🔍 Auxiliary Analysis

- **Semantic Matching Report**: Built-in industry lexicon and lightweight semantic matching statistical analysis
- **Optional AI Mode**: Can enable cloud model assistance, automatically falls back to rule mode when no Key is configured

## 🏗️ Architecture Design

### Interaction Layer

- `frontend_2.0` - Web frontend interface
- `main.py` - CLI batch processing tool

### Service Layer

- `api_server.py` - HTTP API entry point

### Core Processing Modules

- **Extraction Modules**: `text_extractor.py` (text extraction), `jd_parser.py` (JD parsing), `resume_parser.py` (resume parsing)
- **Generation and Validation**: `resume_generator.py` (generation), `compressor.py` (compression), `layout_validator.py` (layout validation), `authenticity_validator.py` (authenticity validation)
- **AI Adaptation**: `llm_client.py` (cloud model calling), `ai_adapter.py` (AI mode adaptation)

## ⚙️ Quick Start

### Environment Configuration

```
# Install dependencies
pip install -r requirements.txt

# Optional configuration
# Configure environment variables to use screenshot OCR or AI mode
# LLM_API_KEY, LLM_API_BASE, etc.
```

### Startup Methods

```
# Start API service
python api_server.py
# Default address: http://127.0.0.1:8000

# Frontend interaction
# Directly open frontend_2.0/index.html

# CLI batch processing
# Specify input/output and configuration through command line parameters
# Such as: --jd, --resume, --out, etc.
```

### API Interface Documentation

#### Generate Resume

**POST** `/api/generate`

**Parameters**:

- `jd_text`: Job description text
- `resume_text`: Original resume text
- `format`: Output format (json/md/html/pdf)
- `config`: Budget and industry configuration

#### Input Extraction

**POST** `/api/extract-inputs`

**Parameters**:

- `jd_image_base64`: JD screenshot Base64 encoding
- `resume_file_base64`: Resume file Base64 encoding

## ⚠️ Notes

### Dependency Information

- **API Key Dependency**: Text generation main process can still run without configuration, but screenshot OCR function will be unavailable
- **AI Mode Positioning**: AI serves as an "optional skeleton", main rewriting logic is driven by rule engine

### Usage Limitations

- **Disclaimer**: Output content is for editing assistance only, users need to verify authenticity and compliance of content

## 💡 Technical Advantages

Resume Master combines **rule engines** (budget control, authenticity validation) with **AI capabilities** (OCR, semantic matching) to provide job seekers with an efficient, controllable resume optimization solution. It ensures content compliance while enhancing customization efficiency, serving as a reliable assistant in the job-seeking process.

