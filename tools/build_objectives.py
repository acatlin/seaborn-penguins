"""Build the mastery-objectives workbook in instructor/.

Usage:  python tools/build_objectives.py     (python tools/build_materials.py runs it too)

Reads   instructor/mastery_objectives.yaml    the objectives, the page map, the evidence map
        content/_site.yml, content/*.md       page sections, lesson goals, exercises, quizzes
        instructor/exam_questions.yaml        exam questions
        instructor/assignments.yaml           rubric rows
Writes  instructor/Seaborn_Mastery_Objectives.xlsx

The build is strict: it fails if the maps name a page section, exercise, question or
rubric row that does not exist, or leave out one that does.

Counts, totals and statuses in the workbook are formulas, so they follow an edit made
in Excel. openpyxl saves a formula without its result, and a viewer that does not
calculate would then show an empty cell. Every formula here is therefore built by a
helper that also knows how to work out its value (class F), and that value is stored
in the file beside the formula.

The file is reproducible: the same sources give the same bytes on the same machine.
"""

import datetime
import html
import io
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

import markdown
import yaml
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
INSTRUCTOR = ROOT / "instructor"
SOURCE = INSTRUCTOR / "mastery_objectives.yaml"
OUTPUT = INSTRUCTOR / "Seaborn_Mastery_Objectives.xlsx"
sys.path.insert(0, str(ROOT / "tools"))
import build_site  # noqa: E402  (fence parsing and the Markdown settings that name the anchors)

BLOOM = ("Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create")
ROLES = {"T": "Teaches", "I": "Introduces", "R": "Reinforces", "O": "Orientation"}
GOAL, PRACTICE, QUIZ = "Lesson goal", "Practice", "Quiz"
EXERCISE, QUIZ_ITEM, EXAM_ITEM, RUBRIC_ROW = "Exercise", "Quiz question", "Exam question", "Rubric row"
COVERED, PARTIAL, PLANNED = "Covered", "Partial", "Planned"
LESSON_MIDPOINT = 60  # minutes: the middle of the instructor guide's 45-75 per lesson
SHEETS = ("Read me", "Objectives", "Page map", "Page detail", "Evidence", "Timing")


class ObjectivesError(Exception):
    pass


# ---------------------------------------------------------------- the course as it stands

@dataclass
class Section:
    anchor: str
    title: str
    exercises: list = field(default_factory=list)  # exercise ids
    quiz: list = field(default_factory=list)       # question numbers on the page


@dataclass
class Page:
    slug: str
    num: str
    label: str   # "Start here" or "Lesson 3"
    nav: str     # the short title in the sidebar
    url: str
    sections: list
    goals: list  # the "By the end of this lesson you can" bullets


@dataclass
class Course:
    pages: list
    exercises: dict  # id -> {"page", "title"}
    quiz: dict       # "lesson.question" -> {"page", "number", "text"}
    exam: list       # the questions of exam_questions.yaml
    rubric: dict     # "assignment.row" -> {"assignment", "criterion", "points"}

    def page(self, slug):
        return next(p for p in self.pages if p.slug == slug)


GOALS = re.compile(r"\*\*By the end of this lesson you can:\*\*\n\n((?:- [^\n]*\n)+)")


def plain(text):
    """Markdown inline code without its backticks, for a spreadsheet cell."""
    return str(text).replace("`", "").strip()


def _flatten(tokens):
    for token in tokens:
        yield token
        yield from _flatten(token["children"])


def read_page(entry, base):
    slug = entry["slug"]
    text = (CONTENT / f"{slug}.md").read_text(encoding="utf-8")
    md_text, blocks = build_site.split_blocks(text)
    md = markdown.Markdown(extensions=build_site.MD_EXTENSIONS, extension_configs={"toc": {"permalink": False}})
    md.convert(md_text)  # the same conversion the site build does, so the ids are the site's ids
    headings = [t for t in _flatten(md.toc_tokens) if t["level"] == 2]
    sections, question = [], 0
    for line in md_text.splitlines():
        if line.startswith("## "):
            token = headings[len(sections)]
            sections.append(Section(token["id"], plain(html.unescape(token["name"]))))
        placeholder = re.fullmatch(r"BLOCK(\d+)PLACEHOLDER", line.strip())
        if not placeholder or not sections:
            continue
        block = blocks[int(placeholder.group(1))]
        if block.kind == "exercise":
            sections[-1].exercises.append((block.opts["id"], plain(block.opts.get("title", ""))))
        elif block.kind == "quiz":
            for q in yaml.safe_load(block.body):
                question += 1
                sections[-1].quiz.append((question, plain(q["q"])))
    if len(sections) != len(headings):
        raise ObjectivesError(f"{slug}: found {len(sections)} '## ' lines but {len(headings)} h2 headings")
    goals = GOALS.search(text)
    num = str(entry["num"])
    return Page(slug=slug, num=num, label=entry["nav"] if num == "0" else f"Lesson {num}", nav=entry["nav"],
                url=f"{base}{slug}.html", sections=sections,
                goals=[plain(line[2:]) for line in goals.group(1).splitlines()] if goals else [])


def read_course():
    site = yaml.safe_load((CONTENT / "_site.yml").read_text(encoding="utf-8"))
    base = f"https://{site['github_user']}.github.io/{site['repo']}/"
    pages = [read_page(entry, base) for entry in site["pages"] if entry["slug"] != "instructor-guide"]
    exercises, quiz = {}, {}
    for page in pages:
        for section in page.sections:
            for ex_id, title in section.exercises:
                exercises[ex_id] = {"page": page, "title": title}
            for number, text in section.quiz:
                quiz[f"{page.num}.{number}"] = {"page": page, "number": number, "text": text}
    exam = yaml.safe_load((INSTRUCTOR / "exam_questions.yaml").read_text(encoding="utf-8"))
    assignments = yaml.safe_load((INSTRUCTOR / "assignments.yaml").read_text(encoding="utf-8"))["assignments"]
    rubric = {f"{a}.{r}": {"assignment": assignment["title"], "criterion": row[0], "points": row[1]}
              for a, assignment in enumerate(assignments, 1) for r, row in enumerate(assignment["rubric"], 1)}
    return Course(pages=pages, exercises=exercises, quiz=quiz, exam=exam, rubric=rubric)


def load_spec():
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- the maps, checked and joined

def _mapped(entry):
    """An evidence entry is a list of objectives, one objective, or {objectives, note}."""
    if isinstance(entry, dict):
        return list(entry.get("objectives") or []), entry.get("note", "")
    if isinstance(entry, str):
        return [entry], ""
    return list(entry or []), ""


def evidence_of(spec, kind):
    """{key: (objectives, note)} for 'exercises', 'quiz', 'exam' or 'rubric', keys as strings."""
    return {str(key): _mapped(entry) for key, entry in (spec["evidence"].get(kind) or {}).items()}


def validate(spec, course):
    """Raise ObjectivesError listing every way the maps disagree with the course."""
    problems = []
    objectives = spec["objectives"]
    ids = [o["id"] for o in objectives]
    known = set(ids)
    sections = [s["key"] for s in spec["sections"]]
    if len(known) != len(ids):
        problems.append("objective ids are not unique")
    for key in sections:
        got = [i for i in ids if i.startswith(key)]
        if got != [f"{key}{n:02d}" for n in range(1, len(got) + 1)]:
            problems.append(f"section {key}: ids should run {key}01, {key}02, ... in order, got {got}")
    if [i[0] for i in ids] != sorted((i[0] for i in ids), key=sections.index):
        problems.append("objectives should be listed section by section, in the order of 'sections'")
    for position, o in enumerate(objectives):
        where = o["id"]
        for name in ("name", "can", "tools", "strand", "bloom", "shown_by"):
            if not str(o.get(name) or "").strip():
                problems.append(f"{where}: '{name}' is empty")
        if not o.get("criteria"):
            problems.append(f"{where}: needs at least one criterion")
        if o.get("bloom") not in BLOOM:
            problems.append(f"{where}: bloom '{o.get('bloom')}' is not one of {', '.join(BLOOM)}")
        if o.get("strand") not in spec["strands"]:
            problems.append(f"{where}: strand '{o.get('strand')}' is not defined under 'strands'")
        if o.get("shown_by") not in spec["shown_by"]:
            problems.append(f"{where}: shown_by '{o.get('shown_by')}' is not defined under 'shown_by'")
        for needed in o.get("prerequisites") or []:
            if needed not in ids[:position]:
                problems.append(f"{where}: prerequisite {needed} must be an objective listed before it")
        if not isinstance(o.get("to_write"), int) or o["to_write"] < 0:
            problems.append(f"{where}: to_write must be a whole number of minutes")

    slugs = {p.slug for p in course.pages}
    for slug, split in spec["lesson_minutes"].items():
        if slug not in slugs:
            problems.append(f"lesson_minutes: no page '{slug}'")
        problems += [f"lesson_minutes {slug}: unknown objective {o}" for o in split if o not in known]

    for n, added in enumerate(spec.get("added_minutes") or [], 1):
        where = f"added_minutes, entry {n}"
        if set(added) != {"lesson", "objective", "minutes", "what"}:
            problems.append(f"{where}: give lesson, objective, minutes and what")
            continue
        if added["lesson"] not in spec["lesson_minutes"]:
            problems.append(f"{where}: no lesson '{added['lesson']}'")
        if added["objective"] not in known:
            problems.append(f"{where}: unknown objective {added['objective']}")
        if not isinstance(added["minutes"], int) or added["minutes"] <= 0:
            problems.append(f"{where}: minutes must be a whole number above zero")

    for page in course.pages:
        goals = spec["lesson_goals"].get(page.slug, [])
        if len(goals) != len(page.goals):
            problems.append(f"lesson_goals {page.slug}: the page states {len(page.goals)} goals, "
                            f"the map has {len(goals)}")
        problems += [f"lesson_goals {page.slug}: unknown objective {o}" for o in goals if o not in known]
    problems += [f"lesson_goals: no page '{slug}'" for slug in spec["lesson_goals"] if slug not in slugs]

    for slug, entries in spec["page_map"].items():
        if slug not in slugs:
            problems.append(f"page_map: no page '{slug}'")
            continue
        anchors = {s.anchor for s in course.page(slug).sections}
        seen = set()
        for entry in entries:
            anchor, objective, role = entry[0], entry[1], entry[2]
            if anchor != "*" and anchor not in anchors:
                problems.append(f"page_map {slug}: no section '#{anchor}' on the page")
            if role not in ROLES:
                problems.append(f"page_map {slug} #{anchor}: role '{role}' is not one of {', '.join(ROLES)}")
            if (role == "O") != (objective is None):
                problems.append(f"page_map {slug} #{anchor}: role O goes with no objective, every other role needs one")
            if objective is not None and objective not in known:
                problems.append(f"page_map {slug} #{anchor}: unknown objective {objective}")
            if (anchor, objective) in seen:
                problems.append(f"page_map {slug} #{anchor}: {objective} is mapped twice")
            seen.add((anchor, objective))
        for section in course.page(slug).sections:
            if not (section.exercises or section.quiz or any(e[0] == section.anchor for e in entries)):
                problems.append(f"page_map {slug}: section '#{section.anchor}' is not mapped "
                                "(give it an objective, or role O)")
    problems += [f"page_map: page '{p.slug}' is missing" for p in course.pages if p.slug not in spec["page_map"]]

    expected = {"exercises": set(course.exercises), "quiz": set(course.quiz),
                "exam": {str(n) for n in range(1, len(course.exam) + 1)}, "rubric": set(course.rubric)}
    for kind, wanted in expected.items():
        mapped = evidence_of(spec, kind)
        problems += [f"evidence {kind}: '{key}' does not exist" for key in sorted(set(mapped) - wanted)]
        problems += [f"evidence {kind}: '{key}' is not mapped" for key in sorted(wanted - set(mapped))]
        for key, (objs, note) in mapped.items():
            problems += [f"evidence {kind} {key}: unknown objective {o}" for o in objs if o not in known]
            if len(set(objs)) != len(objs):
                problems.append(f"evidence {kind} {key}: an objective is listed twice")
            if kind in ("quiz", "exam") and len(objs) != 1:
                problems.append(f"evidence {kind} {key}: map it to exactly one objective")
            if kind == "exercises" and not objs:
                problems.append(f"evidence exercises {key}: map it to at least one objective")
            if kind == "rubric" and not objs and not note:
                problems.append(f"evidence rubric {key}: a row mapped to no objective needs a note saying why")
    if problems:
        raise ObjectivesError("instructor/mastery_objectives.yaml:\n  " + "\n  ".join(problems))


def _runs(numbers, prefix=""):
    """[5, 6, 7, 8, 10] -> 'Q5-Q8, Q10' (runs of three or more are folded)."""
    numbers = sorted(set(numbers))
    out, i = [], 0
    while i < len(numbers):
        j = i
        while j + 1 < len(numbers) and numbers[j + 1] == numbers[j] + 1:
            j += 1
        if j - i >= 2:
            out.append(f"{prefix}{numbers[i]}-{prefix}{numbers[j]}")
        else:
            out += [f"{prefix}{n}" for n in numbers[i:j + 1]]
        i = j + 1
    return ", ".join(out)


def _page_list(pages):
    """Pages as 'Start here; Lessons 2-5, 7'."""
    parts = [p.label for p in pages if p.num == "0"]
    lessons = [int(p.num) for p in pages if p.num != "0"]
    if lessons:
        parts.append(("Lesson " if len(lessons) == 1 else "Lessons ") + _runs(lessons))
    return "; ".join(parts)


def assemble(spec, course):
    """Join the maps to the course: the rows of the Page detail and Evidence sheets, and
    for every objective its counts, its status and the text of its summary cells."""
    names = {o["id"]: o["name"] for o in spec["objectives"]}
    exercises, quiz = evidence_of(spec, "exercises"), evidence_of(spec, "quiz")
    exam, rubric = evidence_of(spec, "exam"), evidence_of(spec, "rubric")

    detail = []  # (page, section title, link, role, objective or None, note)

    def items_by_objective(found, label):
        """found: [(item label, objectives)] -> [(objective, note)], primary items first."""
        order = []
        for _, objs in found:
            order += [o for o in objs if o not in order]
        rows = []
        for objective in order:
            main = [item for item, objs in found if objs[0] == objective]
            also = [item for item, objs in found if objective in objs[1:]]
            note = ", ".join(main)
            if also:
                note += ("; " if main else "") + f"also {label} " + ", ".join(also)
            rows.append((objective, note[0].upper() + note[1:]))
        return rows

    for page in course.pages:
        for objective, goal in zip(spec["lesson_goals"].get(page.slug, []), page.goals):
            detail.append((page, "Lesson goals", page.url, GOAL, objective, goal[0].upper() + goal[1:]))
        entries = spec["page_map"][page.slug]
        for section in page.sections:
            link = f"{page.url}#{section.anchor}"
            for entry in entries:
                if entry[0] == section.anchor:
                    detail.append((page, section.title, link, ROLES[entry[2]], entry[1],
                                   entry[3] if len(entry) > 3 else ""))
            found = [(f"Ex {ex_id}", exercises[ex_id][0]) for ex_id, _ in section.exercises]
            for objective, note in items_by_objective(found, "checked in"):
                detail.append((page, section.title, link, PRACTICE, objective, note))
            found = [(f"Q{number}", quiz[f"{page.num}.{number}"][0]) for number, _ in section.quiz]
            for objective, note in items_by_objective(found, "in"):
                detail.append((page, section.title, link, QUIZ, objective, note))
        for entry in entries:
            if entry[0] == "*":
                detail.append((page, "Whole page", page.url, ROLES[entry[2]], entry[1],
                               entry[3] if len(entry) > 3 else ""))

    evidence = []  # (item, type, where, text, link, primary, also, points, use, note)
    for ex_id, info in course.exercises.items():
        objs, note = exercises[ex_id]
        evidence.append((f"Ex {ex_id}", EXERCISE, info["page"].label, info["title"],
                         f"{info['page'].url}#ex-{ex_id}", objs[0], objs[1:], None,
                         "Practice, checked automatically", note))
    for key, info in course.quiz.items():
        objs, note = quiz[key]
        page = info["page"]
        evidence.append((f"Quiz L{page.num} Q{info['number']}", QUIZ_ITEM, page.label, info["text"],
                         f"{page.url}#{page.slug}-q{info['number']}", objs[0], [], None,
                         "Practice, instant feedback", note))
    for number, question in enumerate(course.exam, 1):
        objs, note = exam[str(number)]
        stem = plain(question["q"])
        if question.get("code"):  # "this chart" means nothing without the code it refers to
            stem += "\n" + question["code"].strip()
        evidence.append((f"Exam Q{number}", EXAM_ITEM, f"Assessment pack, Part 1 (Lesson {question['lesson']})",
                         stem, None, objs[0], [], 1, "Summative", note))
    for key, info in course.rubric.items():
        objs, note = rubric[key]
        a, r = key.split(".")
        evidence.append((f"A{a} R{r}", RUBRIC_ROW, info["assignment"], info["criterion"], None,
                         objs[0] if objs else None, objs[1:], info["points"], "Summative, rubric", note))

    summary = {}
    for o in spec["objectives"]:
        oid = o["id"]
        roles = {}  # page slug -> strongest role
        for slug, entries in spec["page_map"].items():
            for entry in entries:
                if entry[1] == oid:
                    best = roles.get(slug)
                    if best is None or "TIR".index(entry[2]) < "TIR".index(best):
                        roles[slug] = entry[2]
        taught = [f"{ROLES[code]}: " + _page_list([p for p in course.pages if roles.get(p.slug) == code])
                  for code in "TIR" if code in roles.values()]
        # Rule 1 of the mastery rule counts only the exercises on the pages that teach the objective.
        listed = [k for k, (objs, _) in exercises.items() if oid in objs]
        decisive = [k for k in listed if roles.get(course.exercises[k]["page"].slug) == "T"]
        further = [k for k in listed if k not in decisive]
        quiz_by_lesson = {}
        for key, (objs, _) in quiz.items():
            if objs == [oid]:
                lesson, number = key.split(".")
                quiz_by_lesson.setdefault(lesson, []).append(int(number))
        exam_hits = [int(k) for k, (objs, _) in exam.items() if objs == [oid]]
        rub_main = [k for k, (objs, _) in rubric.items() if objs[:1] == [oid]]
        rub_also = [k for k, (objs, _) in rubric.items() if oid in objs[1:]]

        def code(key):
            return "A{} R{}".format(*key.split("."))

        practice = []
        if listed:
            practice.append("Exercises for mastery: " + (", ".join(decisive) or "none"))
        if further:
            practice.append("Further practice: " + ", ".join(further))
        if not listed:
            practice.append("Exercises: none")
        quizzes = "; ".join(f"L{lesson} {_runs(qs, 'Q')}" for lesson, qs in sorted(quiz_by_lesson.items()))
        practice.append("Quiz: " + (quizzes or "none"))
        check = ["Exam: " + (_runs(exam_hits, "Q") or "none")]
        rub = ", ".join(code(k) for k in rub_main)
        if rub_also:
            rub += ("; also " if rub_main else "also ") + ", ".join(code(k) for k in rub_also)
        check.append("Rubric: " + (rub or "none"))

        teach = sum(1 for row in detail if row[4] == oid and row[3] == ROLES["T"])
        counts = {
            "goals": sum(1 for row in detail if row[4] == oid and row[3] == GOAL),
            "teach": teach,
            "exercises": len(listed),
            "quiz": sum(len(qs) for qs in quiz_by_lesson.values()),
            "exam": len(exam_hits),
            "rubric": len(rub_main) + len(rub_also),
        }
        if not teach:
            status = PLANNED
        elif counts["exercises"] and counts["exam"] + counts["rubric"]:
            status = COVERED
        else:
            status = PARTIAL
        written = bool(roles) or any(counts.values())
        summary[oid] = {
            **counts, "status": status, "roles": roles, "decisive": decisive,
            "existing": sum(split.get(oid, 0) for split in spec["lesson_minutes"].values()),
            "added": sum(a["minutes"] for a in spec.get("added_minutes") or [] if a["objective"] == oid),
            "taught": "\n".join(taught) if taught else "Not written yet",
            "practice": "\n".join(practice) if written else "None yet",
            "check": "\n".join(check) if written else "None yet",
        }
    return {"names": names, "detail": detail, "evidence": evidence, "summary": summary}


# ---------------------------------------------------------------- formulas that know their value

class F:
    """An Excel formula together with a way to work out the value it shows."""

    def __init__(self, text, compute, atomic=True):
        self.text, self._compute, self.atomic = text, compute, atomic

    @property
    def value(self):
        if not hasattr(self, "_value"):
            self._value = self._compute()
        return self._value


def _val(x):
    return x.value if isinstance(x, F) else x


def _txt(x):
    if isinstance(x, F):
        return x.text
    if isinstance(x, str):
        return '"' + x.replace('"', '""') + '"'
    return repr(x)


def _factor(x):
    return f"({x.text})" if isinstance(x, F) and not x.atomic else _txt(x)


def _sheet(name):
    return "'" + name.replace("'", "''") + "'"


class Grid:
    """A worksheet, plus a record of what each cell holds so that formulas can be evaluated."""

    def __init__(self, ws):
        self.ws, self.cells = ws, {}

    def put(self, row, col, value, **look):
        if isinstance(value, str) and value.startswith("="):
            raise ObjectivesError(f"{self.ws.title}: text starting with '=' would be read as a formula: {value!r}")
        cell = self.ws.cell(row=row, column=col)
        cell.value = "=" + value.text if isinstance(value, F) else value
        self.cells[(row, col)] = value
        dress(cell, **look)
        return cell

    def at(self, row, col):
        return _val(self.cells.get((row, col)))

    def ref(self, row, col, here=None, lock=""):
        """A reference to one cell. lock: '', 'row', 'col' or 'both' (the $ signs)."""
        a1 = (("$" if lock in ("col", "both") else "") + get_column_letter(col)
              + ("$" if lock in ("row", "both") else "") + str(row))
        return F(a1 if here in (None, self) else f"{_sheet(self.ws.title)}!{a1}", lambda: self.at(row, col))

    def col(self, col, first=None, last=None):
        return Col(self, col, first, last)

    def formulas(self):
        return {f"{get_column_letter(c)}{r}": v.value for (r, c), v in self.cells.items() if isinstance(v, F)}


class Col:
    """A whole column of a sheet, or rows first..last of it, as a range in a formula."""

    def __init__(self, grid, col, first=None, last=None):
        self.grid, self.col, self.first, self.last = grid, col, first, last

    def text(self, here):
        letter = get_column_letter(self.col)
        a1 = f"${letter}:${letter}" if self.first is None else f"${letter}${self.first}:${letter}${self.last}"
        return a1 if self.grid is here else f"{_sheet(self.grid.ws.title)}!{a1}"

    def rows(self):
        return {r: self.grid.at(r, c) for (r, c) in self.grid.cells
                if c == self.col and (self.first is None or self.first <= r <= self.last)}


def _matches(value, criterion):
    """Excel's test for a COUNTIFS/SUMIFS criterion: text ignores case, * and ? are wildcards."""
    if value is None or value == "":
        return False
    if not isinstance(criterion, str):
        return value == criterion
    if criterion[:1] in "=<>" or "~" in criterion:
        raise ObjectivesError(f"criterion {criterion!r} would be read by Excel as an operator or an escape")
    pattern = re.escape(criterion.lower()).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(pattern, str(value).lower(), flags=re.S) is not None


def _matching_rows(pairs):
    rows = None
    for rng, criterion in pairs:
        hit = {r for r, v in rng.rows().items() if _matches(v, _val(criterion))}
        rows = hit if rows is None else rows & hit
    return rows


def countifs(here, *pairs):
    """COUNTIFS over (Col, criterion) pairs."""
    text = "COUNTIFS(" + ",".join(f"{rng.text(here)},{_txt(c)}" for rng, c in pairs) + ")"
    return F(text, lambda: len(_matching_rows(pairs)))


def sumifs(here, total, *pairs):
    text = f"SUMIFS({total.text(here)}," + ",".join(f"{rng.text(here)},{_txt(c)}" for rng, c in pairs) + ")"

    def compute():
        rows, values = _matching_rows(pairs), total.rows()
        return sum(v for r, v in values.items() if r in rows and isinstance(v, (int, float)))

    return F(text, compute)


def sum_of(grid, row, first_col, last_col):
    """SUM over cells first_col..last_col of one row."""
    a1 = f"{get_column_letter(first_col)}{row}:{get_column_letter(last_col)}{row}"
    return F(f"SUM({a1})", lambda: sum(grid.at(row, c) or 0 for c in range(first_col, last_col + 1)))


def plus(*terms):
    return F("+".join(_txt(t) for t in terms), lambda: sum(_val(t) for t in terms), atomic=False)


def times(a, b):
    return F(f"{_factor(a)}*{_factor(b)}", lambda: _val(a) * _val(b), atomic=False)


def over(a, b):
    return F(f"{_factor(a)}/{_factor(b)}", lambda: _val(a) / _val(b), atomic=False)


def more_than(a, b):
    return F(f"{_txt(a)}>{_txt(b)}", lambda: _val(a) > _val(b), atomic=False)


def equal_to(a, b):
    return F(f"{_txt(a)}={_txt(b)}", lambda: _val(a) == _val(b), atomic=False)


def all_of(*conditions):
    return F("AND(" + ",".join(c.text for c in conditions) + ")", lambda: all(c.value for c in conditions))


def when(condition, then, otherwise):
    return F(f"IF({condition.text},{_txt(then)},{_txt(otherwise)})",
             lambda: _val(then) if condition.value else _val(otherwise))


def joined(*parts):
    return F("&".join(_txt(p) for p in parts), lambda: "".join(str(_val(p)) for p in parts), atomic=False)


# ---------------------------------------------------------------- how the cells look

ARIAL = "Arial"
INK, MUTED, WHITE, ACCENT, BLUE, RULE = "1F2328", "555B63", "FFFFFF", "0F7173", "0B57D0", "D0D5DA"


def font(size=10, bold=False, italic=False, color=INK, underline=None):
    return Font(name=ARIAL, size=size, bold=bold, italic=italic, color=color, underline=underline)


def fill(color):
    return PatternFill(fill_type="solid", start_color=color, end_color=color)


BODY, BOLD, HEAD, NOTE = font(), font(bold=True), font(bold=True, color=WHITE), font(9, color=MUTED)
TITLE, HEADING, LINK = font(14, bold=True), font(11, bold=True, color=ACCENT), font(color=BLUE, underline="single")
HEAD_FILL, INPUT_FILL, BAND_FILL = fill(ACCENT), fill("FFF6D9"), fill("EEF6F6")
SECTION_FILL = {"S": fill("DDEEEE"), "I": fill("EADFFB"), "D": fill("FFE8CC")}
STATUS_FILL = {COVERED: fill("DDF2E1"), PARTIAL: fill("FFEFC7"), PLANNED: fill("ECEEF1")}
ROLE_LOOK = {"T": (fill(ACCENT), font(bold=True, color=WHITE)), "I": (fill("A9D6D6"), font(bold=True)),
             "R": (fill("E3F1F1"), font())}
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(wrap_text=True, vertical="top", horizontal="center")
MIDDLE = Alignment(wrap_text=True, vertical="center")
MIDDLE_CENTER = Alignment(wrap_text=True, vertical="center", horizontal="center")
RUN_ON = Alignment(vertical="center")  # no wrapping: the text runs on over the empty cells to its right
_side = Side(style="thin", color=RULE)
BOX = Border(left=_side, right=_side, top=_side, bottom=_side)
UNDER = Border(bottom=Side(style="medium", color=ACCENT))


def dress(cell, font=BODY, fill=None, align=WRAP, border=None, fmt=None, link=None):
    cell.font, cell.alignment = (LINK if link and font is BODY else font), align
    if fill is not None:
        cell.fill = fill
    if border is not None:
        cell.border = border
    if fmt is not None:
        cell.number_format = fmt
    if link:
        cell.hyperlink = link


def header_row(grid, row, headers, first_col=1):
    for i, text in enumerate(headers):
        grid.put(row, first_col + i, text, font=HEAD, fill=HEAD_FILL, align=MIDDLE, border=BOX)
    grid.ws.row_dimensions[row].height = 32


def widths(ws, sizes):
    for i, width in enumerate(sizes, 1):
        ws.column_dimensions[get_column_letter(i)].width = width


def as_table(ws, name, first_row, last_row, columns):
    """An Excel table over the range: filter buttons, and headers a screen reader can announce."""
    table = Table(displayName=name, ref=f"A{first_row}:{get_column_letter(columns)}{last_row}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showFirstColumn=False, showLastColumn=False,
                                          showRowStripes=False, showColumnStripes=False)
    ws.add_table(table)


def for_print(ws, header_rows, pages_wide=1):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = pages_wide, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins = PageMargins(left=0.4, right=0.4, top=0.5, bottom=0.6)
    ws.oddFooter.center.text = "&A - page &P of &N"
    if header_rows:
        ws.print_title_rows = header_rows


def highlight(ws, cells, looks):
    """Color cells by what they say. The text carries the meaning; the color only helps the eye."""
    for text, look in looks.items():
        fill_, font_ = look if isinstance(look, tuple) else (look, None)
        ws.conditional_formatting.add(cells, CellIsRule(operator="equal", formula=[f'"{text}"'],
                                                        fill=fill_, font=font_))


# ---------------------------------------------------------------- the sheets

# (key, header, width, what the column holds). The Read me sheet prints the last part.
OBJECTIVE_COLUMNS = [
    ("id", "ID", 6, "A stable code: S is static, I is interactive, D is dashboards. A code is never reused."),
    ("name", "Objective", 30, "A short name."),
    ("section", "Section", 14, "The section of the larger course."),
    ("strand", "Strand", 11, "The thread the objective belongs to across the three sections (listed above)."),
    ("can", "The learner can ...", 50,
     "The objective itself: one performance an instructor can observe, with its conditions."),
    ("criteria", "Mastery looks like", 62, "What the instructor sees when the objective is met."),
    ("bloom", "Bloom level", 10, "The highest level of the revised Bloom taxonomy that the objective asks for."),
    ("shown_by", "Shown by", 15, "The kind of evidence that shows mastery (listed above)."),
    ("prerequisites", "Prerequisites", 13, "Objectives to master first."),
    ("tools", "Key tools", 40,
     "The functions and arguments the objective uses. Sections 2 and 3 are not written yet, so theirs are "
     "plans: assumption A4 names the libraries and the versions the names were checked against."),
    ("status", "Status", 10, "Covered, Partial or Planned. Worked out on the Page map sheet from the two maps."),
    ("taught", "Where it is taught", 24,
     "Pages by role. This is the corrective reading; the Page detail sheet lists the sections."),
    ("practice", "Practice today", 27,
     "Exercises whose automatic check tests the objective: first those on the pages that teach it, which "
     "decide mastery (rule 1 above), then those on other pages. Last, the quiz questions on it."),
    ("check", "Mastery check today", 24,
     "Exam questions and rubric rows mapped to the objective. The Evidence sheet explains the codes."),
    ("gap", "Gap today", 40, "What today's materials lack for this objective. Empty means nothing specific."),
    ("next_step", "Next step", 44, "What to add or decide."),
    ("existing", "Minutes: existing pages", 12,
     "Learner minutes in the existing lessons, summed from the table at the foot of the Timing sheet."),
    ("added", "Minutes: additions built", 12,
     "Learner minutes of what was added to a lesson after it was timed, such as a new exercise. They are "
     "counted on top of the lesson's 60 minutes, summed from the second table at the foot of the Timing sheet."),
    ("to_write", "Minutes: to write", 12,
     "Learner minutes that the next step would add. An estimate, and an input you can change."),
    ("total", "Minutes: total", 12, "Existing, plus additions built, plus to write."),
    ("outcome", "Guide outcome", 9, "The learning outcome (1-6) in the instructor guide that the objective refines."),
]
OBJ = {key: i for i, (key, *_rest) in enumerate(OBJECTIVE_COLUMNS, 1)}
OBJ_FIRST = 2  # first data row of the Objectives sheet

DETAIL_COLUMNS = [("Page", 12), ("Section of the page", 40), ("Role", 13), ("Objective ID", 10),
                  ("Objective", 34), ("Note, or the items", 70)]
DET_PAGE, DET_SECTION, DET_ROLE, DET_ID, DET_NAME, DET_NOTE = range(1, 7)

EVIDENCE_COLUMNS = [("Item", 14), ("Type", 14), ("Where", 30), ("Exercise title, question or rubric row", 62),
                    ("Primary objective", 10), ("Also evidence for", 14), ("Points", 8), ("Use", 30), ("Note", 50)]
EV_ITEM, EV_TYPE, EV_WHERE, EV_TEXT, EV_PRIMARY, EV_ALSO, EV_POINTS, EV_USE, EV_NOTE = range(1, 10)

MAP_HEADER, MAP_FIRST = 4, 5          # rows of the Page map sheet
MAP_ID, MAP_NAME, MAP_STATUS, MAP_PAGES = 1, 2, 3, 4   # columns; the pages start at MAP_PAGES
MAP_COUNTS = ("Lesson goals", "Teaching sections", "Exercises", "Quiz questions", "Exam questions", "Rubric rows")

T_LABEL, T_FIRST, T_ALL, T_BASIS = 1, 2, 5, 6     # columns of the Timing sheet (one per section from T_FIRST)
T_INPUTS, T_CHECK, T_PROJECT, T_ALLOW, T_SESSION = 4, 5, 6, 7, 8
T_RESULTS = 10
(T_COUNT, T_COVERED, T_PARTIAL, T_PLANNED, T_EXISTING, T_ADDED, T_TO_WRITE, T_CHECK_H, T_PROJECT_H, T_ALLOW_H,
 T_TOTAL, T_TAUGHT, T_SESSIONS) = range(11, 24)
T_SPLIT = 27  # header row of the table that splits each lesson's minutes; data from T_SPLIT + 1


def fill_page_detail(grid, joined_up):
    header_row(grid, 1, [h for h, _ in DETAIL_COLUMNS])
    for row, (page, section, link, role, objective, note) in enumerate(joined_up["detail"], 2):
        grid.put(row, DET_PAGE, page.label, border=BOX)
        grid.put(row, DET_SECTION, section, border=BOX, link=link)
        grid.put(row, DET_ROLE, role, border=BOX)
        grid.put(row, DET_ID, objective, border=BOX, align=CENTER,
                 fill=SECTION_FILL[objective[0]] if objective else None)
        grid.put(row, DET_NAME, joined_up["names"].get(objective), border=BOX)
        grid.put(row, DET_NOTE, note or None, border=BOX)
    last = 1 + len(joined_up["detail"])
    widths(grid.ws, [w for _, w in DETAIL_COLUMNS])
    grid.ws.freeze_panes = "C2"
    as_table(grid.ws, "PageDetailTable", 1, last, len(DETAIL_COLUMNS))
    for_print(grid.ws, "1:1")


def fill_evidence(grid, joined_up):
    header_row(grid, 1, [h for h, _ in EVIDENCE_COLUMNS])
    for row, (item, kind, where, text, link, primary, also, points, use, note) in enumerate(joined_up["evidence"], 2):
        grid.put(row, EV_ITEM, item, border=BOX, link=link)
        grid.put(row, EV_TYPE, kind, border=BOX)
        grid.put(row, EV_WHERE, where, border=BOX)
        grid.put(row, EV_TEXT, text, border=BOX)
        grid.put(row, EV_PRIMARY, primary, border=BOX, align=CENTER,
                 fill=SECTION_FILL[primary[0]] if primary else None)
        grid.put(row, EV_ALSO, ", ".join(also) or None, border=BOX)
        grid.put(row, EV_POINTS, points, border=BOX, align=CENTER)
        grid.put(row, EV_USE, use, border=BOX)
        grid.put(row, EV_NOTE, note or None, border=BOX)
    last = 1 + len(joined_up["evidence"])
    widths(grid.ws, [w for _, w in EVIDENCE_COLUMNS])
    grid.ws.freeze_panes = "B2"
    as_table(grid.ws, "EvidenceTable", 1, last, len(EVIDENCE_COLUMNS))
    for_print(grid.ws, "1:1")


def fill_page_map(grid, spec, course, joined_up, detail, evidence):
    ws, pages = grid.ws, course.pages
    first_count = MAP_PAGES + len(pages)
    last_col = first_count + len(MAP_COUNTS) - 1
    grid.put(1, 1, "Page map: which pages teach which objective", font=TITLE, align=RUN_ON)
    grid.put(2, 1, "T = teaches: the page has the main instruction for the objective or for one of its criteria.   "
                   "I = introduces: a preview before the objective's main lesson.   "
                   "R = reinforces: used again after it was taught.   "
                   "A cell shows the strongest role on the page. The Page detail sheet lists the sections, "
                   "and the Evidence sheet lists the exercises, questions and rubric rows that are counted here.",
             font=NOTE, align=MIDDLE)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
    ws.row_dimensions[2].height = 40
    grid.put(3, MAP_PAGES - 1, "Page:", font=BOLD, align=Alignment(horizontal="right", vertical="center"))
    for i, page in enumerate(pages):
        grid.put(3, MAP_PAGES + i, page.nav, font=LINK, align=MIDDLE_CENTER, link=page.url)
    grid.put(3, first_count, "Evidence in today's materials (counts)", font=BOLD, align=RUN_ON)
    ws.row_dimensions[3].height = 30
    header_row(grid, MAP_HEADER, ["ID", "Objective", "Status"] + [p.label for p in pages] + list(MAP_COUNTS))
    for c in range(MAP_PAGES, last_col + 1):
        ws.cell(row=MAP_HEADER, column=c).alignment = MIDDLE_CENTER

    def detail_count(obj, role, page=None):
        pairs = [(detail.col(DET_ID), obj), (detail.col(DET_ROLE), role)]
        if page is not None:
            pairs.insert(1, (detail.col(DET_PAGE), page))
        return countifs(grid, *pairs)

    def evidence_count(obj, kind):
        return plus(countifs(grid, (evidence.col(EV_TYPE), kind), (evidence.col(EV_PRIMARY), obj)),
                    countifs(grid, (evidence.col(EV_TYPE), kind), (evidence.col(EV_ALSO), joined("*", obj, "*"))))

    for i, o in enumerate(spec["objectives"]):
        row = MAP_FIRST + i
        obj = grid.ref(row, MAP_ID, lock="col")
        grid.put(row, MAP_ID, o["id"], font=BOLD, border=BOX, align=CENTER, fill=SECTION_FILL[o["id"][0]])
        grid.put(row, MAP_NAME, o["name"], border=BOX)
        for p in range(len(pages)):
            page = grid.ref(MAP_HEADER, MAP_PAGES + p, lock="row")
            role = ""
            for code in "RIT":  # built inside out, so that T wins over I and I over R
                role = when(more_than(detail_count(obj, ROLES[code], page), 0), code, role)
            grid.put(row, MAP_PAGES + p, role, border=BOX, align=CENTER)
        counts = [detail_count(obj, GOAL), detail_count(obj, ROLES["T"])]
        counts += [evidence_count(obj, kind) for kind in (EXERCISE, QUIZ_ITEM, EXAM_ITEM, RUBRIC_ROW)]
        for c, formula in enumerate(counts):
            grid.put(row, first_count + c, formula, border=BOX, align=CENTER)
        teach, exercises, exam, rubric = (grid.ref(row, first_count + n) for n in (1, 2, 4, 5))
        grid.put(row, MAP_STATUS, when(equal_to(teach, 0), PLANNED,
                                       when(all_of(more_than(exercises, 0), more_than(plus(exam, rubric), 0)),
                                            COVERED, PARTIAL)), border=BOX)
    last = MAP_FIRST + len(spec["objectives"]) - 1
    letter = get_column_letter
    highlight(ws, f"{letter(MAP_STATUS)}{MAP_FIRST}:{letter(MAP_STATUS)}{last}", STATUS_FILL)
    highlight(ws, f"{letter(MAP_PAGES)}{MAP_FIRST}:{letter(first_count - 1)}{last}", ROLE_LOOK)
    widths(ws, [6, 40, 10] + [13] * len(pages) + [10] * len(MAP_COUNTS))
    ws.freeze_panes = ws.cell(row=MAP_FIRST, column=MAP_STATUS)
    as_table(ws, "PageMapTable", MAP_HEADER, last, last_col)
    for_print(ws, f"{MAP_HEADER}:{MAP_HEADER}")


def fill_objectives(grid, spec, joined_up, page_map, timing, added_rows):
    ws = grid.ws
    header_row(grid, 1, [header for _, header, _, _ in OBJECTIVE_COLUMNS])
    section_label = {s["key"]: s["label"] for s in spec["sections"]}
    split_rows = sum(len(split) for split in spec["lesson_minutes"].values())
    split_obj = timing.col(2, T_SPLIT + 1, T_SPLIT + split_rows)
    split_min = timing.col(3, T_SPLIT + 1, T_SPLIT + split_rows)
    added_obj, added_min = timing.col(2, *added_rows), timing.col(3, *added_rows)
    for i, o in enumerate(spec["objectives"]):
        row, info = OBJ_FIRST + i, joined_up["summary"][o["id"]]
        text = {
            "name": o["name"], "section": section_label[o["id"][0]], "strand": o["strand"], "can": o["can"],
            "criteria": "\n".join(f"• {c}" for c in o["criteria"]), "bloom": o["bloom"],
            "shown_by": o["shown_by"], "prerequisites": ", ".join(o.get("prerequisites") or []) or None,
            "tools": o["tools"], "taught": info["taught"], "practice": info["practice"], "check": info["check"],
            "gap": o.get("gap") or None, "next_step": o.get("next_step") or None,
        }
        grid.put(row, OBJ["id"], o["id"], font=BOLD, border=BOX, align=CENTER, fill=SECTION_FILL[o["id"][0]])
        for key, value in text.items():
            grid.put(row, OBJ[key], value, border=BOX, font=BOLD if key == "name" else BODY)
        grid.put(row, OBJ["status"], page_map.ref(MAP_FIRST + i, MAP_STATUS, here=grid), border=BOX)
        grid.put(row, OBJ["existing"], sumifs(grid, split_min, (split_obj, grid.ref(row, OBJ["id"], lock="col"))),
                 border=BOX, align=CENTER)
        grid.put(row, OBJ["added"], sumifs(grid, added_min, (added_obj, grid.ref(row, OBJ["id"], lock="col"))),
                 border=BOX, align=CENTER)
        grid.put(row, OBJ["to_write"], o["to_write"], border=BOX, align=CENTER, fill=INPUT_FILL)
        grid.put(row, OBJ["total"], plus(grid.ref(row, OBJ["existing"]), grid.ref(row, OBJ["added"]),
                                         grid.ref(row, OBJ["to_write"])),
                 border=BOX, align=CENTER)
        grid.put(row, OBJ["outcome"], o.get("outcome"), border=BOX, align=CENTER)
    last = OBJ_FIRST + len(spec["objectives"]) - 1
    status = get_column_letter(OBJ["status"])
    highlight(ws, f"{status}{OBJ_FIRST}:{status}{last}", STATUS_FILL)
    widths(ws, [width for _, _, width, _ in OBJECTIVE_COLUMNS])
    ws.row_dimensions[1].height = 44
    ws.freeze_panes = "C2"
    as_table(ws, "ObjectivesTable", 1, last, len(OBJECTIVE_COLUMNS))
    for_print(ws, "1:1", pages_wide=2)
    ws.print_title_cols = "A:B"  # the id and the name repeat on the second page across


def fill_timing_split(grid, spec, course):
    """The tables at the foot of the Timing sheet: how each existing lesson's minutes divide, and what
    was added to a lesson since. Returns the first and the last row of the additions."""
    grid.put(T_SPLIT - 2, T_LABEL, "Where the existing lesson time goes (section 1)", font=HEADING, border=UNDER,
             align=RUN_ON)
    grid.put(T_SPLIT - 1, T_LABEL, spec["timing"]["lesson_basis"], font=NOTE)
    grid.ws.merge_cells(start_row=T_SPLIT - 1, start_column=T_LABEL, end_row=T_SPLIT - 1, end_column=T_BASIS)
    grid.ws.row_dimensions[T_SPLIT - 1].height = 54
    header_row(grid, T_SPLIT, ["Lesson", "Objective", "Minutes"])
    row = T_SPLIT
    for slug, split in spec["lesson_minutes"].items():
        page = course.page(slug)
        for objective, minutes in split.items():
            row += 1
            grid.put(row, 1, f"{page.label} - {page.nav}", border=BOX)
            grid.put(row, 2, objective, border=BOX, align=CENTER, fill=SECTION_FILL[objective[0]])
            grid.put(row, 3, minutes, border=BOX, align=CENTER, fill=INPUT_FILL)
    first, last = T_SPLIT + 1, row
    row += 2
    # Printed, the two small tables below used to start at the foot of one page and end on the next.
    grid.ws.row_breaks.append(Break(id=row - 1))
    grid.put(row, T_LABEL, "Additions built on top of the lessons (section 1)", font=HEADING, border=UNDER,
             align=RUN_ON)
    row += 1
    grid.put(row, T_LABEL, spec["timing"]["added_basis"], font=NOTE)
    grid.ws.merge_cells(start_row=row, start_column=T_LABEL, end_row=row, end_column=T_BASIS)
    grid.ws.row_dimensions[row].height = 28
    row += 1
    header_row(grid, row, ["Lesson", "Objective", "Minutes", "What was added"])
    grid.ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=T_BASIS)
    added_first = row + 1
    for added in spec.get("added_minutes") or [{"lesson": None, "objective": None, "minutes": None,
                                                 "what": "Nothing yet."}]:
        row += 1
        page = course.page(added["lesson"]) if added["lesson"] else None
        grid.put(row, 1, f"{page.label} - {page.nav}" if page else None, border=BOX)
        grid.put(row, 2, added["objective"], border=BOX, align=CENTER,
                 fill=SECTION_FILL[added["objective"][0]] if added["objective"] else None)
        grid.put(row, 3, added["minutes"], border=BOX, align=CENTER, fill=INPUT_FILL)
        grid.put(row, 4, added["what"], border=BOX)
        grid.ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=T_BASIS)
    added_rows = (added_first, row)
    row += 2
    grid.put(row, T_LABEL, "Check: every lesson's minutes add up to the midpoint", font=HEADING, border=UNDER,
             align=RUN_ON)
    row += 1
    header_row(grid, row, ["Lesson", "Minutes", "Midpoint"])
    for slug in spec["lesson_minutes"]:
        page = course.page(slug)
        row += 1
        grid.put(row, 1, f"{page.label} - {page.nav}", border=BOX)
        this_lesson = (grid.col(1, first, last), grid.ref(row, 1, lock="col"))
        grid.put(row, 2, sumifs(grid, grid.col(3, first, last), this_lesson), border=BOX, align=CENTER)
        grid.put(row, 3, LESSON_MIDPOINT, border=BOX, align=CENTER)
    return added_rows


def fill_timing(grid, spec, objectives):
    ws, timing, sections = grid.ws, spec["timing"], spec["sections"]
    cols = {s["key"]: T_FIRST + i for i, s in enumerate(sections)}
    last_section = T_FIRST + len(sections) - 1
    grid.put(1, 1, "Timing: learner hours by section", font=TITLE, align=RUN_ON)
    grid.put(2, 1, "Shaded cells are inputs: estimates and assumptions, each with its basis beside it. Everything "
                   "else on this sheet is a formula. A rebuild resets the inputs to the values in "
                   "instructor/mastery_objectives.yaml.", font=NOTE, align=MIDDLE)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=T_BASIS)
    ws.row_dimensions[2].height = 28

    labels = [s["label"] for s in sections]
    header_row(grid, T_INPUTS, ["Inputs"] + labels + ["", "Basis"])
    inputs = [
        (T_CHECK, "Section check (minutes)", timing["check_minutes"], "0", timing["check_basis"]),
        (T_PROJECT, "Project work (hours)", timing["project_hours"], "0.0", timing["project_basis"]),
        (T_ALLOW, "Reassessment allowance (share of lesson and check time)",
         {s["key"]: timing["allowance"] for s in sections}, "0%", timing["allowance_basis"]),
    ]
    for row, label, values, fmt, basis in inputs:
        grid.put(row, T_LABEL, label, border=BOX)
        for key, col in cols.items():
            grid.put(row, col, values[key], border=BOX, align=CENTER, fill=INPUT_FILL, fmt=fmt)
        grid.put(row, T_BASIS, basis, border=BOX, font=NOTE)
    grid.put(T_SESSION, T_LABEL, "Session length (minutes)", border=BOX)
    grid.put(T_SESSION, T_FIRST, timing["session_minutes"], border=BOX, align=CENTER, fill=INPUT_FILL, fmt="0")
    grid.put(T_SESSION, T_BASIS, timing["session_basis"], border=BOX, font=NOTE)

    header_row(grid, T_RESULTS, ["Results"] + labels + ["All sections", "How it is worked out"])
    section_col = objectives.col(OBJ["section"])
    status_col = objectives.col(OBJ["status"])

    def lesson_hours(key, col):
        return over(sumifs(grid, objectives.col(OBJ[key]), (section_col, grid.ref(T_RESULTS, col, lock="row"))), 60)

    rows = [
        (T_COUNT, "Objectives", "0", "Counted on the Objectives sheet.",
         lambda col: countifs(grid, (section_col, grid.ref(T_RESULTS, col, lock="row")))),
        (T_EXISTING, "Lesson time in the existing pages (hours)", "0.0",
         "Objectives sheet, 'Minutes: existing pages', divided by 60.", lambda col: lesson_hours("existing", col)),
        (T_ADDED, "Additions built on top of the lessons (hours)", "0.0",
         "Objectives sheet, 'Minutes: additions built', divided by 60. " + timing["added_basis"],
         lambda col: lesson_hours("added", col)),
        (T_TO_WRITE, "Lesson time still to write (hours)", "0.0",
         "Objectives sheet, 'Minutes: to write', divided by 60. " + timing["to_write_basis"],
         lambda col: lesson_hours("to_write", col)),
        (T_CHECK_H, "Section check (hours)", "0.0", "The input above, divided by 60.",
         lambda col: over(grid.ref(T_CHECK, col), 60)),
        (T_PROJECT_H, "Project work (hours)", "0.0", "The input above.", lambda col: grid.ref(T_PROJECT, col)),
        (T_ALLOW_H, "Reassessment allowance (hours)", "0.0", "The allowance times the lesson and check hours.",
         lambda col: times(grid.ref(T_ALLOW, col), plus(grid.ref(T_EXISTING, col), grid.ref(T_ADDED, col),
                                                        grid.ref(T_TO_WRITE, col), grid.ref(T_CHECK_H, col)))),
        (T_TOTAL, "Total learner time (hours)", "0.0", "The six rows above, added.",
         lambda col: plus(*(grid.ref(r, col) for r in (T_EXISTING, T_ADDED, T_TO_WRITE, T_CHECK_H, T_PROJECT_H,
                                                       T_ALLOW_H)))),
        (T_TAUGHT, "Of which taught and checked: lessons, check and allowance (hours)", "0.0",
         "The total without the project work, which is done outside class.",
         lambda col: plus(*(grid.ref(r, col) for r in (T_EXISTING, T_ADDED, T_TO_WRITE, T_CHECK_H, T_ALLOW_H)))),
        (T_SESSIONS, "The same in sessions", "0.0", "Taught and checked hours times 60, divided by the session length.",
         lambda col: over(times(grid.ref(T_TAUGHT, col), 60), grid.ref(T_SESSION, T_FIRST, lock="both"))),
    ]
    for status_row, status in ((T_COVERED, COVERED), (T_PARTIAL, PARTIAL), (T_PLANNED, PLANNED)):
        rows.append((status_row, f"   of which {status.lower()}", "0", "Status column of the Objectives sheet.",
                     lambda col, status=status: countifs(grid, (section_col, grid.ref(T_RESULTS, col, lock="row")),
                                                         (status_col, status))))
    for row, label, fmt, how, formula in rows:
        bold = row in (T_TOTAL,)
        grid.put(row, T_LABEL, label, border=BOX, font=BOLD if bold else BODY)
        for col in cols.values():
            grid.put(row, col, formula(col), border=BOX, align=CENTER, fmt=fmt, font=BOLD if bold else BODY)
        grid.put(row, T_ALL, sum_of(grid, row, T_FIRST, last_section), border=BOX, align=CENTER, fmt=fmt,
                 font=BOLD if bold else BODY, fill=BAND_FILL)
        grid.put(row, T_BASIS, how, border=BOX, font=NOTE)
    widths(ws, [58, 15, 15, 15, 15, 84])
    ws.freeze_panes = "B4"
    for_print(ws, None)


def fill_read_me(grid, spec, course):
    ws, meta = grid.ws, spec["meta"]
    site = course.pages[0].url.rsplit("/", 1)[0] + "/"
    count = len(spec["objectives"])
    row = 1
    grid.put(row, 1, f"{meta['title']}: {meta['course']}", font=font(16, bold=True), align=RUN_ON)
    ws.row_dimensions[1].height = 30

    def block(title, pairs):
        nonlocal row
        row += 2
        grid.put(row, 1, title, font=HEADING, border=UNDER, align=RUN_ON)
        grid.put(row, 2, None, border=UNDER)
        for label, text in pairs:
            row += 1
            grid.put(row, 1, label, font=BOLD)
            grid.put(row, 2, text)

    row -= 1  # the first block sits right under the title
    block("About this workbook", [
        ("What it is", f"{count} objectives for a course in three sections: static visualization, interactive "
                       "charts and dashboards. Section 1 is the Seaborn with Penguins site, and this workbook shows "
                       "which of its pages, exercises, quiz questions, exam questions and rubric rows serve which "
                       "objective. Sections 2 and 3 are not written yet: their objectives are here to plan from."),
        ("Version", f"{meta['version']}, {meta['date']}"),
        ("Where it comes from", "Generated from instructor/mastery_objectives.yaml by tools/build_objectives.py. "
                                "Change that file and run python tools/build_materials.py: edits made in this "
                                "workbook are lost at the next build."),
    ])
    block("The sheets", [
        ("Objectives", f"The {count} objectives, one per row: what the learner can do, what mastery looks like, "
                       "prerequisites, where it is taught, practiced and checked today, the gap and the next step."),
        ("Page map", "Objectives down, pages across: which page teaches, introduces or reinforces which objective, "
                     "with a count of the evidence for each and the status that follows from it."),
        ("Page detail", "The same map section by section, one row per page section and objective, with a link to "
                        "the section. Filter on an objective to get its corrective reading."),
        ("Evidence", "Every exercise, quiz question, exam question and rubric row, with the objective it gives "
                     "evidence for."),
        ("Timing", "Learner hours by section, from inputs you can change."),
    ])
    block("How mastery is decided", [(f"{n}.", text) for n, text in enumerate(spec["mastery_rule"], 1)])
    block("Assumptions", [(f"A{n}", text) for n, text in enumerate(spec["assumptions"], 1)])
    block("Status", [
        (COVERED, "The pages teach the objective, at least one checked exercise practices it, and at least one "
                  "exam question or rubric row assesses it."),
        (PARTIAL, "The pages teach it, but practice or assessment is missing. The 'Gap today' column says which."),
        (PLANNED, "No page teaches it yet."),
    ])
    block("Roles on the page sheets", [
        (f"{ROLES['T']} (T)", "The section holds the main instruction for the objective or for one of its criteria."),
        (f"{ROLES['I']} (I)", "A preview before the objective's main lesson."),
        (f"{ROLES['R']} (R)", "The objective is used again after it was taught."),
        (GOAL, "One of the page's own 'By the end of this lesson you can' bullets."),
        (PRACTICE, "An exercise in the section has an automatic check that tests the objective."),
        (QUIZ, "A quiz question in the section is about the objective."),
        (ROLES["O"], "The section serves no objective: prerequisites, navigation."),
    ])
    block("Strands", list(spec["strands"].items()))
    block("Shown by", list(spec["shown_by"].items()))
    block("Bloom level", [("Levels used", "Apply, Analyze, Evaluate and Create, from the revised Bloom taxonomy "
                                          "(Anderson and Krathwohl, 2001). An objective is tagged with the highest "
                                          "level it asks for.")])
    block("Columns of the Objectives sheet", [(header, about) for _, header, _, about in OBJECTIVE_COLUMNS])
    block("Evidence codes", [
        ("Ex 2.1", "Exercise 2.1 on the Lesson 2 page."),
        ("Quiz L2 Q3", "Question 3 of the Lesson 2 quiz."),
        ("Exam Q5", "Question 5 of the 25-question exam in the assessment pack."),
        ("A1 R2", "Assignment 1, second row of its rubric."),
    ])
    row += 2
    grid.put(row, 1, "Links", font=HEADING, border=UNDER)
    grid.put(row, 2, None, border=UNDER)
    for label, url in (("The site", site), ("Instructor guide", f"{site}instructor-guide.html")):
        row += 1
        grid.put(row, 1, label, font=BOLD)
        grid.put(row, 2, url, link=url)
    widths(ws, [26, 112])
    ws.sheet_view.showGridLines = False
    for_print(ws, None)


# ---------------------------------------------------------------- the file

_FORMULA_CELL = re.compile(r"<c (?P<attrs>[^>]*)>(?P<formula><f>.*?</f>)<v\s*(?:/>|>\s*</v>)</c>", re.S)


def _with_results(xml, results, sheet):
    """Put each formula's value beside it, as Excel does when it saves."""
    seen = set()

    def stored(match):
        attrs = match.group("attrs")
        ref = re.search(r'\br="([A-Z]+[0-9]+)"', attrs).group(1)
        value = results[ref]
        seen.add(ref)
        if isinstance(value, bool):
            return f'<c {attrs} t="b">{match.group("formula")}<v>{int(value)}</v></c>'
        if isinstance(value, str):
            return f'<c {attrs} t="str">{match.group("formula")}<v>{escape(value)}</v></c>'
        return f'<c {attrs}>{match.group("formula")}<v>{value!r}</v></c>'

    out = _FORMULA_CELL.sub(stored, xml)
    if seen != set(results):
        raise ObjectivesError(f"{sheet}: could not store the results of {sorted(set(results) - seen)[:5]}")
    return out


def _repack(raw, results_by_part, stamp):
    """Rewrite the saved workbook with formula results stored and nothing that depends on the clock."""
    source = zipfile.ZipFile(io.BytesIO(raw))
    out = io.BytesIO()
    when_text = datetime.datetime(*stamp).strftime("%Y-%m-%dT%H:%M:%SZ")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename in results_by_part:
                sheet, results = results_by_part[info.filename]
                data = _with_results(data.decode("utf-8"), results, sheet).encode("utf-8")
            elif info.filename == "docProps/core.xml":
                text, changed = re.subn(r"(<dcterms:(created|modified)\b[^>]*>)[^<]*(</dcterms:\2>)",
                                        rf"\g<1>{when_text}\g<3>", data.decode("utf-8"))
                if changed != 2:
                    raise ObjectivesError("docProps/core.xml: expected a created and a modified date")
                data = text.encode("utf-8")
            entry = zipfile.ZipInfo(info.filename, date_time=stamp)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 0  # the same on Windows and Linux
            target.writestr(entry, data)
    return out.getvalue()


def build(spec=None, course=None):
    """The workbook as bytes."""
    spec = spec or load_spec()
    course = course or read_course()
    validate(spec, course)
    joined_up = assemble(spec, course)

    wb = Workbook()
    wb.remove(wb.active)
    grids = {name: Grid(wb.create_sheet(name)) for name in SHEETS}
    tabs = {"Read me": MUTED, "Objectives": ACCENT, "Page map": "A034F0", "Page detail": "A034F0",
            "Evidence": "FF8C00", "Timing": MUTED}
    for name, color in tabs.items():
        grids[name].ws.sheet_properties.tabColor = color

    # Data first, then the sheets whose formulas read it.
    fill_page_detail(grids["Page detail"], joined_up)
    fill_evidence(grids["Evidence"], joined_up)
    added_rows = fill_timing_split(grids["Timing"], spec, course)
    fill_page_map(grids["Page map"], spec, course, joined_up, grids["Page detail"], grids["Evidence"])
    fill_objectives(grids["Objectives"], spec, joined_up, grids["Page map"], grids["Timing"], added_rows)
    fill_timing(grids["Timing"], spec, grids["Objectives"])
    fill_read_me(grids["Read me"], spec, course)

    meta = spec["meta"]
    made = datetime.datetime.strptime(str(meta["date"]), "%Y-%m-%d")
    wb.properties.title = f"{meta['title']}: {meta['course']}"
    wb.properties.creator = "Seaborn with Penguins"
    wb.properties.created = made
    raw = io.BytesIO()
    wb.save(raw)
    results = {f"xl/worksheets/sheet{n}.xml": (name, grids[name].formulas()) for n, name in enumerate(SHEETS, 1)}
    return _repack(raw.getvalue(), results, made.timetuple()[:6])


def write(path=OUTPUT):
    path.write_bytes(build())
    return path


def main():
    try:
        path = write()
    except ObjectivesError as exc:
        print(f"OBJECTIVES BUILD FAILED\n{exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  wrote instructor/{path.name}")


if __name__ == "__main__":
    main()
