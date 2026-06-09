"""Generate PDF review document from content JSON.
Styling based on the SE study guide design system.
"""
import json
import sys
from pathlib import Path
from fpdf import FPDF

# === Design System (matching SE study guide) ===

# Color palette
C_TITLE       = (0x1a, 0x3a, 0x5c)  # 17pt chapter title (dark navy)
C_SUBTITLE    = (0xc8, 0x32, 0x32)  # 10pt chapter subtitle / importance (red)
C_SECTION     = (0x28, 0x3c, 0x5a)  # 12pt section header (navy)
C_BODY        = (0x3c, 0x1e, 0x1e)  # 8.5pt body text (dark brown)
C_KEYPOINT    = (0x28, 0x32, 0x46)  # 8.5pt key/emphasis box text
C_EXAM        = (0xc8, 0x32, 0x32)  # 8.5pt exam highlight (red)
C_CAPTION     = (0xb4, 0x32, 0x32)  # 8pt figure caption (red-brown)
C_NOTE        = (0x64, 0x64, 0x64)  # 7pt commentary note (gray)
C_TABLE_HDR   = (0xff, 0xff, 0xff)  # 7.5pt table header text (white)
C_TABLE_BG    = (0x28, 0x3c, 0x5a)  # table header background
C_TABLE_BODY  = (0x28, 0x28, 0x28)  # 7pt table body text
C_PAGENUM     = (0x96, 0x96, 0x96)  # 7pt page number (light gray)
C_TITLE_PAGE  = (0x00, 0x00, 0x00)  # 24pt main title
C_TITLE_SUB   = (0x64, 0x64, 0x64)  # 14pt English subtitle
C_TITLE_INFO  = (0x1e, 0x32, 0x50)  # 13pt info line
C_TRANSLATION = (0x28, 0x3c, 0x5a)  # translation text color (matches section headers)
C_OVERVIEW_JP = (0x3c, 0x1e, 0x1e)  # overview Japanese (body color)
C_OVERVIEW_CN = (0x64, 0x64, 0x64)  # overview Chinese (gray note color)

# Font sizes
FS_TITLE      = 24.0
FS_TITLE_SUB  = 20.0
FS_TITLE_EN   = 14.0
FS_TITLE_INFO = 13.0
FS_TITLE_DESC = 10.0
FS_CHAPTER    = 17.0
FS_CHAPTER_SUB = 10.0
FS_SECTION    = 12.0
FS_BODY       = 8.5
FS_KEYPOINT   = 8.5
FS_EXAM       = 8.5
FS_CAPTION    = 8.0
FS_NOTE       = 7.0
FS_TABLE_HDR  = 7.5
FS_TABLE_BODY = 7.0
FS_PAGENUM    = 7.0

# Layout
LH_BODY       = 5.5   # line height for body text
LH_TABLE      = 5.5   # line height for table cells


class ReviewPDF(FPDF):
    """Custom PDF with CJK font and SE guide-aligned styling."""

    def __init__(self, language="bilingual"):
        super().__init__()
        self.language = language
        self.font_reg = None
        self._register_fonts()
        self.set_auto_page_break(True, margin=15)

    def _register_fonts(self):
        """Register CJK fonts. Prefer SimSun, fallback to NotoSansSC."""
        font_dir = Path("fonts")

        # Try system SimSun first (Windows CJK), then bundled fonts
        candidates = [
            font_dir / "NotoSansSC-Regular.ttf",
            font_dir / "NotoSansJP-Regular.ttf",
        ]
        candidates_bold = [
            font_dir / "NotoSansSC-Bold.ttf",
            font_dir / "NotoSansJP-Bold.ttf",
        ]

        regular = None
        for c in candidates:
            if c.exists():
                regular = c
                break
        bold = None
        for c in candidates_bold:
            if c.exists():
                bold = c
                break

        if regular:
            self.add_font("CJK", fname=str(regular))
            self.font_reg = "CJK"
        else:
            self.font_reg = "Helvetica"

        if bold:
            self.add_font("CJK", style="B", fname=str(bold))
        else:
            self.font_reg = "Helvetica"

    # ---------- helpers ----------
    def _w(self):
        return self.w - 2 * self.l_margin

    def _set_font(self, style="", size=FS_BODY):
        if self.font_reg:
            self.set_font(self.font_reg, style, size)

    def _set_color(self, rgb):
        self.set_text_color(*rgb)

    def _paragraph(self, text, size=FS_BODY, color=None, lh=None, keywords=None):
        """Render paragraph. If keywords list provided, bold those terms inline."""
        if color:
            self._set_color(color)
        h = lh if lh else LH_BODY

        if keywords:
            # Split text around keywords and render inline with bold
            self._render_with_keywords(text, keywords, size, h)
        else:
            self._set_font("", size)
            self.multi_cell(self._w(), h, text, align="L")

    def _render_with_keywords(self, text, keywords, size, lh):
        """Render text normally, with a keyword tag line before it in bold."""
        # Render keyword tags if present
        if keywords:
            tag_line = "【关键词 / Keywords】 " + "  ·  ".join(keywords)
            self._set_font("B", FS_NOTE)
            self._set_color(C_KEYPOINT)
            self.multi_cell(self._w(), LH_BODY, tag_line, align="L")
            self.ln(1)
        # Render main text normally
        self._set_font("", size)
        self._set_color(C_BODY)
        self.multi_cell(self._w(), lh, text, align="L")

    def _bold_paragraph(self, text, size=FS_BODY, color=None, lh=None):
        if color:
            self._set_color(color)
        self._set_font("B", size)
        h = lh if lh else LH_BODY
        self.multi_cell(self._w(), h, text, align="L")

    # ---------- block renderers ----------

    def render_heading(self, block):
        level = block.get("level", 1)
        if level == 1:
            self.ln(6)
            self._set_font("B", FS_CHAPTER)
            self._set_color(C_TITLE)
            self.multi_cell(self._w(), 9, block["text"], align="L")
            self.ln(2)
        elif level == 2:
            self.ln(4)
            self._set_font("B", FS_SECTION)
            self._set_color(C_SECTION)
            self.multi_cell(self._w(), 7, block["text"], align="L")
            self.ln(1)
        else:
            self._set_color(C_BODY)
            self._bold_paragraph(block["text"], FS_BODY, C_BODY)

    def render_text(self, block):
        color = C_BODY
        if block.get("style") == "note":
            color = C_NOTE
        self._paragraph(block["content"], block.get("size", FS_BODY), color)

    def render_image(self, block):
        img_path = Path("output/images") / block["file"]
        if not img_path.exists():
            self._paragraph(f"[Image not found: {block['file']}]", FS_NOTE, C_NOTE)
            return

        self.ln(2)
        max_w = self._w() * 0.9
        max_h = 100

        try:
            from PIL import Image
            with Image.open(img_path) as im:
                img_w, img_h = im.size
        except Exception:
            img_w, img_h = 300, 200

        scale = min(max_w / (img_w * 0.2646), max_h / (img_h * 0.2646), 1.0)
        disp_w = img_w * 0.2646 * scale

        x = self.l_margin + (self._w() - disp_w) / 2
        self.image(str(img_path), x=x, w=disp_w)

        if block.get("caption"):
            self.ln(2)
            self._set_font("", FS_CAPTION)
            self._set_color(C_CAPTION)
            self.cell(self._w(), 5, block["caption"], align="C")
        self.ln(3)

    def render_term_table(self, block):
        """Render terminology table in SE guide style: dark header + light body."""
        self.ln(2)
        cols = block.get("columns", ["日语", "读音", "中文", "说明"])
        col_widths = block.get("col_widths", [50, 30, 35, self._w() - 115])
        rows = block.get("rows", [])

        # Header row — dark background, white text
        self._set_font("B", FS_TABLE_HDR)
        self._set_color(C_TABLE_HDR)
        self.set_fill_color(*C_TABLE_BG)
        for i, col in enumerate(cols):
            self.cell(col_widths[i], 6, col, border=0, fill=True, align="C")
        self.ln()

        # Data rows
        self._set_font("", FS_TABLE_BODY)
        self._set_color(C_TABLE_BODY)
        alt = False
        for row in rows:
            if alt:
                self.set_fill_color(248, 248, 252)
            else:
                self.set_fill_color(255, 255, 255)
            alt = not alt

            # Calculate row height
            max_lines = 1
            for i, ct in enumerate(row):
                if i >= len(col_widths):
                    break
                text_w = self.get_string_width(str(ct))
                lines = max(1, int(text_w / (col_widths[i] - 1)) + 1)
                max_lines = max(max_lines, lines)
            row_h = max(5, LH_TABLE * max_lines)

            y_before = self.get_y()
            x_start = self.get_x()
            for i, ct in enumerate(row):
                if i >= len(col_widths):
                    break
                self.set_xy(x_start + sum(col_widths[:i]), y_before)
                if y_before + row_h > self.h - self.b_margin:
                    self.add_page()
                    y_before = self.get_y()
                self.multi_cell(col_widths[i], LH_TABLE, str(ct), border=0, align="L", fill=True)
            self.set_y(y_before + row_h)

    def _draw_divider(self):
        """Light horizontal separator line."""
        self.ln(2)
        self.set_draw_color(200, 200, 210)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(2)

    def render_concept_card(self, block):
        """Render concept card: JP/CN interleaved, CN with bg+border, keywords tag."""
        title = block.get("title", "")
        if title:
            self.ln(1)
            importance = block.get("importance", "")
            stars = ""
            if importance:
                stars = "★" * importance + " "
            self._set_font("B", FS_SECTION)
            self._set_color(C_SECTION)
            self.multi_cell(self._w(), 7, f"{title} {stars}", align="L")
            self.ln(1)

        # Keywords tag line (once at top)
        keywords = block.get("keywords", None)
        if keywords:
            self._set_font("B", FS_NOTE)
            self._set_color(C_KEYPOINT)
            kw_tag = "【Keywords】 " + "  ·  ".join(keywords)
            self.multi_cell(self._w(), LH_BODY, kw_tag, align="L")
            self.ln(2)

        # Interleaved bilingual paragraphs
        if block.get("content") or block.get("translation"):
            jp_paras = block.get("content", "").split("\n\n")
            cn_paras = block.get("translation", "").split("\n\n")

            max_len = max(len(jp_paras), len(cn_paras))
            while len(jp_paras) < max_len:
                jp_paras.append("")
            while len(cn_paras) < max_len:
                cn_paras.append("")

            for i in range(max_len):
                jp = jp_paras[i].strip()
                cn = cn_paras[i].strip()

                if jp:
                    self._paragraph(jp, FS_BODY, C_BODY)

                if cn:
                    if jp:
                        self.ln(1)
                    # Scheme B: bg + left border for translation
                    y0 = self.get_y()
                    self.set_fill_color(0xf0, 0xf4, 0xfa)
                    self.set_draw_color(0x28, 0x3c, 0x5a)
                    self.set_line_width(0.6)
                    self._set_font("", FS_BODY)
                    self._set_color(C_TRANSLATION)
                    self.set_x(self.l_margin + 7)
                    self.multi_cell(self._w() - 7, LH_BODY, cn, align="L", fill=True)
                    y1 = self.get_y()
                    # Left border bar (2mm wide, ~2mm gap to bg)
                    self.set_fill_color(0x28, 0x3c, 0x5a)
                    self.rect(self.l_margin, y0, 2, y1 - y0, "F")
                    self.ln(2)

                if jp or cn:
                    self.ln(1)

        # Exam highlight
        if block.get("exam_tip"):
            self.ln(1)
            self._set_font("", FS_EXAM)
            self._set_color(C_EXAM)
            self.multi_cell(self._w(), LH_BODY, block["exam_tip"], align="L")

        # Key point
        if block.get("key_point"):
            self.ln(1)
            self._set_font("B", FS_KEYPOINT)
            self._set_color(C_KEYPOINT)
            self.multi_cell(self._w(), LH_BODY, block["key_point"], align="L")

        # Example
        if block.get("example"):
            self.ln(1)
            self._paragraph(block["example"], FS_NOTE, C_NOTE)

    def render_highlight_box(self, block):
        """Render exam/important highlight in SE guide style — red text on white, no background box."""
        self.ln(2)
        box_type = block.get("box_type", "warning")
        if box_type == "danger" or box_type == "warning":
            color = C_EXAM
        elif box_type == "info":
            color = C_KEYPOINT
        else:
            color = C_NOTE

        label = block.get("label", "")
        content = block.get("content", "")
        text = f"{label}\n{content}" if label else content

        self._set_font("", FS_EXAM)
        self._set_color(color)
        self.multi_cell(self._w(), LH_BODY, text, align="L")
        self.ln(1)

    def render_exam_stat(self, block):
        self._set_font("B", FS_SECTION)
        self._set_color(C_SECTION)
        self.multi_cell(self._w(), 7, block.get("title", ""), align="L")
        self.ln(2)

        items = block.get("items", [])
        if block.get("stat_type") == "distribution":
            self._set_font("B", FS_TABLE_HDR)
            self._set_color(C_TABLE_HDR)
            self.set_fill_color(*C_TABLE_BG)
            col_w = self._w() / 3
            self.cell(col_w, 6, "题型", border=0, fill=True, align="C")
            self.cell(col_w, 6, "分值", border=0, fill=True, align="C")
            self.cell(col_w, 6, "占比", border=0, fill=True, align="C")
            self.ln()
            self._set_font("", FS_TABLE_BODY)
            self._set_color(C_TABLE_BODY)
            for item in items:
                self.cell(col_w, 5, item.get("type", ""), border=0, align="C")
                self.cell(col_w, 5, str(item.get("score", "")), border=0, align="C")
                self.cell(col_w, 5, str(item.get("ratio", "")), border=0, align="C")
                self.ln()
        else:
            for item in items:
                self._paragraph(f"  {item}", FS_BODY, C_BODY)
        self.ln(2)


def generate_pdf(content_json_path, output_path, language="bilingual"):
    with open(content_json_path, "r", encoding="utf-8") as f:
        document = json.load(f)

    pdf = ReviewPDF(language=language)
    pdf.set_left_margin(18)
    pdf.set_right_margin(18)

    # ===== Title page =====
    pdf.add_page()
    pdf.ln(25)
    # Main title
    pdf._set_font("B", FS_TITLE)
    pdf._set_color(C_TITLE_PAGE)
    title = document.get("title", "")
    pdf.multi_cell(pdf._w(), 14, title, align="C")
    pdf.ln(4)
    # Subtitle
    subtitle = document.get("subtitle", "")
    if subtitle:
        pdf._set_font("", FS_TITLE_SUB)
        pdf._set_color(C_TITLE_PAGE)
        pdf.multi_cell(pdf._w(), 11, subtitle, align="C")
        pdf.ln(6)
    # English / description
    pdf._set_font("", FS_TITLE_EN)
    pdf._set_color(C_TITLE_SUB)
    pdf.multi_cell(pdf._w(), 8, "Computer Networks", align="C")
    pdf.ln(2)
    # Info line
    pdf._set_font("", FS_TITLE_INFO)
    pdf._set_color(C_TITLE_INFO)
    pdf.cell(pdf._w(), 7, "期末試験対策·復習ガイド（期末考试复习指南）", align="C")
    pdf.ln(12)
    # Description
    pdf._set_font("", FS_TITLE_DESC)
    pdf._set_color(C_NOTE)
    desc = "全8章PPT内容 | 中日対照 | 試験重点付き"
    pdf.cell(pdf._w(), 6, desc, align="C")

    # ===== Content sections =====
    for section in document.get("sections", []):
        pdf.add_page()

        # Chapter title (17pt dark navy)
        section_title = section.get("title", "")
        pdf._set_font("B", FS_CHAPTER)
        pdf._set_color(C_TITLE)
        pdf.multi_cell(pdf._w(), 9, section_title, align="L")
        pdf.ln(2)

        # Section overview
        overview = section.get("overview", "")
        if overview:
            # Split overview into Japanese and Chinese parts (separated by \n\n)
            parts = overview.split("\n\n")
            for i, part in enumerate(parts):
                pdf.set_x(pdf.l_margin)  # force reset x before each paragraph
                if i == 0 and part.strip():
                    pdf._paragraph(part.strip(), FS_BODY, C_OVERVIEW_JP)
                elif part.strip():
                    pdf._paragraph(part.strip(), FS_NOTE, C_OVERVIEW_CN)
            pdf.ln(2)

        # Render blocks
        for block in section.get("blocks", []):
            block_type = block.get("type", "text")
            render_func = getattr(pdf, f"render_{block_type}", None)
            if render_func:
                render_func(block)
            else:
                pdf._paragraph(f"[Unknown block type: {block_type}]", FS_NOTE, C_NOTE)

    # ===== Footer: page numbers =====
    for page_num in range(1, pdf.page + 1):
        pdf.page = page_num
        pdf.set_y(-12)
        pdf._set_font("", FS_PAGENUM)
        pdf._set_color(C_PAGENUM)
        pdf.cell(0, 8, f"- {page_num} -", align="C")

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
