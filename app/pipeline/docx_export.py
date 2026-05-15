"""Export .docx mis en page.

Convertit la synthèse Markdown (qui suit déjà la structure en blocs dictée
par le prompt du programme) en document Word : page de couverture,
titres stylés par bloc dans la couleur du programme (orange CPC / cyan
CRY), listes, tableaux, et mise en évidence des repères d'illustration.
La FORME = structure des blocs (prompt) + identité couleur (programme).
"""

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from programs import Program

BODY_FONT = "Calibri"
DARK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x55, 0x55, 0x55)

ILLUS_RE = re.compile(r"【\s*Illustration.*?】")
TOKEN_RE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*)")


def _shade(cell_or_para_elem, hex_color: str):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    cell_or_para_elem.append(shd)


def _bottom_border(paragraph, hex_color: str, size: str = "12"):
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), hex_color)
    bdr.append(bottom)
    pPr.append(bdr)


def _add_runs(paragraph, text: str, color=DARK, base_size=11, base_bold=False):
    """Rend le gras (**), l'italique (*) et les sauts de ligne internes."""
    for part in text.split("\n"):
        if part is not text.split("\n")[0]:
            paragraph.add_run().add_break()
        for tok in TOKEN_RE.split(part):
            if not tok:
                continue
            bold, ital = base_bold, False
            inner = tok
            if tok.startswith("**") and tok.endswith("**"):
                bold, inner = True, tok[2:-2]
            elif tok.startswith("*") and tok.endswith("*"):
                ital, inner = True, tok[1:-1]
            run = paragraph.add_run(inner)
            run.font.name = BODY_FONT
            run.font.size = Pt(base_size)
            run.font.color.rgb = color
            run.font.bold = bold
            run.font.italic = ital


def _heading(doc, text, size, accent_rgb, hex_accent, rule=False):
    text = text.strip()
    if text.startswith("**") and text.endswith("**"):
        text = text[2:-2]
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16 if size >= 15 else 10)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.font.name = BODY_FONT
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = accent_rgb
    if rule:
        _bottom_border(p, hex_accent, "8")
    return p


def _illustration(doc, text, hex_accent, accent_rgb):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    _shade(p._p.get_or_add_pPr(), "F4F4F4")
    r = p.add_run("📷  " + text.strip())
    r.font.name = BODY_FONT
    r.font.size = Pt(10.5)
    r.font.italic = True
    r.font.bold = True
    r.font.color.rgb = accent_rgb


def _table(doc, header, rows, hex_accent):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        cell = t.rows[0].cells[j]
        cell.text = ""
        _shade(cell._tc.get_or_add_tcPr(), hex_accent)
        run = cell.paragraphs[0].add_run(h.strip())
        run.font.name = BODY_FONT
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for row in rows:
        cells = t.add_row().cells
        for j in range(len(header)):
            cells[j].text = ""
            val = row[j] if j < len(row) else ""
            _add_runs(cells[j].paragraphs[0], val, color=DARK, base_size=10)


def _cover(doc, program: Program, month: str, year: str, accent_rgb, hex_accent):
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(program.name.upper())
    r.font.name = BODY_FONT
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = GREY
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title = f"DOSSIER {month.upper()} {year}".strip()
    r2 = p2.add_run(title)
    r2.font.name = BODY_FONT
    r2.font.size = Pt(34)
    r2.font.bold = True
    r2.font.color.rgb = accent_rgb
    rule = doc.add_paragraph()
    rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _bottom_border(rule, hex_accent, "18")
    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rs = s.add_run("Synthèse exclusive")
    rs.font.name = BODY_FONT
    rs.font.size = Pt(12)
    rs.font.italic = True
    rs.font.color.rgb = GREY
    doc.add_page_break()


def _footer(doc, program: Program, month: str, year: str):
    sec = doc.sections[0]
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"{program.name} — Dossier {month} {year}")
    run.font.name = BODY_FONT
    run.font.size = Pt(8)
    run.font.color.rgb = GREY


def build_docx(markdown_text: str, program: Program, month: str, year: str, out_path: str) -> str:
    hex_accent = (program.docx_accent or "1F3A93").lstrip("#").upper()
    accent_rgb = RGBColor.from_string(hex_accent)

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = BODY_FONT
    style.font.size = Pt(11)
    style.font.color.rgb = DARK
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(2.2)
        s.left_margin = s.right_margin = Cm(2.4)

    _cover(doc, program, month, year, accent_rgb, hex_accent)
    _footer(doc, program, month, year)

    lines = (markdown_text or "").replace("\r", "").split("\n")
    i = 0
    while i < len(lines):
        l = lines[i]

        # Tableau Markdown
        if re.match(r"^\s*\|.*\|\s*$", l) and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            header = [c.strip() for c in l.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            _table(doc, header, rows, hex_accent)
            doc.add_paragraph()
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", l)
        if m:
            level = len(m.group(1))
            sizes = {1: 22, 2: 16, 3: 13, 4: 12, 5: 11, 6: 11}
            _heading(doc, m.group(2), sizes.get(level, 12), accent_rgb, hex_accent, rule=(level <= 2))
            i += 1
            continue

        if ILLUS_RE.search(l):
            _illustration(doc, ILLUS_RE.search(l).group(0), hex_accent, accent_rgb)
            i += 1
            continue

        if re.match(r"^\s*[-*]\s+", l):
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                p = doc.add_paragraph(style="List Bullet")
                _add_runs(p, re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            continue

        if re.match(r"^\s*\d+\.\s+", l):
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                p = doc.add_paragraph(style="List Number")
                _add_runs(p, re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            continue

        if l.strip() == "" or re.match(r"^\s*---\s*$", l):
            i += 1
            continue

        para = []
        while i < len(lines) and lines[i].strip() != "" and not re.match(r"^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|\s*\|)", lines[i]) and not ILLUS_RE.search(lines[i]):
            para.append(lines[i])
            i += 1
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        _add_runs(p, "\n".join(para))

    doc.core_properties.title = f"Dossier {program.short} {month} {year}"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path
