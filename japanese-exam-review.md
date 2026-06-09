# 日语考试复习文档生成器

## 概述
为软件工程中日合作办学项目的学生，根据日语授课的 PPT 课件和历年试卷，自动生成复习文档 PDF。用户是 CS 专业学生，用日语学习软件工程课程（数据结构、计算机网络、数据库、操作系统等）。

## 触发条件

本 Skill 仅在**同时满足以下两个要素**时触发：

**要素 A — 日语相关**：
- 提及"日语""日文""日本語""Japanese""Japan"
- 提及日本学校、日本教师、日本教材
- 提及日语考试、日语授课、日本课程

**要素 B — 软件专业课程**：
- 提及具体的 CS/SE 专业课：计算机网络、数据库、操作系统、数据结构、算法、软件工程、编程语言（Java/C/Python 等）、计算机组成原理、编译原理、线性代数、离散数学等
- 提及 PPT 课件 .pptx 或试卷 .pdf，且上下文涉及专业课
- 提及"专业课""CS 课程""软件工程""编程""代码"

**触发示例**：
- "帮我整理日语的计算机网络PPT" ✅
- "日本老师的数据库课件帮我生成复习资料" ✅
- "我有一份日文的算法PPT和历年试卷，帮我分析考点" ✅
- "このPPTを復習ドキュメントにして"（且 PPT 内容为 CS 专业课）✅
- "帮我把计算机网络PPT整理成复习文档" ❌（未涉及日语）
- "帮我学日语语法" ❌（不是专业课）

## 前置步骤：确认用户需求

在开始处理前，向用户确认：
1. **模式选择**：模式一（仅 PPT 复习）还是模式二（PPT + 试卷考点分析）？
2. **输出语言**：
   - `bilingual`（中日双语，默认推荐）：解释用中文，关键术语保留日语原文并标注读音和中文对应
   - `chinese`（中文为主）：尽可能用中文表述，日语术语仅首次出现时标注
   - `japanese`（日语为主）：主要用日语，中文仅作辅助注释
3. **其他需求**：是否有特别关注的章节？是否有需要强调的考点？

## 工作流程

### 模式一：PPT → 复习文档

1. **解析 PPT**
   ```
   python scripts/parse_ppt.py
   ```
   读取 `output/parsed_ppt.json`，了解所有幻灯片的文本和图片信息。

2. **筛选重点图片**
   - 使用 Read 工具查看提取出的图片（`output/images/`），判断哪些是：
     - 系统架构图、网络拓扑图 → 最高优先级
     - 算法流程图、状态机图、UML 图、ER 图 → 高优先级
     - 公式截图、代码截图、表格截图 → 保留
     - 小图标、装饰图、背景图、Logo → 舍弃
   - 对大尺寸图片（width_px > 400）优先查看判断

3. **生成内容 JSON**
   根据 PPT 内容和筛选出的图片，按照 **内容 JSON 规范**（见下文）编写 `output/content_mode1.json`。

   组织逻辑：
   - 以 PPT 的自然章节/课次划分 section
   - 每个 section 包含：
     - **章节概览**（overview）：简要说明本章覆盖的 CS 知识域
     - **专业术语表**（term_table block）：日语术语 → 读音 → 中文对应术语 → 简明解释
     - **知识点卡片**（concept_card block）：每个核心知识点一张卡片
     - **重点图表**（image block）：嵌入筛选出的图片，附双语图注
     - **易混淆概念**（highlight_box block）：dog-food 相近术语的区分

4. **生成 PDF**
   ```
   python scripts/generate_pdf.py output/content_mode1.json -o output/review_mode1.pdf -l <语言选择>
   ```

### 模式二：PPT + 试卷 → 考点复习文档

1. **解析 PPT 和试卷**
   ```
   python scripts/parse_ppt.py
   python scripts/parse_pdf.py
   ```
   读取 `output/parsed_ppt.json` 和 `output/parsed_exams.json`。

2. **试卷分析**
   - 识别每道题的题型（选择题、填空题、简答题、计算题、编程题等）
   - 提取每道题考察的知识点关键词
   - 统计各知识点的出现频次和分值权重
   - 记录哪份试卷（哪一年）考了哪个知识点

3. **交叉分析**
   - 将试卷考点映射回 PPT 对应章节
   - 标记「高频考点」：出现 >= 2 次的考点
   - 标记「未考重点」：PPT 中篇幅大但试卷中未出现的知识点
   - 标记「易错题型」：结合题目复杂度判断

4. **生成内容 JSON**
   编写 `output/content_mode2.json`，结构：
   - **考试情报** section（exam_stat block）
   - **高频考点排行** section（term_table + highlight_box）
   - **逐考点精讲** section（concept_card + image + highlight_box）
   - **未考重点预警** section（highlight_box type=danger）
   - **易错题型分析** section（concept_card）
   - **模拟自测建议** section（text）

5. **生成 PDF**
   ```
   python scripts/generate_pdf.py output/content_mode2.json -o output/review_mode2.pdf -l <语言选择>
   ```

---

## 内容 JSON 规范

`generate_pdf.py` 接受如下结构的 JSON 文件：

```json
{
  "title": "复习文档标题",
  "subtitle": "副标题（可选）",
  "sections": [
    {
      "title": "章节/部分标题",
      "overview": "本章概览（可选）",
      "blocks": [
        {块1},
        {块2},
        ...
      ]
    }
  ]
}
```

### 支持的内容块类型

#### heading
```json
{"type": "heading", "text": "标题文本", "level": 2}
```
`level`: 1=主标题, 2=子标题, 3=小标题

#### text
```json
{"type": "text", "content": "段落文本", "size": 10}
```
`size`: 字体大小，默认 10

#### image
```json
{
  "type": "image",
  "file": "slide3_img1.png",
  "caption": "図1: TCPの3ウェイハンドシェイク (三次握手)"
}
```
`file`: 相对于 `output/images/` 的文件名
`caption`: 图片说明（建议中日双语）

#### term_table
```json
{
  "type": "term_table",
  "columns": ["日本語", "読み方", "中国語", "説明"],
  "col_widths": [45, 30, 35, 65],
  "rows": [
    ["ルーティング", "ルーティング", "路由", "パケットの転送経路を決定する処理"],
    ...
  ]
}
```
`col_widths`: 四列宽度（mm），总和约 175mm，可省略使用默认值

#### concept_card
```json
{
  "type": "concept_card",
  "title": "知識点标题（建议日语）",
  "content": "详细解释（中日双语）",
  "example": "具体示例或代码（可选）"
}
```

#### highlight_box
```json
{
  "type": "highlight_box",
  "box_type": "warning",
  "label": "⚠ よく間違えるポイント",
  "content": "内容"
}
```
`box_type`: "warning"(橙) / "tip"(绿) / "info"(蓝) / "danger"(红)

#### exam_stat
```json
{
  "type": "exam_stat",
  "title": "試験統計",
  "stat_type": "distribution",
  "items": [
    {"type": "選択問題", "score": 30, "ratio": "30%"},
    {"type": "穴埋め問題", "score": 20, "ratio": "20%"},
    {"type": "記述問題", "score": 50, "ratio": "50%"}
  ]
}
```
`stat_type`: "distribution" 显示为三列表格，省略则显示为列表

---

## 内容质量要求

1. **专业术语准确**：日语术语必须与 PPT 原文一致，中文对应术语使用大陆 CS 领域标准译名
2. **保留日文原表述**：关键定义和概念解释保留日语原文，确保学生能对应考试中的日语表述
3. **图表说明双语化**：图片标题和说明用中日双语，方便理解
4. **考试导向**（模式二）：每个考点需标注"该考点出现在 20XX 年卷第 X 题"
5. **不要编造内容**：只基于 PPT 和试卷中实际存在的内容，不添加未涉及的知识点

---

## 注意事项

- 解析脚本会覆盖 `output/parsed_ppt.json` 和 `output/parsed_exams.json`，图片会保存到 `output/images/`
- 如果解析脚本报错「目录不存在」，提醒用户将文件放入对应目录（ppt/ 或 exams/）
- 生成 PDF 前确认 `fonts/NotoSansSC-Regular.ttf` 和 `fonts/NotoSansSC-Bold.ttf` 存在（覆盖中日韩全字符集）
- 模式二如果没有试卷文件，自动降级为模式一
