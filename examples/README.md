# Examples

## Input: Content JSON

`content_example.json` — 计算机网络第1章的完整内容 JSON（jp_first 格式）。

包含的块类型：
- `term_table`：专业术语表（日本語 → 読み方 → 中国語 → 説明）
- `concept_card`：知识点卡片（含 title / content / translation / keywords / importance）
- `image`：图片块
- `highlight_box`：考试重点提示

完整规范见 `japanese-exam-review.md` → 内容 JSON 规范。

## Output: Generated PDF

`output_example_jp.pdf` — 由 `content_example.json` 生成的 PDF（jp_first 模式）。

生成命令：
```bash
python scripts/generate_pdf.py examples/content_example.json -o examples/output_example_jp.pdf -l jp_first
```
