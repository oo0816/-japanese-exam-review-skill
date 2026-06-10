"""Generate PDF review document from content JSON.
Uses reportlab for reliable CJK font rendering.
"""
import json
import re
import sys
from pathlib import Path
from fontTools.ttLib import TTCollection

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, PageBreak, KeepTogether)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Resolve font dir relative to project root (scripts/ -> skill/ -> skills/ -> .claude/ -> root/)
_SCRIPT_DIR = Path(__file__).resolve().parent
FONT_DIR = _SCRIPT_DIR.parent.parent.parent.parent / "fonts"
if not FONT_DIR.exists():
    FONT_DIR = Path(r"D:\作业\计算机网络\计网\fonts")

# Font family names used in ParagraphStyle (keep short, reportlab ps2tt parses them)
FONT_JP = 'NS'
FONT_JP_BOLD = 'NSB'
FONT_CN = 'SS'

# === Design System ===
STYLES = {
    "jp_first": {
        "C_TITLE":       "#1a3a5c",
        "C_SECTION":     "#283c5a",
        "C_BODY":        "#222222",
        "C_KEYPOINT":    "#283246",
        "C_EXAM":        "#c83232",
        "C_CAPTION":     "#505050",
        "C_NOTE":        "#646464",
        "C_TABLE_HDR":   "#ffffff",
        "C_TABLE_BG":    "#283c5a",
        "C_TABLE_BODY":  "#222222",
        "C_TABLE_ROW1":  "#f2f5fa",
        "C_TABLE_ROW2":  "#ffffff",
        "C_TABLE_BORDER":"#d0d5e0",
        "C_PAGENUM":     "#969696",
        "C_TITLE_PAGE":  "#000000",
        "C_TITLE_SUB":   "#646464",
        "C_TITLE_INFO":  "#1e3250",
        "C_TRANSLATION": "#1e5080",
        "C_OVERVIEW_JP": "#222222",
        "C_OVERVIEW_CN": "#646464",
        "C_TRANS_BG":    "#edf2f8",
        "FS_TITLE":      24, "FS_TITLE_SUB": 20, "FS_TITLE_EN": 14,
        "FS_TITLE_INFO": 13, "FS_TITLE_DESC": 10,
        "FS_CHAPTER":    17, "FS_SECTION": 12,
        "FS_BODY":       8.5, "FS_KEYPOINT": 8.5, "FS_EXAM": 8.5,
        "FS_CAPTION":    8, "FS_NOTE": 7,
        "FS_TABLE_HDR":  7.5, "FS_TABLE_BODY": 7, "FS_PAGENUM": 7,
        "LH_BODY":       13, "LH_TABLE": 11,
        "CN_HAS_BG":     True,
    },
    "chinese_annotated": {
        "C_TITLE":       "#1a3a5c",
        "C_SECTION":     "#283c5a",
        "C_BODY":        "#323232",
        "C_ANNOTATION":  "#1a7a5c",
        "C_KEYPOINT":    "#283246",
        "C_EXAM":        "#c83232",
        "C_CAPTION":     "#505050",
        "C_NOTE":        "#646464",
        "C_TABLE_HDR":   "#ffffff",
        "C_TABLE_BG":    "#283c5a",
        "C_TABLE_BODY":  "#282828",
        "C_TABLE_ROW1":  "#f8f8fc",
        "C_TABLE_ROW2":  "#ffffff",
        "C_TABLE_BORDER":"#d0d5e0",
        "C_PAGENUM":     "#969696",
        "C_TITLE_PAGE":  "#000000",
        "C_TITLE_SUB":   "#646464",
        "C_TITLE_INFO":  "#1e3250",
        "C_TRANSLATION": "#283c5a",
        "C_OVERVIEW_JP": "#323232",
        "C_OVERVIEW_CN": "#646464",
        "C_TRANS_BG":    "#f0f4fa",
        "FS_TITLE":      24, "FS_TITLE_SUB": 20, "FS_TITLE_EN": 14,
        "FS_TITLE_INFO": 13, "FS_TITLE_DESC": 10,
        "FS_CHAPTER":    17, "FS_SECTION": 12,
        "FS_BODY":       8.5, "FS_KEYPOINT": 8.5, "FS_EXAM": 8.5,
        "FS_CAPTION":    8, "FS_NOTE": 7,
        "FS_TABLE_HDR":  7.5, "FS_TABLE_BODY": 7, "FS_PAGENUM": 7,
        "LH_BODY":       13, "LH_TABLE": 11,
        "CN_HAS_BG":     False,
    },
}


def _register_fonts():
    """Register CJK fonts with reportlab. Also patch _ps2tt_map so that
    <font face="..."> and <b>/<i> XML tags work with custom fonts."""
    from reportlab.lib import fonts as _rl_fonts

    ns_regular = FONT_DIR / "NotoSansSC-Regular.ttf"
    ns_bold = FONT_DIR / "NotoSansSC-Bold.ttf"
    if ns_regular.exists():
        pdfmetrics.registerFont(TTFont(FONT_JP, str(ns_regular)))
        _rl_fonts._ps2tt_map[FONT_JP.lower()] = (FONT_JP.lower(), 0, 0)
    if ns_bold.exists():
        pdfmetrics.registerFont(TTFont(FONT_JP_BOLD, str(ns_bold)))
        _rl_fonts._ps2tt_map[FONT_JP_BOLD.lower()] = (FONT_JP_BOLD.lower(), 0, 0)
    elif ns_regular.exists():
        pdfmetrics.registerFont(TTFont(FONT_JP_BOLD, str(ns_regular)))
        _rl_fonts._ps2tt_map[FONT_JP_BOLD.lower()] = (FONT_JP_BOLD.lower(), 0, 0)

    simsun_ttf = FONT_DIR / "simsun_extracted.ttf"
    if not simsun_ttf.exists():
        simsun_ttc = FONT_DIR / "simsun.ttc"
        if simsun_ttc.exists():
            try:
                tt = TTCollection(str(simsun_ttc))
                tt[0].save(str(simsun_ttf))
            except Exception:
                pass
    if simsun_ttf.exists():
        pdfmetrics.registerFont(TTFont(FONT_CN, str(simsun_ttf)))
        _rl_fonts._ps2tt_map[FONT_CN.lower()] = (FONT_CN.lower(), 0, 0)


class ReviewPDFBuilder:
    """Build review PDF using reportlab platypus."""

    def __init__(self, language="jp_first"):
        self.language = language
        self.s = STYLES.get(language, STYLES["jp_first"])
        _register_fonts()
        self._build_styles()

    def _c(self, name):
        return self.s[f"C_{name}"]

    def _fs(self, name):
        return self.s[f"FS_{name}"]

    def _lh(self, name):
        return self.s[f"LH_{name}"]

    def _build_styles(self):
        """Create ParagraphStyle objects. Bold is handled via <b> tags, not bold font styles."""
        font_body = FONT_CN if self.language == 'chinese_annotated' else FONT_JP
        font_jp = FONT_JP
        c = self._c
        fs = self._fs
        lh = self._lh

        self.style_chapter = ParagraphStyle('Chapter',
            fontName=FONT_JP_BOLD, fontSize=fs('CHAPTER'), leading=fs('CHAPTER')*1.4,
            textColor=c('TITLE'), spaceAfter=4)

        self.style_section = ParagraphStyle('Section',
            fontName=FONT_JP_BOLD, fontSize=fs('SECTION'), leading=fs('SECTION')*1.4,
            textColor=c('SECTION'), spaceAfter=2)

        self.style_body = ParagraphStyle('Body',
            fontName=font_body, fontSize=fs('BODY'), leading=lh('BODY'),
            textColor=c('BODY'))

        self.style_body_jp = ParagraphStyle('BodyJP',
            fontName=font_jp, fontSize=fs('BODY'), leading=lh('BODY'),
            textColor=c('BODY'))

        self.style_translation = ParagraphStyle('Translation',
            fontName=font_jp, fontSize=fs('BODY'), leading=lh('BODY'),
            textColor=c('TRANSLATION'),
            backColor=c('TRANS_BG') if self.language == 'jp_first' else None)

        self.style_note = ParagraphStyle('Note',
            fontName=font_body, fontSize=fs('NOTE'), leading=fs('NOTE')*1.5,
            textColor=c('NOTE'))

        self.style_overview_jp = ParagraphStyle('OverviewJP',
            fontName=font_jp, fontSize=fs('BODY'), leading=lh('BODY'),
            textColor=c('OVERVIEW_JP'))

        self.style_overview_cn = ParagraphStyle('OverviewCN',
            fontName=font_body, fontSize=fs('NOTE'), leading=fs('NOTE')*1.5,
            textColor=c('OVERVIEW_CN'))

        self.style_caption = ParagraphStyle('Caption',
            fontName=font_jp, fontSize=fs('CAPTION'), leading=fs('CAPTION')*1.5,
            textColor=c('CAPTION'), alignment=TA_CENTER)

        self.style_exam = ParagraphStyle('Exam',
            fontName=font_body, fontSize=fs('EXAM'), leading=lh('BODY'),
            textColor=c('EXAM'))

        self.style_keypoint = ParagraphStyle('KeyPoint',
            fontName=font_jp, fontSize=fs('KEYPOINT'), leading=lh('BODY'),
            textColor=c('KEYPOINT'))

        self.style_keypoint_bold = ParagraphStyle('KeyPointBold',
            fontName=FONT_JP_BOLD, fontSize=fs('KEYPOINT'), leading=lh('BODY'),
            textColor=c('KEYPOINT'))

        self.style_keywords = ParagraphStyle('Keywords',
            fontName=FONT_JP_BOLD, fontSize=fs('NOTE'), leading=lh('BODY'),
            textColor=c('KEYPOINT'))

        self.style_title_main = ParagraphStyle('TitleMain',
            fontName=FONT_JP_BOLD, fontSize=fs('TITLE'), leading=fs('TITLE')*1.4,
            textColor=c('TITLE_PAGE'), alignment=TA_CENTER)

        self.style_title_sub = ParagraphStyle('TitleSub',
            fontName=font_jp, fontSize=fs('TITLE_SUB'), leading=fs('TITLE_SUB')*1.4,
            textColor=c('TITLE_PAGE'), alignment=TA_CENTER)

        self.style_title_en = ParagraphStyle('TitleEN',
            fontName=font_jp, fontSize=fs('TITLE_EN'), leading=fs('TITLE_EN')*1.5,
            textColor=c('TITLE_SUB'), alignment=TA_CENTER)

        self.style_title_info = ParagraphStyle('TitleInfo',
            fontName=font_jp, fontSize=fs('TITLE_INFO'), leading=fs('TITLE_INFO')*1.5,
            textColor=c('TITLE_INFO'), alignment=TA_CENTER)

        self.style_title_desc = ParagraphStyle('TitleDesc',
            fontName=font_jp, fontSize=fs('TITLE_DESC'), leading=fs('TITLE_DESC')*1.5,
            textColor=c('NOTE'), alignment=TA_CENTER)

        self.style_pagenum = ParagraphStyle('PageNum',
            fontName=font_jp, fontSize=fs('PAGENUM'), leading=fs('PAGENUM')*1.5,
            textColor=c('PAGENUM'), alignment=TA_CENTER)

        # Table cell styles
        self.style_th = ParagraphStyle('TH',
            fontName=FONT_JP_BOLD, fontSize=fs('TABLE_HDR'), leading=fs('TABLE_HDR')*1.4,
            textColor=c('TABLE_HDR'))

        self.style_td = ParagraphStyle('TD',
            fontName=font_jp, fontSize=fs('TABLE_BODY'), leading=lh('TABLE'),
            textColor=c('TABLE_BODY'))

    def _p(self, text, style):
        """Create a Paragraph. Escapes '&' to '&amp;'."""
        text = text.replace('&', '&amp;')
        return Paragraph(text, style)

    def _pb(self, text, style):
        """Create a Paragraph with bold font — wraps in <b> + uses bold style font."""
        return Paragraph(f"<b>{text.replace('&', '&amp;')}</b>", style)

    def _bold_inline(self, text, style):
        """Handle <b> tags in text (already XML-escaped)."""
        return Paragraph(text, style)

    def _fix_text(self, text):
        """Replace SimSun-incompatible chars."""
        if self.language == "chinese_annotated":
            text = text.replace('・', '·')
            text = text.replace('〜', '~')
            text = text.replace('⇔', '<->')
            text = text.replace('⑪', '(11)')
        return text

    def build(self, document, output_path):
        """Build the complete PDF document."""
        doc = SimpleDocTemplate(
            str(output_path), pagesize=A4,
            leftMargin=16*mm, rightMargin=17*mm,
            topMargin=15*mm, bottomMargin=15*mm,
            title=document.get("title", ""),
            author="Review Generator",
        )

        story = []
        self._build_title_page(story, document)

        for section in document.get("sections", []):
            story.append(PageBreak())
            self._build_section(story, section)

        doc.build(story, onFirstPage=self._add_page_number,
                  onLaterPages=self._add_page_number)
        return output_path

    def _add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('NS', self._fs('PAGENUM'))
        canvas.setFillColor(HexColor(self._c('PAGENUM')))
        canvas.drawCentredString(A4[0] / 2, 10*mm, f"- {doc.page} -")
        canvas.restoreState()

    def _build_title_page(self, story, document):
        story.append(Spacer(1, 60*mm))
        title = document.get("title", "")
        if title:
            story.append(self._p(title, self.style_title_main))
            story.append(Spacer(1, 8))

        subtitle = document.get("subtitle", "")
        if subtitle:
            story.append(self._p(subtitle, self.style_title_sub))
            story.append(Spacer(1, 12))

        story.append(self._p("Computer Networks", self.style_title_en))
        story.append(Spacer(1, 4))
        story.append(self._p("期末試験対策·復習ガイド（期末考试复习指南）", self.style_title_info))
        story.append(Spacer(1, 24))
        story.append(self._p("全8章PPT内容 | 中日対照 | 試験重点付き", self.style_title_desc))

    def _build_section(self, story, section):
        # Chapter title
        section_title = section.get("title", "")
        story.append(self._p(section_title, self.style_chapter))
        story.append(Spacer(1, 4))

        # Overview
        overview = section.get("overview", "")
        if overview:
            parts = overview.split("\n\n")
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                if i == 0:
                    story.append(self._p(self._fix_text(part), self.style_overview_jp))
                else:
                    story.append(self._p(part, self.style_overview_cn))
            story.append(Spacer(1, 4))

        # Render blocks
        for block in section.get("blocks", []):
            block_type = block.get("type", "text")
            render_func = getattr(self, f"render_{block_type}", None)
            if render_func:
                elements = render_func(block)
                if elements:
                    if isinstance(elements, list):
                        story.extend(elements)
                    else:
                        story.append(elements)
            else:
                story.append(self._p(f"[Unknown: {block_type}]", self.style_note))

    # ---------- block renderers ----------

    def render_heading(self, block):
        level = block.get("level", 1)
        text = block["text"]
        if level == 1:
            return [Spacer(1, 6), self._p(text, self.style_chapter), Spacer(1, 2)]
        elif level == 2:
            return [Spacer(1, 4), self._p(text, self.style_section), Spacer(1, 2)]
        else:
            return self._p(text, self.style_body)

    def render_text(self, block):
        style = self.style_note if block.get("style") == "note" else self.style_body
        return self._p(block["content"], style)

    def render_image(self, block):
        img_path = Path("output/images") / block["file"]
        if not img_path.exists():
            return self._p(f"[Image not found: {block['file']}]", self.style_note)

        max_w = (A4[0] - 33*mm) * 0.9
        max_h = 100*mm

        try:
            from PIL import Image as PILImage
            with PILImage.open(img_path) as im:
                iw, ih = im.size
        except Exception:
            iw, ih = 300, 200

        scale = min(max_w / iw, max_h / ih, 1.0)
        disp_w = iw * scale
        disp_h = ih * scale

        elements = [Spacer(1, 4), Image(str(img_path), width=disp_w, height=disp_h)]

        if block.get("caption"):
            elements.append(Spacer(1, 2))
            elements.append(self._p(block["caption"], self.style_caption))
        elements.append(Spacer(1, 4))
        return elements

    def render_term_table(self, block):
        cols = block.get("columns", ["日语", "读音", "中文", "说明"])
        col_widths_mm = block.get("col_widths")
        rows = block.get("rows", [])

        # Column widths
        if col_widths_mm:
            col_widths = [w * mm for w in col_widths_mm]
        else:
            usable = A4[0] - 33*mm
            if len(cols) == 4:
                col_widths = [usable * 0.25, usable * 0.15, usable * 0.17, usable * 0.43]
            else:
                w_each = usable / len(cols)
                col_widths = [w_each] * len(cols)

        # Header row
        header = [self._p(col, self.style_th) for col in cols]

        # Data rows
        data = []
        for row in rows:
            data.append([self._p(self._fix_text(str(ct)), self.style_td)
                         for ct in row[:len(cols)]])

        table_data = [header] + data
        t = Table(table_data, colWidths=col_widths, repeatRows=1,
                  hAlign='LEFT')

        # Build style
        ts = [
            ('BACKGROUND', (0, 0), (-1, 0), self._c('TABLE_BG')),
            ('TEXTCOLOR', (0, 0), (-1, 0), self._c('TABLE_HDR')),
            ('GRID', (0, 0), (-1, -1), 0.5, self._c('TABLE_BORDER')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]
        # Alternating row colors
        c1 = self._c('TABLE_ROW1')
        c2 = self._c('TABLE_ROW2')
        for i in range(1, len(table_data)):
            ts.append(('BACKGROUND', (0, i), (-1, i), c1 if i % 2 == 1 else c2))

        t.setStyle(TableStyle(ts))

        return [Spacer(1, 4), t, Spacer(1, 4)]

    def render_concept_card(self, block):
        elements = [Spacer(1, 4)]

        # Title
        title = block.get("title", "")
        if title:
            importance = block.get("importance", 0)
            stars = "★" * importance + " " if importance else ""
            elements.append(self._p(f"{stars}{title}", self.style_section))
            elements.append(Spacer(1, 2))

        # Keywords
        keywords = block.get("keywords")
        if keywords:
            kw_text = "【Keywords】 " + "  ·  ".join(keywords)
            elements.append(self._p(kw_text, self.style_keywords))
            elements.append(Spacer(1, 3))

        # Interleaved bilingual paragraphs
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
                text = self._fix_text(jp)
                if self.language == "chinese_annotated":
                    text = self._annotate_terms(text)
                body_style = self.style_body if self.language == "chinese_annotated" else self.style_body_jp
                elements.append(self._p(text, body_style))
                if cn:
                    elements.append(Spacer(1, 1))

            if cn:
                elements.append(self._p(cn, self.style_translation))
                elements.append(Spacer(1, 2))

            if jp or cn:
                gap = 5 if self.language == "chinese_annotated" else 1
                elements.append(Spacer(1, gap))

        # Exam tip
        if block.get("exam_tip"):
            elements.append(Spacer(1, 2))
            elements.append(self._p(block["exam_tip"], self.style_exam))

        # Key point
        if block.get("key_point"):
            elements.append(Spacer(1, 2))
            elements.append(self._p(block["key_point"], self.style_keypoint_bold))

        # Example
        if block.get("example"):
            elements.append(Spacer(1, 2))
            elements.append(self._p(block["example"], self.style_note))

        elements.append(Spacer(1, 4))
        return elements

    def _annotate_terms(self, text):
        """Annotation (English / 日本語) in green NotoSansSC."""
        pattern = r'(（[^）]*?/[^）]*?）)'
        parts = re.split(pattern, text)
        result = []
        for part in parts:
            if not part:
                continue
            if re.match(r'^（[^）]*?/[^）]*?）$', part):
                result.append(
                    f'<font name="{FONT_JP}" color="{self._c("ANNOTATION")}">{part}</font>'
                )
            else:
                result.append(part)
        return ''.join(result)

    def render_highlight_box(self, block):
        box_type = block.get("box_type", "warning")
        if box_type in ("danger", "warning"):
            style = self.style_exam
        elif box_type == "info":
            style = self.style_keypoint
        else:
            style = self.style_note

        label = block.get("label", "")
        content = block.get("content", "")
        elements = [Spacer(1, 4)]
        if label:
            elements.append(self._p(label, self.style_keypoint_bold))
        elements.append(self._p(self._fix_text(content), style))
        elements.append(Spacer(1, 2))
        return elements

    def render_exam_stat(self, block):
        elements = [Spacer(1, 2)]
        elements.append(self._p(block.get("title", ""), self.style_section))
        elements.append(Spacer(1, 3))

        items = block.get("items", [])
        if block.get("stat_type") == "distribution":
            col_w = (A4[0] - 33*mm) / 3
            header = [
                self._p("<b>题型</b>", self.style_th),
                self._p("<b>分值</b>", self.style_th),
                self._p("<b>占比</b>", self.style_th),
            ]
            data = [header]
            for item in items:
                data.append([
                    self._p(item.get("type", ""), self.style_td),
                    self._p(str(item.get("score", "")), self.style_td),
                    self._p(str(item.get("ratio", "")), self.style_td),
                ])
            t = Table(data, colWidths=[col_w, col_w, col_w])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self._c('TABLE_BG')),
                ('GRID', (0, 0), (-1, -1), 0.5, self._c('TABLE_BORDER')),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elements.append(t)
        else:
            for item in items:
                elements.append(self._p(f"  {item}", self.style_body))

        elements.append(Spacer(1, 4))
        return elements


def generate_pdf(content_json_path, output_path, language="jp_first"):
    with open(content_json_path, "r", encoding="utf-8") as f:
        document = json.load(f)

    builder = ReviewPDFBuilder(language=language)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    builder.build(document, output_path)
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate review PDF from JSON")
    parser.add_argument("input", help="Path to content JSON file")
    parser.add_argument("-o", "--output", default="output/review.pdf", help="Output PDF path")
    parser.add_argument("-l", "--language", default="jp_first",
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
