# 日语CS专业课复习文档生成器

[![日本語](./assets/badge-jp.svg)](./README.md)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-6C4DF6)](https://claude.ai/code)

软件工程中日合作办学项目专用。根据**日语授课的 CS 专业课 PPT** 和**历年试卷**，自动生成结构化复习文档 PDF。

## 适用场景

你是软件工程/CS 中日合办项目的学生，用日语学习专业课（计算机网络、数据库、操作系统、数据结构等），考试在即，需要：

- 📝 **模式一**：把日文 PPT 课件整理成复习文档（术语表 + 知识点 + 重点图）
- 📊 **模式二**：结合历年试卷，生成考点分析 + 高频考点精讲

## 项目结构

```
japanese-exam-review-skill/
├── japanese-exam-review.md   ← Skill 定义文件
├── scripts/
│   ├── parse_ppt.py          ← PPTX → 文本 + 图片 → JSON
│   ├── parse_pdf.py          ← PDF 试卷 → 文本 → JSON
│   └── generate_pdf.py       ← 内容 JSON → PDF
├── assets/                   ← Badge/图标资源
├── requirements.txt
└── README.md
```

## 安装

### 1. 克隆到 Claude Code skills 目录

```bash
# 在你的项目根目录下
mkdir -p .claude/skills
git clone https://github.com/oo0816/japanese-exam-review-skill.git .claude/skills/japanese-exam-review
```

### 2. 安装 Python 依赖

```bash
pip install -r .claude/skills/japanese-exam-review/requirements.txt
```

### 3. 下载 CJK 字体

```powershell
# 自动下载 NotoSansSC（覆盖中文简体 + 日语）
mkdir fonts
Invoke-WebRequest -Uri "https://fonts.gstatic.com/s/notosanssc/v40/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYw.ttf" -OutFile "fonts\NotoSansSC-Regular.ttf"
Invoke-WebRequest -Uri "https://fonts.gstatic.com/s/notosanssc/v40/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaGzjCnYw.ttf" -OutFile "fonts\NotoSansSC-Bold.ttf"
```

### 4. 准备目录

```bash
mkdir ppt      # 放入你的 .pptx 课件
mkdir exams    # 放入历年试卷 .pdf
```

## 使用

### 触发 Skill

在 Claude Code 中输入包含 **日语相关** + **CS专业课** 两个关键词的请求，Skill 会自动激活：

```
> 帮我把日语的计算机网络PPT整理成复习文档
> 日本老师的数据库课件和历年试卷，帮我做考点分析
> このPPTを復習ドキュメントにして (PPTはCSの授業です)
```

### 工作流程

1. Claude 确认你的需求（模式 + 输出语言）
2. 自动运行解析脚本提取文本和图片
3. AI 分析内容，生成结构化复习材料
4. 输出 PDF 到 `output/` 目录

### 输出语言选项

| 选项 | 说明 |
|---|---|
| `bilingual` (默认) | 中日双语：解释用中文，术语保留日文并注音 |
| `chinese` | 中文为主：尽量用中文，日语术语仅首次标注 |
| `japanese` | 日语为主：主用日语，中文作辅助注释 |

### 内容块类型

生成的 PDF 支持以下内容块：

| 类型 | 用途 | 示例 |
|---|---|---|
| `term_table` | 专业术语对照表 | 日本語 → 読み方 → 中国語 → 説明 |
| `concept_card` | 知识点卡片 | 带左侧色条的详细讲解 |
| `highlight_box` | 重点提醒框 | 考点预警 / 易错提醒 |
| `image` | 嵌入图片 | 架构图、流程图 + 双语图注 |
| `exam_stat` | 考试统计 | 题型分布、分值占比 |

## 示例输出

见 [`examples/`](./examples/) 目录（含测试 PPT 和生成的复习文档 PDF）。

## 依赖

- Python >= 3.10
- python-pptx
- PyMuPDF
- fpdf2
- Pillow

## License

MIT
