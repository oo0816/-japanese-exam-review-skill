"""Generate PDF review document from content JSON.
Styling based on the SE study guide design system.
"""
import json
import re
import sys
from pathlib import Path
from fpdf import FPDF

# === Design System: two visual presets ===
# jp_first: enhanced readability (stronger contrast, table borders, more spacing)
# chinese_annotated: SE guide original specs (subtle, compact, academic)

STYLES = {
    "jp_first": {
        "C_TITLE":       (0x1a, 0x3a, 0x5c),
        "C_SECTION":     (0x28, 0x3c, 0x5a),
        "C_BODY":        (0x22, 0x22, 0x22),
        "C_KEYPOINT":    (0x28, 0x32, 0x46),
        "C_EXAM":        (0xc8, 0x32, 0x32),
        "C_CAPTION":     (0x50, 0x50, 0x50),
        "C_NOTE":        (0x64, 0x64, 0x64),
        "C_TABLE_HDR":   (0xff, 0xff, 0xff),
        "C_TABLE_BG":    (0x28, 0x3c, 0x5a),
        "C_TABLE_BODY":  (0x22, 0x22, 0x22),
        "C_TABLE_ROW1":  (0xf2, 0xf5, 0xfa),
        "C_TABLE_ROW2":  (0xff, 0xff, 0xff),
        "C_TABLE_BORDER": (0xd0, 0xd5, 0xe0),
        "C_PAGENUM":     (0x96, 0x96, 0x96),
        "C_TITLE_PAGE":  (0x00, 0x00, 0x00),
        "C_TITLE_SUB":   (0x64, 0x64, 0x64),
        "C_TITLE_INFO":  (0x1e, 0x32, 0x50),
        "C_TRANSLATION": (0x1e, 0x50, 0x80),
        "C_OVERVIEW_JP": (0x22, 0x22, 0x22),
        "C_OVERVIEW_CN": (0x64, 0x64, 0x64),
        "C_TRANS_BG":    (0xed, 0xf2, 0xf8),
        "FS_TITLE":      24.0, "FS_TITLE_SUB": 20.0, "FS_TITLE_EN": 14.0,
        "FS_TITLE_INFO": 13.0, "FS_TITLE_DESC": 10.0,
        "FS_CHAPTER":    17.0, "FS_SECTION": 12.0,
        "FS_BODY":       8.5, "FS_KEYPOINT": 8.5, "FS_EXAM": 8.5,
        "FS_CAPTION":    8.0, "FS_NOTE": 7.0,
        "FS_TABLE_HDR":  7.5, "FS_TABLE_BODY": 7.0, "FS_PAGENUM": 7.0,
        "LH_BODY":       6.0, "LH_TABLE": 5.5,
        "MARGIN_LEFT":   16, "MARGIN_RIGHT": 17,
        "TABLE_BORDERED": True,
        "CARD_SPACING":  4,
        "CN_HAS_BG":     True,
    },
    "chinese_annotated": {
        "C_TITLE":       (0x1a, 0x3a, 0x5c),
        "C_SECTION":     (0x28, 0x3c, 0x5a),
        "C_BODY":        (0x32, 0x32, 0x32),  # SE guide original body color
        "C_ANNOTATION":  (0x1a, 0x6e, 0x5c),  # teal-green for (English / 日本語) annotations
        "C_KEYPOINT":    (0x28, 0x32, 0x46),
        "C_EXAM":        (0xc8, 0x32, 0x32),
        "C_CAPTION":     (0x50, 0x50, 0x50),
        "C_NOTE":        (0x64, 0x64, 0x64),
        "C_TABLE_HDR":   (0xff, 0xff, 0xff),
        "C_TABLE_BG":    (0x28, 0x3c, 0x5a),
        "C_TABLE_BODY":  (0x28, 0x28, 0x28),  # SE guide original table color
        "C_TABLE_ROW1":  (0xf8, 0xf8, 0xfc),  # SE guide subtle alt row
        "C_TABLE_ROW2":  (0xff, 0xff, 0xff),
        "C_TABLE_BORDER": (0xd0, 0xd5, 0xe0),
        "C_PAGENUM":     (0x96, 0x96, 0x96),
        "C_TITLE_PAGE":  (0x00, 0x00, 0x00),
        "C_TITLE_SUB":   (0x64, 0x64, 0x64),
        "C_TITLE_INFO":  (0x1e, 0x32, 0x50),
        "C_TRANSLATION": (0x28, 0x3c, 0x5a),  # SE guide navy (not used in cn mode)
        "C_OVERVIEW_JP": (0x32, 0x32, 0x32),
        "C_OVERVIEW_CN": (0x64, 0x64, 0x64),
        "C_TRANS_BG":    (0xf0, 0xf4, 0xfa),
        "FS_TITLE":      24.0, "FS_TITLE_SUB": 20.0, "FS_TITLE_EN": 14.0,
        "FS_TITLE_INFO": 13.0, "FS_TITLE_DESC": 10.0,
        "FS_CHAPTER":    17.0, "FS_SECTION": 12.0,
        "FS_BODY":       8.5, "FS_KEYPOINT": 8.5, "FS_EXAM": 8.5,
        "FS_CAPTION":    8.0, "FS_NOTE": 7.0,
        "FS_TABLE_HDR":  7.5, "FS_TABLE_BODY": 7.0, "FS_PAGENUM": 7.0,
        "LH_BODY":       6.0, "LH_TABLE": 5.5,
        "MARGIN_LEFT":   16, "MARGIN_RIGHT": 17,
        "TABLE_BORDERED": False,
        "CARD_SPACING":  2,
        "CN_HAS_BG":     False,
    },
}


class ReviewPDF(FPDF):
    """Custom PDF with CJK font. Visual preset selected by language mode."""

    def __init__(self, language="jp_first"):
        super().__init__()
        self.language = language
        self.s = STYLES.get(language, STYLES["jp_first"])
        self.font_reg = None
        self._register_fonts()
        self.set_auto_page_break(True, margin=15)

    def _c(self, name):
        """Get color from current style preset."""
        return self.s[f"C_{name}"]

    def _fs(self, name):
        """Get font size from current style preset."""
        return self.s[f"FS_{name}"]

    def _lh(self, name):
        """Get line height from current style preset."""
        return self.s[f"LH_{name}"]

    def _register_fonts(self):
        """Register CJK fonts: SimSun for Chinese body, NotoSansSC for Japanese terms.
        SimSun (宋体) gives the academic serif look; NotoSansSC covers JP kana fully.
        """
        font_dir = Path("fonts")

        # --- Chinese serif font (SimSun) ---
        cn_regular = font_dir / "simsun.ttc"
        cn_bold = font_dir / "simsunb.ttf"

        if cn_regular.exists():
            self.add_font("CN", fname=str(cn_regular))
            if cn_bold.exists():
                self.add_font("CN", style="B", fname=str(cn_bold))
            else:
                self.add_font("CN", style="B", fname=str(cn_regular))
        else:
            # Fallback to NotoSansSC
            cn_regular = None

        # --- Japanese sans-serif font (NotoSansSC) ---
        jp_regular = None
        for c in [font_dir / "NotoSansSC-Regular.ttf", font_dir / "NotoSansJP-Regular.ttf"]:
            if c.exists():
                jp_regular = c
                break

        jp_bold = None
        for c in [font_dir / "NotoSansSC-Bold.ttf", font_dir / "NotoSansJP-Bold.ttf"]:
            if c.exists():
                jp_bold = c
                break

        if jp_regular:
            self.add_font("JP", fname=str(jp_regular))
            if jp_bold:
                self.add_font("JP", style="B", fname=str(jp_bold))
            else:
                self.add_font("JP", style="B", fname=str(jp_regular))

        # Set default font
        self.font_cn = "CN" if cn_regular and cn_regular.exists() else ("JP" if jp_regular else "Helvetica")
        self.font_jp = "JP" if jp_regular else "Helvetica"

    def _use_cn(self, bold=False):
        """Switch to Chinese serif font (SimSun)."""
        self.set_font(self.font_cn, "B" if bold else "")

    def _use_jp(self, bold=False):
        """Switch to Japanese font (NotoSansSC)."""
        self.set_font(self.font_jp, "B" if bold else "")

    # ---------- helpers ----------
    def _w(self):
        return self.w - 2 * self.l_margin

    def _set_font(self, style="", size=None):
        """Set primary font: CN (SimSun) for chinese_annotated, JP (NotoSansSC) for jp_first."""
        if size is None:
            size = self._fs("BODY")
        if self.language == "chinese_annotated":
            self.set_font(self.font_cn, style, size)
        else:
            self.set_font(self.font_jp, style, size)

    def _set_font_jp(self, style="", size=None):
        """Set JP font (NotoSansSC) — for kana-rich Japanese text in any mode."""
        if size is None:
            size = self._fs("BODY")
        self.set_font(self.font_jp, style, size)

    def _set_color(self, rgb):
        self.set_text_color(*rgb)

    def _fix_simsun(self, text):
        """Replace characters missing from SimSun (U+30FB ・→·)"""
        if self.language == "chinese_annotated":
            return text.replace('・', '·')
        return text

    def multi_cell(self, w=None, h=None, text="", border=0, align="L", fill=False, **kwargs):
        """Override multi_cell to fix SimSun-incompatible chars."""
        super().multi_cell(w, h, self._fix_simsun(text), border, align, fill, **kwargs)

    def write(self, h=None, text="", link="", **kwargs):
        """Override write to fix SimSun-incompatible chars."""
        super().write(h, self._fix_simsun(text), link, **kwargs)

    def cell(self, w=None, h=None, text="", border=0, ln=0, align="", fill=False, **kwargs):
        """Override cell to fix SimSun-incompatible chars."""
        super().cell(w, h, self._fix_simsun(text), border, ln, align, fill, **kwargs)

    def _paragraph(self, text, size=None, color=None, lh=None, keywords=None):
        """Render paragraph. If keywords list provided, bold those terms inline."""
        if size is None:
            size = self._fs("BODY")
        text = self._fix_simsun(text)
        if color:
            self._set_color(color)
        h = lh if lh else self._lh("BODY")

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
            self._set_font("B", self._fs("NOTE"))
            self._set_color(self._c("KEYPOINT"))
            self.multi_cell(self._w(), self._lh("BODY"), tag_line, align="L")
            self.ln(1)
        # Render main text normally
        self._set_font("", size)
        self._set_color(self._c("BODY"))
        self.multi_cell(self._w(), lh, text, align="L")

    def _annotated_paragraph(self, text, size=None, lh=None):
        """Render body text with colored (English / 日本語) annotations inline.
        Uses write() for inline color switching on annotation patterns."""
        import re
        if size is None:
            size = self._fs("BODY")
        h = lh if lh else self._lh("BODY")

        # Split text at （English / 日本語） patterns
        # Pattern: full-width parens containing chars + / + chars
        pattern = r'(（[^）]*?/[^）]*?）)'
        parts = re.split(pattern, text)

        self._set_font("", size)
        x_start = self.get_x()
        for part in parts:
            if not part:
                continue
            # Check if this part is an annotation
            if re.match(r'^（[^）]*?/[^）]*?）$', part):
                self._set_color(self._c("ANNOTATION"))
            else:
                self._set_color(self._c("BODY"))
            self.write(h, part)

    def _annotated_multi_cell(self, text, size=None, lh=None):
        """Render body text with annotations colored, using multi_cell for line wrapping.
        Handles long paragraphs that need to wrap across lines."""
        if size is None:
            size = self._fs("BODY")
        h = lh if lh else self._lh("BODY")

        text = self._fix_simsun(text)

        pattern = r'(（[^）]*?/[^）]*?）)'
        segments = re.split(pattern, text)

        self._set_font("", size)

        # Build the line word-by-word, switching colors for annotation segments
        w = self._w()
        line = ""
        for seg in segments:
            if not seg:
                continue
            is_anno = bool(re.match(r'^（[^）]*?/[^）]*?）$', seg))

            # Try to fit segment on current line
            test_line = line + seg
            if self.get_string_width(test_line) > w and line:
                # Flush current line
                self._set_color(self._c("BODY"))
                # Render line with mixed segments
                self._render_mixed_line(line, h, pattern)
                line = seg
            else:
                line = test_line

        # Flush remaining
        if line:
            self._render_mixed_line(line, h, pattern)
        self.ln(h)

    def _render_mixed_line(self, line, h, pattern):
        """Render a single line with mixed body/annotation colors."""
        segments = re.split(pattern, line)
        for seg in segments:
            if not seg:
                continue
            if re.match(r'^（[^）]*?/[^）]*?）$', seg):
                self._set_color(self._c("ANNOTATION"))
            else:
                self._set_color(self._c("BODY"))
            self.write(h, seg)
        self.ln(h)

    def _bold_paragraph(self, text, size=None, color=None, lh=None):
        if size is None:
            size = self._fs("BODY")
        if color:
            self._set_color(color)
        self._set_font("B", size)
        h = lh if lh else self._lh("BODY")
        self.multi_cell(self._w(), h, text, align="L")

    # ---------- block renderers ----------

    def render_heading(self, block):
        level = block.get("level", 1)
        if level == 1:
            self.ln(6)
            self._set_font("B", self._fs("CHAPTER"))
            self._set_color(self._c("TITLE"))
            self.multi_cell(self._w(), 9, block["text"], align="L")
            self.ln(2)
        elif level == 2:
            self.ln(4)
            self._set_font("B", self._fs("SECTION"))
            self._set_color(self._c("SECTION"))
            self.multi_cell(self._w(), 7, block["text"], align="L")
            self.ln(1)
        else:
            self._set_color(self._c("BODY"))
            self._bold_paragraph(block["text"], self._fs("BODY"), self._c("BODY"))

    def render_text(self, block):
        color = self._c("BODY")
        if block.get("style") == "note":
            color = self._c("NOTE")
        self._paragraph(block["content"], block.get("size", self._fs("BODY")), color)

    def render_image(self, block):
        img_path = Path("output/images") / block["file"]
        if not img_path.exists():
            self._paragraph(f"[Image not found: {block['file']}]", self._fs("NOTE"), self._c("NOTE"))
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
            self._set_font("", self._fs("CAPTION"))
            self._set_color(self._c("CAPTION"))
            self.cell(self._w(), 5, block["caption"], align="C")
        self.ln(3)

    def render_term_table(self, block):
        """Render table with visible borders, strong alternating rows, dark header."""
        self.ln(3)
        cols = block.get("columns", ["日语", "读音", "中文", "说明"])
        col_widths = block.get("col_widths", [50, 30, 35, self._w() - 115])
        rows = block.get("rows", [])

        border_color = self._c("TABLE_BORDER")

        # Header row — dark navy bg, white bold text (JP font for kana-rich headers)
        self._set_font_jp("B", self._fs("TABLE_HDR"))
        self._set_color(self._c("TABLE_HDR"))
        self.set_fill_color(*self._c("TABLE_BG"))
        self.set_draw_color(*border_color)
        for i, col in enumerate(cols):
            self.cell(col_widths[i], 6, " " + col, border=1, fill=True, align="C")
        self.ln()

        # Data rows — JP font for kana-rich Japanese terms
        self._set_font_jp("", self._fs("TABLE_BODY"))
        alt = False
        for row in rows:
            if alt:
                self.set_fill_color(*self._c("TABLE_ROW1"))
            else:
                self.set_fill_color(*self._c("TABLE_ROW2"))
            alt = not alt
            self._set_color(self._c("TABLE_BODY"))
            self.set_draw_color(*border_color)

            # Calculate row height
            max_lines = 1
            for i, ct in enumerate(row):
                if i >= len(col_widths):
                    break
                text_w = self.get_string_width(str(ct))
                lines = max(1, int(text_w / (col_widths[i] - 1.5)) + 1)
                max_lines = max(max_lines, lines)
            row_h = max(6, self._lh("TABLE") * max_lines)

            y_before = self.get_y()
            x_start = self.get_x()
            for i, ct in enumerate(row):
                if i >= len(col_widths):
                    break
                self.set_xy(x_start + sum(col_widths[:i]), y_before)
                if y_before + row_h > self.h - self.b_margin:
                    self.add_page()
                    y_before = self.get_y()
                    self._set_color(self._c("TABLE_BODY"))
                    self.set_draw_color(*border_color)
                self.multi_cell(col_widths[i], self._lh("TABLE"), " " + str(ct), border="LR", align="L", fill=True)
            self.set_y(y_before + row_h)

        # Bottom border line
        self.set_draw_color(*border_color)
        self.line(self.l_margin, self.get_y(), self.l_margin + sum(col_widths), self.get_y())
        self.ln(3)

    def render_concept_card(self, block):
        """Render concept card: JP/CN interleaved, CN with bg+border, keywords tag."""
        title = block.get("title", "")
        if title:
            self.ln(4)
            importance = block.get("importance", "")
            stars = ""
            if importance:
                stars = "★" * importance + " "
            self._set_font("B", self._fs("SECTION"))
            self._set_color(self._c("SECTION"))
            self.multi_cell(self._w(), 7, f"{title} {stars}", align="L")
            self.ln(1)

        # Keywords tag line (once at top)
        keywords = block.get("keywords", None)
        if keywords:
            self._set_font("B", self._fs("NOTE"))
            self._set_color(self._c("KEYPOINT"))
            kw_tag = "【Keywords】 " + "  ·  ".join(keywords)
            self.multi_cell(self._w(), self._lh("BODY"), kw_tag, align="L")
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
                    if self.language == "chinese_annotated":
                        self._annotated_multi_cell(jp, self._fs("BODY"), self._lh("BODY"))
                    else:
                        self._paragraph(jp, self._fs("BODY"), self._c("BODY"))

                if cn:
                    if jp:
                        self.ln(1)
                    # Light blue bg for translation (no left bar)
                    self.set_fill_color(*self._c("TRANS_BG"))
                    self._set_font("", self._fs("BODY"))
                    self._set_color(self._c("TRANSLATION"))
                    self.set_x(self.l_margin)
                    self.multi_cell(self._w(), self._lh("BODY"), cn, align="L", fill=True)
                    self.ln(2)

                if jp or cn:
                    self.ln(1)

        # Exam highlight
        if block.get("exam_tip"):
            self.ln(1)
            self._set_font("", self._fs("EXAM"))
            self._set_color(self._c("EXAM"))
            self.multi_cell(self._w(), self._lh("BODY"), block["exam_tip"], align="L")

        # Key point
        if block.get("key_point"):
            self.ln(1)
            self._set_font("B", self._fs("KEYPOINT"))
            self._set_color(self._c("KEYPOINT"))
            self.multi_cell(self._w(), self._lh("BODY"), block["key_point"], align="L")

        # Example
        if block.get("example"):
            self.ln(1)
            self._paragraph(block["example"], self._fs("NOTE"), self._c("NOTE"))

    def render_highlight_box(self, block):
        """Render exam/important highlight in SE guide style — red text on white, no background box."""
        self.ln(2)
        box_type = block.get("box_type", "warning")
        if box_type == "danger" or box_type == "warning":
            color = self._c("EXAM")
        elif box_type == "info":
            color = self._c("KEYPOINT")
        else:
            color = self._c("NOTE")

        label = block.get("label", "")
        content = block.get("content", "")
        text = f"{label}\n{content}" if label else content

        self._set_font("", self._fs("EXAM"))
        self._set_color(color)
        self.multi_cell(self._w(), self._lh("BODY"), text, align="L")
        self.ln(1)

    def render_exam_stat(self, block):
        self._set_font("B", self._fs("SECTION"))
        self._set_color(self._c("SECTION"))
        self.multi_cell(self._w(), 7, block.get("title", ""), align="L")
        self.ln(2)

        items = block.get("items", [])
        if block.get("stat_type") == "distribution":
            self._set_font("B", self._fs("TABLE_HDR"))
            self._set_color(self._c("TABLE_HDR"))
            self.set_fill_color(*self._c("TABLE_BG"))
            col_w = self._w() / 3
            self.cell(col_w, 6, "题型", border=0, fill=True, align="C")
            self.cell(col_w, 6, "分值", border=0, fill=True, align="C")
            self.cell(col_w, 6, "占比", border=0, fill=True, align="C")
            self.ln()
            self._set_font("", self._fs("TABLE_BODY"))
            self._set_color(self._c("TABLE_BODY"))
            for item in items:
                self.cell(col_w, 5, item.get("type", ""), border=0, align="C")
                self.cell(col_w, 5, str(item.get("score", "")), border=0, align="C")
                self.cell(col_w, 5, str(item.get("ratio", "")), border=0, align="C")
                self.ln()
        else:
            for item in items:
                self._paragraph(f"  {item}", self._fs("BODY"), self._c("BODY"))
        self.ln(2)


def generate_pdf(content_json_path, output_path, language="bilingual"):
    with open(content_json_path, "r", encoding="utf-8") as f:
        document = json.load(f)

    pdf = ReviewPDF(language=language)
    pdf.set_left_margin(16)
    pdf.set_right_margin(17)

    # ===== Title page =====
    pdf.add_page()
    pdf.ln(25)
    # Main title
    pdf._set_font("B", pdf._fs("TITLE"))
    pdf._set_color(pdf._c("TITLE_PAGE"))
    title = document.get("title", "")
    pdf.multi_cell(pdf._w(), 14, title, align="C")
    pdf.ln(4)
    # Subtitle
    subtitle = document.get("subtitle", "")
    if subtitle:
        pdf._set_font("", pdf._fs("TITLE_SUB"))
        pdf._set_color(pdf._c("TITLE_PAGE"))
        pdf.multi_cell(pdf._w(), 11, subtitle, align="C")
        pdf.ln(6)
    # English / description
    pdf._set_font("", pdf._fs("TITLE_EN"))
    pdf._set_color(pdf._c("TITLE_SUB"))
    pdf.multi_cell(pdf._w(), 8, "Computer Networks", align="C")
    pdf.ln(2)
    # Info line
    pdf._set_font("", pdf._fs("TITLE_INFO"))
    pdf._set_color(pdf._c("TITLE_INFO"))
    pdf.cell(pdf._w(), 7, "期末試験対策·復習ガイド（期末考试复习指南）", align="C")
    pdf.ln(12)
    # Description
    pdf._set_font("", pdf._fs("TITLE_DESC"))
    pdf._set_color(pdf._c("NOTE"))
    desc = "全8章PPT内容 | 中日対照 | 試験重点付き"
    pdf.cell(pdf._w(), 6, desc, align="C")

    # ===== Content sections =====
    for section in document.get("sections", []):
        pdf.add_page()

        # Chapter title (17pt dark navy)
        section_title = section.get("title", "")
        pdf._set_font("B", pdf._fs("CHAPTER"))
        pdf._set_color(pdf._c("TITLE"))
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
                    # JP overview: use JP font for kana safety
                    pdf._set_font_jp("", pdf._fs("BODY"))
                    pdf._set_color(pdf._c("OVERVIEW_JP"))
                    pdf.multi_cell(pdf._w(), pdf._lh("BODY"), pdf._fix_simsun(part.strip()), align="L")
                elif part.strip():
                    pdf._paragraph(part.strip(), pdf._fs("NOTE"), pdf._c("OVERVIEW_CN"))
            pdf.ln(2)

        # Render blocks
        for block in section.get("blocks", []):
            block_type = block.get("type", "text")
            render_func = getattr(pdf, f"render_{block_type}", None)
            if render_func:
                render_func(block)
            else:
                pdf._paragraph(f"[Unknown block type: {block_type}]", pdf._fs("NOTE"), pdf._c("NOTE"))

    # ===== Footer: page numbers =====
    for page_num in range(1, pdf.page + 1):
        pdf.page = page_num
        pdf.set_y(-12)
        pdf._set_font("", pdf._fs("PAGENUM"))
        pdf._set_color(pdf._c("PAGENUM"))
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
                        choices=["jp_first", "chinese_annotated"],
                        help="Output language preference")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: input file not found: {args.input}")
        sys.exit(1)

    result = generate_pdf(args.input, args.output, args.language)
    print(f"PDF generated: {result}")


if __name__ == "__main__":
    main()
