# 日语CS专业课复习文档生成器

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-6C4DF6)](https://claude.ai/code)

软件工程中日合作办学项目专用。根据**日语授课的 CS 专业课课件**和**历年试卷**，自动生成结构化复习文档 PDF。支持 PDF 讲义和 PPTX 两种源文件格式。

## 适用场景

用日语学习 CS 专业课（计算机网络、数据库、操作系统、数据结构等），考试在即：

- **模式一**：课件 → 复习文档（术语表 + 知识点卡片 + 对比表格 + 精选图片）
- **模式二**：课件 + 历年试卷 → 考点分析 + 高频考点精讲 + 未考重点预警

## 输出语言

| 模式 | 说明 | 示例效果 |
|------|------|----------|
| `jp_first`（推荐） | 日语原文在上，中文完整翻译在下（蓝底区分），关键词标签，对比表格，精选图片 | 适合对照日语原文备考 |
| `chinese_annotated` | 中文主述，关键术语用 English / 日本語 行内标注，对比表格 | 适合快速理解知识点 |

## 项目结构

```
japanese-exam-review-skill/
├── japanese-exam-review.md   ← Skill 定义文件（触发条件、工作流、内容规范、视觉规范）
├── scripts/
│   ├── parse_ppt.py          ← PPTX → 文本 + 图片 → JSON
│   ├── parse_pdf.py          ← PDF 试卷 → 文本 → JSON
│   └── generate_pdf.py       ← 内容 JSON → PDF（双视觉预设）
├── assets/
├── requirements.txt
└── README.md
```

## 安装

### 1. 克隆到 Claude Code skills 目录

```bash
mkdir -p .claude/skills
git clone https://github.com/oo0816/-japanese-exam-review-skill.git .claude/skills/japanese-exam-review
```

### 2. 安装 Python 依赖

```bash
pip install -r .claude/skills/japanese-exam-review/requirements.txt
```

### 3. 下载 CJK 字体

```powershell
mkdir fonts
Invoke-WebRequest -Uri "https://fonts.gstatic.com/s/notosanssc/v40/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYw.ttf" -OutFile "fonts\NotoSansSC-Regular.ttf"
Invoke-WebRequest -Uri "https://fonts.gstatic.com/s/notosanssc/v40/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaGzjCnYw.ttf" -OutFile "fonts\NotoSansSC-Bold.ttf"
```

### 4. 准备目录

```bash
mkdir ppt      # 放入课件（.pptx 或 .pdf）
mkdir exams    # 放入历年试卷 .pdf（可选）
```

## 使用

在 Claude Code 中输入包含**日语相关 + CS 专业课**两个关键词的请求：

```
> 帮我把日语的计算机网络PPT整理成复习文档
> 日本老师的数据库课件和历年试卷，帮我做考点分析
```

Skill 会强制执行三问确认（模式 → 语言 → 其他需求），然后自动解析、生成、核查、输出 PDF 到 `output/` 目录。

## 生成的 PDF 内容块

| 类型 | 用途 |
|------|------|
| `term_table` | 专业术语对照表（日本語 → 読み方 → 中国語 → 説明） / 对比表格（日中双语） |
| `concept_card` | 知识点卡片：标题 + 关键词标签 + 日语正文 + 中文蓝底翻译（交错排列）+ 考试提示 |
| `highlight_box` | 重点提醒 / 考试要点 |
| `image` | 精选架构图、流程图 + 双语图注 |
| `exam_stat` | 考试统计（题型分布、分值占比） |

## 视觉规范

两套预设，通过 `-l` 参数切换：

- **jp_first**：高对比正文 `#222`、翻译蓝底 `#edf2f8`、表格有边框、卡片间距 4pt
- **chinese_annotated**：SE 指南原版 `#323232` 正文、表格无边框、卡片间距 2pt

共用：16mm/17mm 边距、8.5pt/7pt 字号体系、NotoSansSC 字体

## 依赖

- Python >= 3.10
- python-pptx
- PyMuPDF
- fpdf2
- Pillow

## License

MIT
