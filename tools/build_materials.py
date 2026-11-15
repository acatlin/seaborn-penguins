"""Build the teaching materials in instructor/: the Word files and the objectives workbook.

Usage:  python tools/build_materials.py

Produces:
  instructor/Seaborn_Assessment_Pack_INSTRUCTOR.docx  25 MCQs with answers marked,
                                                      answer key, 3 assignments
                                                      and a short task, with
                                                      rubrics and solutions
  instructor/Seaborn_Assessment_Pack_STUDENT.docx     the same without answers
                                                      or solutions
  instructor/Seaborn_Instructor_Guide.docx            content/instructor-guide.md
                                                      as a Word document
  instructor/Seaborn_Mastery_Objectives.xlsx          the mastery objectives and
                                                      their map onto the course
                                                      (tools/build_objectives.py)

Every assignment solution is executed (via tools/runner.py) and its figure is
embedded, so a solution that stops working fails the build.
"""

import collections
import io
import re
import sys
from pathlib import Path

import yaml
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
INSTRUCTOR = ROOT / "instructor"
sys.path.insert(0, str(ROOT / "tools"))
import build_objectives  # noqa: E402
import runner  # noqa: E402

runner.DATA_PATH = str(ROOT / "data" / "penguins.csv")

LETTERS = "ABCD"
ACCENT = RGBColor(0x0F, 0x71, 0x73)
GOOD = RGBColor(0x1A, 0x7F, 0x37)
MUTED = RGBColor(0x55, 0x5B, 0x63)
FONT = "Calibri"
MONO = "Consolas"


class MaterialsError(Exception):
    pass


# ---------------------------------------------------------------- data

def load_exam():
    return yaml.safe_load((INSTRUCTOR / "exam_questions.yaml").read_text(encoding="utf-8"))


def load_assignments():
    return yaml.safe_load((INSTRUCTOR / "assignments.yaml").read_text(encoding="utf-8"))


def graded_work(spec):
    """The assignments, then the short tasks: both are written, scored and rendered alike."""
    return list(spec["assignments"]) + list(spec.get("tasks") or [])


def run_solutions(spec):
    """Execute every solution part; return {(assignment_idx, part_idx): result}. The short
    tasks are numbered on from the assignments."""
    results = {}
    for a, assignment in enumerate(graded_work(spec)):
        for p, part in enumerate(assignment["solution"]):
            if "code" not in part:
                continue
            result = runner.run_cell(part["code"], setup=spec["setup"], dpi=130)
            where = f"{assignment['title']} / {part['title']}"
            if result["error"]:
                raise MaterialsError(f"{where} failed:\n{result['error']}")
            if result["warnings"]:
                raise MaterialsError(f"{where} warned:\n" + "\n".join(result["warnings"]))
            results[(a, p)] = result
    return results


# ---------------------------------------------------------------- docx helpers

def new_document(title):
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, side, Inches(1))
    styles = doc.styles
    styles["Normal"].font.name = FONT
    styles["Normal"].font.size = Pt(11)
    styles["Normal"].paragraph_format.space_after = Pt(6)
    for name, size, before, after in (("Title", 26, 0, 6), ("Heading 1", 18, 18, 8),
                                      ("Heading 2", 14, 14, 6), ("Heading 3", 12, 10, 4)):
        st = styles[name]
        st.font.name = FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = ACCENT if name != "Title" else RGBColor(0x1F, 0x23, 0x28)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
    core = doc.core_properties
    core.title = title
    core.author = "Seaborn with Penguins"
    footer = section.footer.paragraphs[0]
    footer.text = title
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = MUTED
    return doc


def shade(paragraph, fill="F2F2F2"):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def left_border(paragraph, color="0F7173"):
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    for k, v in (("w:val", "single"), ("w:sz", "18"), ("w:space", "8"), ("w:color", color)):
        left.set(qn(k), v)
    borders.append(left)
    p_pr.append(borders)


INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|\*[^*\s][^*]*\*)")


def add_rich(paragraph, text, size=None, color=None, bold=None, italic=None):
    """Add text with inline markdown: `code`, **bold**, *italic*, [link](url)."""
    for piece in INLINE.split(str(text)):
        if not piece:
            continue
        run_bold, run_italic, mono = bold, italic, False
        if piece.startswith("`") and piece.endswith("`"):
            piece, mono = piece[1:-1], True
        elif piece.startswith("**") and piece.endswith("**"):
            piece, run_bold = piece[2:-2], True
        elif piece.startswith("[") and "](" in piece:
            label, url = re.match(r"\[([^\]]+)\]\(([^)]+)\)", piece).groups()
            piece = f"{label} ({url})" if url.startswith("http") else label
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            piece, run_italic = piece[1:-1], True
        run = paragraph.add_run(piece)
        if mono:
            run.font.name = MONO
            run.font.size = Pt((size or 11) - 1.5)
        elif size:
            run.font.size = Pt(size)
        if color is not None:
            run.font.color.rgb = color
        if run_bold:
            run.bold = True
        if run_italic:
            run.italic = True
    return paragraph


def add_code(doc, code):
    lines = code.rstrip("\n").split("\n")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    shade(p)
    for i, line in enumerate(lines):
        run = p.add_run(line)
        run.font.name = MONO
        run.font.size = Pt(8.5)
        if i < len(lines) - 1:
            run.add_break()
    return p


def add_table(doc, header, rows, widths, across_pages=False):
    """across_pages: the table may run over a page break, so keep every row whole and
    repeat the header row at the top of the next page."""
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, text in zip(table.rows[0].cells, header):
        cell.text = ""
        add_rich(cell.paragraphs[0], text, bold=True, size=10)
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "E6F1F1")
        tc_pr.append(shd)
    for row in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = ""
            add_rich(cell.paragraphs[0], text, size=10)
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = Inches(width)
    if across_pages:
        for n, row in enumerate(table.rows):
            row_pr = row._tr.get_or_add_trPr()
            row_pr.append(OxmlElement("w:cantSplit"))
            if n == 0:
                row_pr.append(OxmlElement("w:tblHeader"))
    doc.add_paragraph()
    return table


def add_numbered_item(doc, label, text, level=0):
    """One item of a numbered list with an explicit label such as "3.".

    Word's built-in "List Number" style keeps counting across the whole
    document, so the second assignment's tasks would start at 5. Writing the
    number ourselves makes every list restart at 1.
    """
    p = doc.add_paragraph()
    indent = 0.3 + 0.3 * level
    p.paragraph_format.left_indent = Inches(indent)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.paragraph_format.space_after = Pt(3)
    add_rich(p, f"{label}\t", bold=True)
    add_rich(p, text)
    return p


def add_bullets(doc, items, numbered=False):
    for n, item in enumerate(items, 1):
        if numbered:
            add_numbered_item(doc, f"{n}.", item)
        else:
            add_rich(doc.add_paragraph(style="List Bullet"), item)


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ---------------------------------------------------------------- assessment pack

def build_assessment(questions, spec, results, instructor):
    edition = "Instructor Edition" if instructor else "Student Edition"
    doc = new_document(f"Seaborn with Penguins - Assessment Pack ({edition})")
    doc.add_paragraph("Seaborn with Penguins", style="Title")
    add_rich(doc.add_paragraph(), f"Assessment Pack - {edition}", size=16, color=ACCENT, bold=True)
    intro = doc.add_paragraph()
    if instructor:
        add_rich(intro, "Contents: **Part 1** - 25 multiple-choice questions with the correct answer marked "
                        "and explained, followed by an answer key. **Part 2** - three assignments of "
                        "increasing complexity and a short task, each with a rubric and a tested model solution. "
                        "Every solution in this document was executed to produce the figures shown.")
        warn = doc.add_paragraph()
        shade(warn, "FFF6E6")
        add_rich(warn, "Keep this edition private. A student edition without answers or solutions is "
                       "provided alongside it.", italic=True)
    else:
        add_rich(intro, "**Part 1** - 25 multiple-choice questions: choose the single best answer. "
                        "**Part 2** - three assignments of increasing complexity and a short task, "
                        "each with a rubric.")
    add_rich(doc.add_paragraph(), "Dataset for every question: `penguins = sns.load_dataset(\"penguins\")`, "
                                  "seaborn 0.13.", color=MUTED, size=10)

    # Part 1
    doc.add_heading("Part 1 - Multiple-choice questions", level=1)
    if not instructor:
        add_rich(doc.add_paragraph(), "Name: ______________________________    Date: ______________")
    for n, q in enumerate(questions, 1):
        p = doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(10)
        add_rich(p, f"Q{n}. ", bold=True, color=ACCENT)
        add_rich(p, q["q"], bold=True)
        if q.get("code"):
            add_code(doc, q["code"]).paragraph_format.keep_with_next = True
        for j, option in enumerate(q["options"]):
            op = doc.add_paragraph()
            op.paragraph_format.left_indent = Inches(0.3)
            op.paragraph_format.space_after = Pt(2)
            op.paragraph_format.keep_with_next = j < 3 or instructor
            correct = instructor and LETTERS[j] == q["answer"]
            add_rich(op, f"{LETTERS[j]}.  ", bold=True, color=GOOD if correct else None)
            add_rich(op, option, bold=correct or None, color=GOOD if correct else None)
            if correct:
                add_rich(op, "   ✓ correct answer", bold=True, color=GOOD, size=9)
        if instructor:
            ex = doc.add_paragraph()
            ex.paragraph_format.left_indent = Inches(0.3)
            add_rich(ex, f"Why: {q['explain']}", italic=True, color=MUTED, size=9.5)
            add_rich(ex, f"  (Lesson {q['lesson']})", color=MUTED, size=9)

    if instructor:
        page_break(doc)
        doc.add_heading("Answer key", level=2)
        half = (len(questions) + 1) // 2
        rows = []
        for i in range(half):
            left = [f"Q{i + 1}", questions[i]["answer"], f"Lesson {questions[i]['lesson']}"]
            j = i + half
            right = ([f"Q{j + 1}", questions[j]["answer"], f"Lesson {questions[j]['lesson']}"]
                     if j < len(questions) else ["", "", ""])
            rows.append(left + right)
        add_table(doc, ["Question", "Answer", "Lesson", "Question", "Answer", "Lesson"], rows,
                  [0.9, 0.8, 1.0, 0.9, 0.8, 1.0])
        counts = collections.Counter(q["answer"] for q in questions)
        add_rich(doc.add_paragraph(), "Answer distribution: " +
                 ", ".join(f"{k} = {counts[k]}" for k in LETTERS) +
                 f" (out of {len(questions)}).", color=MUTED, size=10)
        per_lesson = collections.Counter(q["lesson"] for q in questions)
        add_rich(doc.add_paragraph(), "Coverage by lesson: " +
                 ", ".join(f"L{k}: {per_lesson[k]}" for k in sorted(per_lesson)) + ".",
                 color=MUTED, size=10)

    # Part 2
    page_break(doc)
    doc.add_heading("Part 2 - Assignments", level=1)
    add_rich(doc.add_paragraph(), "All of them use the Palmer penguins data and the course setup:")
    add_code(doc, spec["setup"])
    scoring = doc.add_paragraph()
    shade(scoring, "EEF6F6")
    left_border(scoring)
    add_rich(scoring, "How the rubrics are scored. ", bold=True)
    add_rich(scoring, spec["scoring"])
    for a, assignment in enumerate(graded_work(spec)):
        if a:
            page_break(doc)
        doc.add_heading(assignment["title"], level=2)
        meta = doc.add_paragraph()
        add_rich(meta, f"Level: {assignment['level']}    ·    Time: {assignment['time']}", color=MUTED, size=10)
        add_rich(doc.add_paragraph(), assignment["scenario"])
        doc.add_heading("Tasks", level=3)
        add_bullets(doc, assignment["tasks"], numbered=True)
        if assignment.get("intern_chart"):
            lead = add_rich(doc.add_paragraph(), "The intern's chart to make over:", bold=True)
            lead.paragraph_format.keep_with_next = True
            add_code(doc, assignment["intern_chart"])
        doc.add_heading("Deliverables", level=3)
        add_bullets(doc, assignment["deliverables"])
        doc.add_heading("Rubric (100 points)", level=3)
        total = sum(r[1] for r in assignment["rubric"])
        if total != 100:
            raise MaterialsError(f"{assignment['title']}: rubric totals {total}, not 100")
        add_table(doc, ["Criterion", "Points", "Full credit looks like"],
                  [[r[0], str(r[1]), r[2]] for r in assignment["rubric"]], [1.8, 0.7, 4.0])
        if not instructor:
            continue
        doc.add_heading("Model solution", level=3)
        for p, part in enumerate(assignment["solution"]):
            title_par = add_rich(doc.add_paragraph(), part["title"], bold=True, color=ACCENT)
            title_par.paragraph_format.keep_with_next = True  # never orphan a part title
            if "code" in part:
                code_par = add_code(doc, part["code"])
                result = results[(a, p)]
                # keep a short solution on the same page as its figure
                code_par.paragraph_format.keep_with_next = part["code"].count("\n") < 25
                if result["stdout"].strip():
                    out_label = add_rich(doc.add_paragraph(), "Output:", color=MUTED, size=9)
                    out_label.paragraph_format.keep_with_next = True
                    add_code(doc, result["stdout"].rstrip())
                for fig in result["figures"]:
                    doc.add_picture(io.BytesIO(fig), width=Inches(6.0))
            if part.get("text"):
                tp = doc.add_paragraph()
                left_border(tp)
                add_rich(tp, part["text"], italic=True)
            if part.get("notes"):
                np_ = doc.add_paragraph()
                add_rich(np_, "Grading note: ", bold=True, size=10, color=MUTED)
                add_rich(np_, part["notes"], size=10, color=MUTED)
    return doc


# ---------------------------------------------------------------- instructor guide

def build_guide(md_text):
    doc = new_document("Seaborn with Penguins - Instructor Guide")
    lines = md_text.splitlines()
    i = 0
    first_h1 = True
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            i += 1
            continue
        if stripped.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            add_code(doc, "\n".join(lines[i + 1:j]))
            i = j + 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            if level == 1 and first_h1:
                doc.add_paragraph(m.group(2), style="Title")
                first_h1 = False
            else:
                doc.add_heading(m.group(2), level=level)
            i += 1
            continue
        if stripped.startswith("!!!"):
            m = re.match(r'!!!\s+\w+\s*(?:"([^"]*)")?', stripped)
            body = []
            i += 1
            while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
                body.append(lines[i][4:])
                i += 1
            p = doc.add_paragraph()
            shade(p, "EEF6F6")
            left_border(p)
            if m and m.group(1):
                add_rich(p, m.group(1) + ". ", bold=True)
            add_rich(p, " ".join(b.strip() for b in body if b.strip() and not b.strip().startswith("|")))
            continue
        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            ncols = len(rows[0])
            width = 6.5 / ncols
            add_table(doc, rows[0], rows[1:], [width] * ncols, across_pages=True)
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", line)
        if m:
            level = 1 if len(m.group(1)) >= 2 else 0
            if m.group(2)[0].isdigit():
                add_numbered_item(doc, m.group(2), m.group(3), level=level)
            else:
                style = "List Bullet 2" if level else "List Bullet"
                add_rich(doc.add_paragraph(style=style), m.group(3))
            i += 1
            continue
        # paragraph: join continuation lines
        para = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^\s*(#|[-*]\s|\d+\.\s|\||!!!|```)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        text = re.sub(r"<[^>]+>", "", " ".join(para))
        add_rich(doc.add_paragraph(), text)
    return doc


def guide_markdown():
    site = yaml.safe_load((ROOT / "content" / "_site.yml").read_text(encoding="utf-8"))
    repo_url = f"https://github.com/{site['github_user']}/{site['repo']}"
    text = (ROOT / "content" / "instructor-guide.md").read_text(encoding="utf-8")
    return text.replace("{{repo_url}}", repo_url)


def main():
    questions = load_exam()
    spec = load_assignments()
    try:
        results = run_solutions(spec)
    except MaterialsError as exc:
        print(f"MATERIALS BUILD FAILED\n{exc}", file=sys.stderr)
        sys.exit(1)
    outputs = {
        "Seaborn_Assessment_Pack_INSTRUCTOR.docx": build_assessment(questions, spec, results, True),
        "Seaborn_Assessment_Pack_STUDENT.docx": build_assessment(questions, spec, results, False),
        "Seaborn_Instructor_Guide.docx": build_guide(guide_markdown()),
    }
    for name, doc in outputs.items():
        doc.save(INSTRUCTOR / name)
        print(f"  wrote instructor/{name}")
    try:
        workbook = build_objectives.write()
    except build_objectives.ObjectivesError as exc:
        print(f"MATERIALS BUILD FAILED\n{exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  wrote instructor/{workbook.name}")


if __name__ == "__main__":
    main()
