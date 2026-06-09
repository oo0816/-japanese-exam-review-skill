"""Generate PDF review document from content JSON."""
import json
import sys
from pathlib import Path
from fpdf import FPDF


class ReviewPDF(FPDF):
    """Custom PDF with Japanese font support and content blocks."""

    def __init__(self, language="bilingual"):
        super().__init__()
        self.language = language  # "bilingual", "chinese", "japanese"
        self.font_reg = None
        self.font_bold = None
        self._register_fonts()
        self.set_auto_page_break(True, margin=20)

    def _register_fonts(self):
        """Register fonts with CJK support (SC covers CN+JP)."""
        font_dir = Path("fonts")
        regular = font_dir / "NotoSansSC-Regular.ttf"
        bold = font_dir / "NotoSansSC-Bold.ttf"
        # Fallback to JP fonts if SC not available
        if not regular.exists():
            regular = font_dir / "NotoSansJP-Regular.ttf"
        if not bold.exists():
            bold = font_dir / "NotoSansJP-Bold.ttf"

        if regular.exists():
            self.add_font("CJK", fname=str(regular))
            self.font_reg = "CJK"
        else:
            self.font_reg = "Helvetica"

        if bold.exists():
            self.add_font("CJK", style="B", fname=str(bold))
            self.font_bold = "CJK"
        else:
            self.font_bold = "Helvetica"

    # ---------- helpers ----------
    def _w(self):
        return self.w - 2 * self.l_margin

    def _set_font(self, style="", size=10):
        if self.font_reg:
            self.set_font(self.font_reg, style, size)

    def _write_paragraph(self, text, size=10):
        self._set_font("", size)
        self.multi_cell(self._w(), 6, text, align="L")

    def _section_title(self, text, level=1):
        sizes = {1: 16, 2: 13, 3: 11}
        self.ln(4)
        self._set_font("B", sizes.get(level, 11))
        self.multi_cell(self._w(), 8, text, align="L")
        if level == 1:
            self.set_draw_color(60, 60, 60)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(3)
        else:
            self.ln(1)

    def _draw_highlight_box(self, text, color=(255, 245, 220)):
        """Draw a box with colored background for emphasis."""
        self.set_fill_color(*color)
        y_before = self.get_y()
        self._set_font("", 9)
        x0 = self.l_margin + 3
        self.set_x(x0)
        self.multi_cell(self._w() - 6, 5.5, text, align="L", fill=True)
        y_after = self.get_y()
        # Draw border
        self.set_draw_color(color[0] - 30, color[1] - 30, color[2] - 30)
        self.rect(self.l_margin, y_before, self._w(), y_after - y_before, "D")
        self.ln(2)

    # ---------- block renderers ----------

    def render_heading(self, block):
        self._section_title(block["text"], block.get("level", 1))

    def render_text(self, block):
        self._write_paragraph(block["content"], block.get("size", 10))

    def render_image(self, block):
        img_path = Path("output/images") / block["file"]
        if not img_path.exists():
            self._write_paragraph(f"[Image not found: {block['file']}]", 8)
            return

        self.ln(2)
        # Calculate display width
        max_w = self._w() * 0.9
        max_h = 100  # max height in mm

        try:
            from PIL import Image
            with Image.open(img_path) as im:
                img_w, img_h = im.size
        except Exception:
            img_w, img_h = 300, 200

        # Scale to fit
        scale = min(max_w / (img_w * 0.2646), max_h / (img_h * 0.2646), 1.0)
        disp_w = img_w * 0.2646 * scale
        # disp_h = img_h * 0.2646 * scale

        x = self.l_margin + (self._w() - disp_w) / 2
        self.image(str(img_path), x=x, w=disp_w)

        # Caption
        if block.get("caption"):
            self.ln(2)
            self._set_font("", 8)
            self.cell(self._w(), 5, block["caption"], align="C")
        self.ln(4)

    def render_term_table(self, block):
        """Render a terminology table."""
        self.ln(2)
        cols = block.get("columns", ["日语", "读音", "中文", "说明"])
        col_widths = block.get("col_widths", [50, 30, 35, self._w() - 115])
        rows = block.get("rows", [])

        # Header
        self._set_font("B", 8)
        self.set_fill_color(230, 230, 230)
        for i, col in enumerate(cols):
            self.cell(col_widths[i], 7, col, border=1, fill=True, align="C")
        self.ln()

        # Data rows
        self._set_font("", 8)
        for row in rows:
            # Calculate max height needed
            max_lines = 1
            col_texts = []
            for i, cell_text in enumerate(row):
                if i >= len(col_widths):
                    break
                text_w = self.get_string_width(str(cell_text))
                lines = max(1, int(text_w / (col_widths[i] - 1)) + 1)
                max_lines = max(max_lines, lines)
                col_texts.append(str(cell_text))
            row_h = max(7, 5.5 * max_lines)

            y_before = self.get_y()
            x_start = self.get_x()
            for i, ct in enumerate(col_texts):
                if i >= len(col_widths):
                    break
                self.set_xy(x_start + sum(col_widths[:i]), y_before)
                # Check if we need a new page
                if y_before + row_h > self.h - self.b_margin:
                    self.add_page()
                    y_before = self.get_y()
                self.multi_cell(col_widths[i], 5.5, ct, border=1, align="L")
            self.set_y(y_before + row_h)

    def render_concept_card(self, block):
        """Render a knowledge point card with left color bar."""
        self.ln(2)
        y0 = self.get_y()

        # Title with colored left bar
        self.set_fill_color(52, 73, 94)
        self.set_draw_color(52, 73, 94)
        bar_w = 3
        self.rect(self.l_margin, y0, bar_w, 7, "F")
        self._set_font("B", 11)
        self.set_x(self.l_margin + bar_w + 2)
        self.cell(self._w() - bar_w - 2, 7, block.get("title", ""), align="L")
        self.ln()

        # Content
        if block.get("content"):
            self._set_font("", 9)
            self.set_x(self.l_margin + bar_w + 2)
            self.multi_cell(self._w() - bar_w - 2, 5.5, block["content"], align="L")

        # Optional example
        if block.get("example"):
            self.ln(1)
            self.set_fill_color(245, 245, 245)
            self._set_font("", 8)
            self.set_x(self.l_margin + bar_w + 4)
            self.multi_cell(self._w() - bar_w - 6, 5, block["example"], align="L", fill=True)
        self.ln(2)

    def render_highlight_box(self, block):
        self.ln(2)
        colors = {
            "warning": (255, 235, 200),
            "tip": (210, 240, 210),
            "info": (200, 220, 255),
            "danger": (255, 200, 200)
        }
        color = colors.get(block.get("box_type", "warning"), (255, 245, 220))
        label_map = {"warning": "⚠ 易错", "tip": "💡 技巧", "info": "ℹ 注意", "danger": "❗ 重要"}
        label = block.get("label", label_map.get(block.get("box_type", "warning"), ""))
        text = f"{label}\n{block['content']}" if label else block["content"]
        self._draw_highlight_box(text, color)

    def render_exam_stat(self, block):
        """Render exam statistics section."""
        self._section_title(block.get("title", "考试统计"), 2)

        items = block.get("items", [])
        if block.get("stat_type") == "distribution":
            # Draw as table
            self._set_font("B", 9)
            col_w = self._w() / 3
            self.cell(col_w, 7, "题型", border=1, align="C")
            self.cell(col_w, 7, "分值", border=1, align="C")
            self.cell(col_w, 7, "占比", border=1, align="C")
            self.ln()
            self._set_font("", 9)
            for item in items:
                self.cell(col_w, 7, item.get("type", ""), border=1, align="C")
                self.cell(col_w, 7, str(item.get("score", "")), border=1, align="C")
                self.cell(col_w, 7, str(item.get("ratio", "")), border=1, align="C")
                self.ln()
        else:
            for item in items:
                self._write_paragraph(f"• {item}", 9)

        self.ln(3)


def generate_pdf(content_json_path, output_path, language="bilingual"):
    """Generate PDF from content JSON file."""
    with open(content_json_path, "r", encoding="utf-8") as f:
        document = json.load(f)

    pdf = ReviewPDF(language=language)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)

    # Title page
    pdf.add_page()
    pdf.ln(30)
    pdf._set_font("B", 24)
    title = document.get("title", "复习文档")
    pdf.multi_cell(pdf._w(), 12, title, align="C")
    pdf.ln(5)
    pdf._set_font("", 11)
    subtitle = document.get("subtitle", "")
    if subtitle:
        pdf.multi_cell(pdf._w(), 7, subtitle, align="C")
    pdf.ln(3)
    pdf._set_font("", 9)
    pdf.cell(pdf._w(), 6,
             f"生成语言: {language}  |  软件工程中日合办课程", align="C")

    # Content sections
    for section in document.get("sections", []):
        pdf.add_page()
        section_title = section.get("title", "")
        pdf._section_title(section_title, 1)

        # Section overview
        if section.get("overview"):
            pdf._write_paragraph(section["overview"], 9)
            pdf.ln(3)

        # Render blocks
        for block in section.get("blocks", []):
            block_type = block.get("type", "text")
            render_func = getattr(pdf, f"render_{block_type}", None)
            if render_func:
                render_func(block)
            else:
                pdf._write_paragraph(f"[Unknown block type: {block_type}]", 8)

    # Footer: page numbers
    pdf.alias_nb_pages()
    for page_num in range(1, pdf.page + 1):
        pdf.page = page_num
        pdf.set_y(-15)
        pdf._set_font("", 7)
        pdf.cell(0, 10, str(page_num), align="C")

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate review PDF from JSON")
    parser.add_argument("input", help="Path to content JSON file")
    parser.add_argument("-o", "--output", default="output/review.pdf", help="Output PDF path")
    parser.add_argument("-l", "--language", default="bilingual",
                        choices=["bilingual", "chinese", "japanese"],
                        help="Output language preference")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: input file not found: {args.input}")
        sys.exit(1)

    result = generate_pdf(args.input, args.output, args.language)
    print(f"PDF generated: {result}")


if __name__ == "__main__":
    main()
