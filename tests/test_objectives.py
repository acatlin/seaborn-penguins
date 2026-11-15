"""Validate the mastery objectives, their map onto the course, the workbook built from
them, and what the instructor guide says about them."""
import copy
import io
import re
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from xml.etree import ElementTree

import pytest
from conftest import ROOT
from openpyxl import load_workbook

import build_objectives as bo

SPEC = bo.load_spec()
COURSE = bo.read_course()
OBJECTIVES = SPEC["objectives"]
IDS = [o["id"] for o in OBJECTIVES]
STATIC = [i for i in IDS if i.startswith("S")]
GUIDE = (ROOT / "content" / "instructor-guide.md").read_text(encoding="utf-8")
WORDS = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 7: "seven", 9: "nine", 10: "ten", 12: "twelve",
         14: "fourteen"}
SIZES = {"S": 14, "I": 12, "D": 12}  # objectives per section


@pytest.fixture(scope="module")
def joined():
    bo.validate(SPEC, COURSE)
    return bo.assemble(SPEC, COURSE)


@pytest.fixture(scope="module")
def book():
    data = bo.build(SPEC, COURSE)
    return {"bytes": data, "formulas": load_workbook(io.BytesIO(data)),
            "values": load_workbook(io.BytesIO(data), data_only=True)}


# ---------------------------------------------------------------- the objectives

def test_thirty_eight_objectives_in_three_sections():
    """Section 1 has fourteen since S05 and S12 were split: a code is never reused, so the two
    halves that were split off are S13 and S14."""
    assert IDS == [f"{key}{n:02d}" for key, size in SIZES.items() for n in range(1, size + 1)]
    assert len({o["name"] for o in OBJECTIVES}) == len(IDS) == 38, "two objectives share a name"


VAGUE = re.compile(r"\b(understands?|knows?|learns?|appreciates?|is aware|is familiar|grasps?)\b", re.I)


def test_every_objective_is_something_an_instructor_can_observe():
    """'Understand' and 'know' cannot be seen. An objective has to name a performance."""
    for o in OBJECTIVES:
        vague = VAGUE.search(o["can"])
        assert not vague, f"{o['id']}: '{vague.group()}' cannot be observed"
        assert o["can"][0].isupper() and o["can"].endswith("."), f"{o['id']}: write a full sentence"
        assert 3 <= len(o["criteria"]) <= 5, f"{o['id']}: give three to five criteria"
        assert o["bloom"] in ("Apply", "Analyze", "Evaluate", "Create"), (
            f"{o['id']}: the Read me sheet says which Bloom levels are used; change it too")


def test_static_objectives_refine_the_six_outcomes_of_the_guide():
    listed = GUIDE.split("### Learning outcomes")[1].split("\n## ")[0]
    assert re.findall(r"^(\d)\. ", listed, flags=re.M) == list("123456")
    outcome = {o["id"]: o["outcome"] for o in OBJECTIVES}
    assert {outcome[i] for i in STATIC} == set(range(1, 7)), "every outcome needs an objective"
    assert all(outcome[i] is None for i in IDS if i not in STATIC), "the guide has no outcomes for sections 2 and 3"


# ---------------------------------------------------------------- the maps

def test_the_maps_agree_with_the_course():
    bo.validate(SPEC, COURSE)  # raises, listing every disagreement


def test_the_build_refuses_a_map_that_disagrees_with_the_course():
    """The check above must be able to fail: break the map seven ways and expect seven complaints."""
    broken = copy.deepcopy(SPEC)
    del broken["evidence"]["exercises"]["2.1"]
    broken["evidence"]["exam"][5] = ["S03", "S04"]
    broken["evidence"]["quiz"]["9.9"] = "S01"
    broken["page_map"]["01-first-plot"].append(["no-such-section", "S01", "T"])
    broken["page_map"]["07-capstone"] = [e for e in broken["page_map"]["07-capstone"] if e[0] != "where-to-next"]
    broken["lesson_goals"]["06-polish"].pop()
    broken["objectives"][0]["prerequisites"] = ["S05"]
    with pytest.raises(bo.ObjectivesError) as caught:
        bo.validate(broken, COURSE)
    for complaint in ("exercises: '2.1' is not mapped", "exam 5: map it to exactly one objective",
                      "quiz: '9.9' does not exist", "no section '#no-such-section'",
                      "section '#where-to-next' is not mapped", "lesson_goals 06-polish",
                      "S01: prerequisite S05"):
        assert complaint in str(caught.value), complaint


def _ids(path):
    return set(re.findall(r'\sid="([^"]+)"', path.read_text(encoding="utf-8")))


def test_everything_mapped_is_on_the_built_site(built_site, book):
    """The builder reads the lesson sources itself. Check its reading against the site build."""
    out, reports = built_site["out"], built_site["reports"]
    ids = {p.slug: _ids(out / f"{p.slug}.html") for p in COURSE.pages}
    for slug, entries in SPEC["page_map"].items():
        for anchor, *_rest in entries:
            assert anchor == "*" or anchor in ids[slug], f"{slug}.html has no section #{anchor}"
    assert sorted(COURSE.exercises) == sorted(e for r in reports.values() for e in r.exercises)
    assert len(COURSE.quiz) == sum(len(r.quiz_answers) for r in reports.values())
    base = COURSE.pages[0].url.rsplit("/", 1)[0] + "/"
    links = 0
    for ws in book["formulas"].worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.hyperlink is None:
                    continue
                links += 1
                target = cell.hyperlink.target
                assert target.startswith(base), f"{ws.title} {cell.coordinate}: {target}"
                page, _, fragment = target[len(base):].partition("#")
                assert not page or (out / page).is_file(), f"{ws.title} {cell.coordinate}: no page {page}"
                assert not fragment or fragment in _ids(out / page), f"{ws.title} {cell.coordinate}: no anchor {target}"
    assert links > 150, "the page and evidence sheets should link to the site"


def test_every_lesson_goal_belongs_to_a_static_objective(joined):
    """The pages' own 'By the end of this lesson you can' bullets are the first test of the static
    objectives: every objective that a page teaches is some page's stated goal."""
    goals = [objective for mapped in SPEC["lesson_goals"].values() for objective in mapped]
    assert len(goals) == sum(len(p.goals) for p in COURSE.pages)
    taught = {i for i in STATIC if joined["summary"][i]["teach"]}
    assert set(goals) == taught, "every static objective that a page teaches should be some page's stated goal"
    assert set(STATIC) == taught, "a static objective is no longer taught by any page"


def test_each_existing_lesson_is_split_into_its_sixty_minutes():
    assert list(SPEC["lesson_minutes"]) == [p.slug for p in COURSE.pages if p.num != "0"]
    for slug, split in SPEC["lesson_minutes"].items():
        assert sum(split.values()) == bo.LESSON_MIDPOINT, slug


def test_additions_are_counted_on_top_of_the_lessons(joined):
    """PLAN.md, question 2: a lesson stays at 60 minutes, and what is added to it later is counted in
    a block of its own. Section 1's additions were planned at 65 minutes. Building one moves its
    minutes from the objective's 'to write' to 'additions built', so the two always add up to 65."""
    added = SPEC["added_minutes"]
    assert len(added) == 5, "exercises 6.3, 6.4 and 7.2, and Step 5 of Lesson 7 for S12 and for S14"
    for item in added:
        assert item["lesson"] in SPEC["lesson_minutes"] and item["objective"] in STATIC
        assert joined["summary"][item["objective"]]["roles"].get(item["lesson"]) == "T", (
            f"{item['what']}: {item['lesson']} does not teach {item['objective']}")
    built = sum(item["minutes"] for item in added)
    assert built == sum(joined["summary"][i]["added"] for i in IDS)
    assert built + sum(o["to_write"] for o in OBJECTIVES if o["id"] in STATIC) == 65


def test_status_follows_from_the_evidence(joined):
    """All fourteen static objectives are covered: S09 since exercise 7.2 and the short task
    'Questions only', S12 and S14 since Step 5 of Lesson 7 and exercise 7.3 (PLAN.md, steps C and D).
    If a change to a section, an exercise or a question takes one of them back to Partial, this test
    says so: change it and the instructor guide only if that is meant."""
    status = {i: joined["summary"][i]["status"] for i in IDS}
    assert {i: status[i] for i in STATIC if status[i] != bo.COVERED} == {}
    assert all(status[i] == bo.PLANNED for i in IDS if i not in STATIC)


def test_rule_one_waits_only_for_exercises_on_the_pages_that_teach_the_objective(joined, book):
    """Rule 1 used to read 'every exercise listed for it', and could not be followed: S02 waited
    for an exercise in Lesson 6, while Lessons 2 to 6 teach objectives that need S02 first. It now
    counts the exercises on the pages that teach the objective. If a change to the page map or to
    the evidence map moves an exercise in or out on purpose, change this test and the guide."""
    summary = joined["summary"]
    assert "on the pages that teach it" in SPEC["mastery_rule"][0]
    assert {i: summary[i]["decisive"] for i in STATIC} == {
        "S01": ["1.1", "1.2"], "S02": ["1.1", "1.2"], "S03": ["2.1", "2.2"], "S04": ["3.1", "3.2"],
        "S05": ["1.2", "4.2"], "S06": ["5.1", "5.2"], "S07": ["1.1", "3.1", "3.2", "6.1", "6.2"],
        "S08": ["6.1", "6.2", "6.3"], "S09": ["7.2"], "S10": ["7.1"], "S11": ["6.1", "6.4"], "S12": ["7.3"],
        "S13": ["4.1"], "S14": ["7.3"]}
    # One pair is known, and was decided (REVIEW.md, O10, and PLAN.md, question 10): S11 lists S09 as
    # a prerequisite, and S11 is first taught by the makeover in Lesson 6, one lesson before the page
    # that teaches S09 and holds its exercise. The map stays as it is, because a full critique does
    # judge the chart's form. Nothing deadlocks: S09 needs nothing from S11, and S11's mastery check
    # is given after Lesson 7. Any other pair is a mistake in the map.
    decided = {("S11", "S09"): ["7.2"]}
    order = [p.slug for p in COURSE.pages]
    page_of = {key: order.index(info["page"].slug) for key, info in COURSE.exercises.items()}
    found = {}
    for o in OBJECTIVES:
        teaching = [n for n, slug in enumerate(order) if summary[o["id"]]["roles"].get(slug) == "T"]
        for needed in (o["prerequisites"] if teaching else []):
            late = [key for key in summary[needed]["decisive"] if page_of[key] > teaching[0]]
            if late:
                found[(o["id"], needed)] = late
    assert found == decided, ("an objective needs another one first, but mastery of that one waits for an "
                              f"exercise on a later page: {found}")
    sheet = book["values"]["Objectives"]
    shown = {sheet.cell(row=r, column=bo.OBJ["id"]).value: sheet.cell(row=r, column=bo.OBJ["practice"]).value
             for r in range(bo.OBJ_FIRST, sheet.max_row + 1)}
    assert shown["S02"].splitlines() == ["Exercises for mastery: 1.1, 1.2",
                                         "Further practice: 2.1, 3.1, 3.2, 4.2, 5.1, 6.1, 6.2", "Quiz: L1 Q3"]
    assert shown["S09"].splitlines()[0] == "Exercises for mastery: 7.2"
    assert shown["S12"].splitlines()[0] == "Exercises for mastery: 7.3"
    assert shown["I01"].splitlines()[0] == "Exercises: none" and shown["I02"] == "None yet"
    assert f"for S02, those are exercises {' and '.join(summary['S02']['decisive'])}." in GUIDE


def test_evidence_shows_the_code_an_exam_question_is_about(joined):
    """A stem such as 'What is the main problem with this chart?' says nothing without its chart."""
    shown = {item: text for item, _kind, _where, text, *_rest in joined["evidence"]}
    with_code = [(number, q["code"].strip()) for number, q in enumerate(COURSE.exam, 1) if q.get("code")]
    assert with_code, "no exam question has a code block any more: this test can go"
    for number, code in with_code:
        assert code in shown[f"Exam Q{number}"], f"Exam Q{number} is listed without its code"


def test_section_two_is_written_for_plotly():
    """Section 2 uses Plotly (decided on 2026-11-15). The alternative that was weighed for linked views
    is named once, in the assumption about tools, and no interactive objective lists its functions."""
    section = next(s for s in SPEC["sections"] if s["key"] == "I")
    assert section["tools"] == "Plotly."
    interactive = [o for o in OBJECTIVES if o["id"].startswith("I")]
    assert not [o["id"] for o in interactive if "Altair" in o["tools"]], "an interactive objective still lists Altair"
    assert sum(1 for o in interactive if "Plotly" in o["tools"]) >= 9, "the interactive objectives should name Plotly's tools"
    assert sum("Altair" in text for text in SPEC["assumptions"]) == 1


def test_section_three_is_written_for_streamlit():
    """Section 3 uses Streamlit. The alternative framework is named once, in the assumption about
    tools (which the guide repeats word for word), and nowhere else in the objectives or the guide."""
    source = bo.SOURCE.read_text(encoding="utf-8")
    assert len(re.findall(r"\bDash\b", source)) <= 1, "mastery_objectives.yaml names Dash more than once"
    assert len(re.findall(r"\bDash\b", GUIDE)) <= 1, "the instructor guide names Dash more than once"
    apps = [o for o in OBJECTIVES if o["id"].startswith("D") and o["tools"].startswith(("Streamlit", "pytest"))]
    assert len(apps) >= 9, "the dashboard objectives should name Streamlit's own tools"


# ---------------------------------------------------------------- the workbook

def test_workbook_has_its_sheets_and_every_objective(book):
    assert book["formulas"].sheetnames == list(bo.SHEETS)
    ws = book["values"]["Objectives"]
    assert [c.value for c in ws[1]] == [header for _, header, _, _ in bo.OBJECTIVE_COLUMNS]
    assert [ws.cell(row=r, column=bo.OBJ["id"]).value for r in range(bo.OBJ_FIRST, ws.max_row + 1)] == IDS
    always = ("name", "section", "strand", "can", "criteria", "bloom", "shown_by", "tools", "status", "taught",
              "practice", "check", "existing", "to_write", "total")
    for row in range(bo.OBJ_FIRST, ws.max_row + 1):
        empty = [key for key in always if ws.cell(row=row, column=bo.OBJ[key]).value in (None, "")]
        assert not empty, f"Objectives row {row}: {empty} empty"
    for sheet in book["formulas"].worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                assert cell.value is None or cell.font.name == "Arial", f"{sheet.title} {cell.coordinate}"


def test_page_map_and_objectives_show_what_the_maps_say(book, joined):
    """The counts, roles and statuses in the workbook are formulas. Their stored results
    are compared here with figures worked out straight from the YAML."""
    summary = joined["summary"]
    page_map = book["values"]["Page map"]
    headers = [c.value for c in page_map[bo.MAP_HEADER]]
    for i, oid in enumerate(IDS):
        shown = dict(zip(headers, (c.value for c in page_map[bo.MAP_FIRST + i])))
        expected = summary[oid]
        assert (shown["ID"], shown["Status"]) == (oid, expected["status"])
        for page in COURSE.pages:
            assert (shown[page.label] or "") == expected["roles"].get(page.slug, ""), (oid, page.label)
        assert [shown[h] for h in bo.MAP_COUNTS] == [
            expected[k] for k in ("goals", "teach", "exercises", "quiz", "exam", "rubric")], oid
    sheet = book["values"]["Objectives"]
    for i, o in enumerate(OBJECTIVES):
        row, expected = bo.OBJ_FIRST + i, summary[o["id"]]
        assert sheet.cell(row=row, column=bo.OBJ["status"]).value == expected["status"]
        assert sheet.cell(row=row, column=bo.OBJ["existing"]).value == expected["existing"]
        assert sheet.cell(row=row, column=bo.OBJ["added"]).value == expected["added"]
        assert sheet.cell(row=row, column=bo.OBJ["total"]).value == (
            expected["existing"] + expected["added"] + o["to_write"])


def hours_by_section(joined):
    """The Timing sheet's results, worked out here without the workbook."""
    timing, out = SPEC["timing"], {}
    for section in SPEC["sections"]:
        key = section["key"]
        mine = [o for o in OBJECTIVES if o["id"].startswith(key)]
        row = {
            "objectives": len(mine),
            "existing": sum(joined["summary"][o["id"]]["existing"] for o in mine) / 60,
            "added": sum(joined["summary"][o["id"]]["added"] for o in mine) / 60,
            "to_write": sum(o["to_write"] for o in mine) / 60,
            "check": timing["check_minutes"][key] / 60,
            "projects": timing["project_hours"][key],
        }
        row["lessons"] = row["existing"] + row["added"] + row["to_write"]
        row["allowance"] = timing["allowance"] * (row["lessons"] + row["check"])
        row["taught"] = row["lessons"] + row["check"] + row["allowance"]
        row["total"] = row["taught"] + row["projects"]
        out[section["label"]] = row
    out["All sections"] = {k: sum(row[k] for row in out.values()) for k in next(iter(out.values()))}
    return out


def test_timing_sheet_adds_up(book, joined):
    sheet = book["values"]["Timing"]
    column = {sheet.cell(row=bo.T_RESULTS, column=c).value: c for c in range(bo.T_FIRST, bo.T_ALL + 1)}
    rows = {"objectives": bo.T_COUNT, "existing": bo.T_EXISTING, "added": bo.T_ADDED, "to_write": bo.T_TO_WRITE,
            "check": bo.T_CHECK_H,
            "projects": bo.T_PROJECT_H, "allowance": bo.T_ALLOW_H, "total": bo.T_TOTAL, "taught": bo.T_TAUGHT}
    for label, expected in hours_by_section(joined).items():
        for key, row in rows.items():
            assert sheet.cell(row=row, column=column[label]).value == pytest.approx(expected[key]), (label, key)
        sessions = expected["taught"] * 60 / SPEC["timing"]["session_minutes"]
        assert sheet.cell(row=bo.T_SESSIONS, column=column[label]).value == pytest.approx(sessions), label
    counted = {status: sheet.cell(row=row, column=column["All sections"]).value
               for status, row in ((bo.COVERED, bo.T_COVERED), (bo.PARTIAL, bo.T_PARTIAL), (bo.PLANNED, bo.T_PLANNED))}
    assert counted == {bo.COVERED: 14, bo.PARTIAL: 0, bo.PLANNED: 24}


def test_every_formula_has_its_result_stored_in_the_file(book):
    """openpyxl saves a formula without its value. The build stores one, so that a viewer
    that does not calculate still shows the numbers. An empty result has to be marked as text."""
    archive = zipfile.ZipFile(io.BytesIO(book["bytes"]))
    formulas = 0
    for name in archive.namelist():
        if not name.startswith("xl/worksheets/sheet"):
            continue
        xml = archive.read(name).decode("utf-8")
        formulas += xml.count("<f>")
        for attrs in re.findall(r"<c ([^>]*)><f>(?:(?!</f>).)*</f><v\s*(?:/>|>\s*</v>)</c>", xml, flags=re.S):
            assert 't="str"' in attrs, f"{name}: a formula without a stored result ({attrs})"
    assert formulas > 600
    errors = [(ws.title, c.coordinate) for ws in book["values"].worksheets for row in ws.iter_rows() for c in row
              if isinstance(c.value, str) and c.value.startswith("#")]
    assert not errors, f"formula errors: {errors[:5]}"


def test_workbook_build_is_reproducible(book):
    assert bo.build(SPEC, COURSE) == book["bytes"]


def _parts(data):
    """Every part of a workbook as canonical XML, which is the same whichever XML library wrote it."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: ElementTree.canonicalize(archive.read(name).decode("utf-8")) for name in archive.namelist()}


def test_committed_workbook_matches_its_sources(book):
    """instructor/Seaborn_Mastery_Objectives.xlsx is generated: it has to be rebuilt after any
    change to the objectives, the lessons, the exam or the assignments. Every part of the
    file is compared (cells, formats, links), as canonical XML rather than bytes: the
    compression, and the XML library openpyxl finds, differ from one machine to the next."""
    assert bo.OUTPUT.is_file(), "run python tools/build_materials.py and commit the workbook"
    committed, fresh = _parts(bo.OUTPUT.read_bytes()), _parts(book["bytes"])
    stale = sorted(name for name in set(committed) | set(fresh) if committed.get(name) != fresh.get(name))
    assert not stale, ("run python tools/build_materials.py and commit instructor/Seaborn_Mastery_Objectives.xlsx; "
                       f"these parts of it are out of date: {stale}")


# ---------------------------------------------------------------- the instructor guide

def _count(n, noun):
    return f"no {noun}" if n == 0 else f"{n} {noun}" + ("" if n == 1 else "s")


def _table_rows(first_cell):
    """Rows of a Markdown table in the guide whose first cell matches the pattern."""
    rows = []
    for line in GUIDE.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and re.fullmatch(first_cell, cells[0]):
            rows.append(cells)
    return rows


def test_guide_table_of_static_objectives_matches_the_map(joined):
    rows = _table_rows(r"\*\*S\d\d\*\* .*")
    assert len(rows) == len(STATIC)
    for o, (objective, taught, evidence, status) in zip(OBJECTIVES, rows):
        info = joined["summary"][o["id"]]
        assert objective == f"**{o['id']}** {o['name']}"
        pages = [p for p in COURSE.pages if info["roles"].get(p.slug) == "T"]
        assert taught == (bo._page_list(pages) or "No page yet"), o["id"]
        counted = [_count(info["exercises"], "exercise"), _count(info["quiz"], "quiz question"),
                   _count(info["exam"], "exam question"), _count(info["rubric"], "rubric row")]
        assert evidence == ", ".join(counted), o["id"]
        assert status == info["status"], o["id"]


def test_guide_lists_the_objectives_of_sections_two_and_three():
    names = {o["id"]: o["name"] for o in OBJECTIVES}
    rows = _table_rows(r"\*\*I\d\d\*\* .*")
    assert rows == [[f"**I{n:02d}** {names[f'I{n:02d}']}", f"**D{n:02d}** {names[f'D{n:02d}']}"] for n in range(1, 13)]


def test_guide_repeats_the_mastery_rule_and_the_assumptions_word_for_word():
    for sentence in SPEC["mastery_rule"] + SPEC["assumptions"]:
        assert sentence in GUIDE, f"the guide and mastery_objectives.yaml disagree on: {sentence[:70]}..."
    assert f"rest on {WORDS[len(SPEC['assumptions'])]} assumptions" in GUIDE


def _shown(hours):
    """A number of hours as Excel shows it with one decimal: 15 significant digits, halves rounded up."""
    return str(Decimal(f"{hours:.15g}").quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def test_guide_timings_match_the_timing_sheet(joined):
    hours = hours_by_section(joined)
    for label, expected in hours.items():
        (row,) = [r for r in _table_rows(re.escape(label)) if len(r) == 7]
        assert row[1:] == [str(expected["objectives"])] + [
            f"{_shown(expected[key])} h" for key in ("lessons", "check", "projects", "allowance", "total")], label
    everything, static = hours["All sections"], hours["1 Static"]
    lessons = sum(1 for p in COURSE.pages if p.num != "0")
    assert (f"of section 1's {_shown(static['lessons'])} hours, {_shown(static['existing'])} are the {WORDS[lessons]} "
            f"lessons ({lessons * 45 / 60:g} to {lessons * 75 / 60:g} at the ends of the 45-75 minute range). "
            f"Another {round(static['added'] * 60)} minutes are built on top of them") in GUIDE
    if static["to_write"]:
        assert f"The remaining {round(static['to_write'] * 60)} minutes are the additions" in GUIDE
    else:
        assert "Nothing of section 1's lessons is left to write" in GUIDE
    sessions = everything["taught"] * 60 / SPEC["timing"]["session_minutes"]
    assert (f"Of the {_shown(everything['total'])} hours, {_shown(everything['taught'])} are lessons, checks and "
            f"reassessment. That is about {round(sessions)} sessions of {SPEC['timing']['session_minutes']} minutes"
            ) in GUIDE
    assert f"The {_shown(everything['projects'])} hours of project work" in GUIDE
    assert f"an allowance of {SPEC['timing']['allowance']:.0%} of lesson and check time" in GUIDE


def test_guide_counts_match_the_course(joined):
    exam = {i: joined["summary"][i]["exam"] for i in STATIC}
    rubric = bo.evidence_of(SPEC, "rubric")
    assert (f"Each of the {sum(len(p.goals) for p in COURSE.pages)} lesson goals" in GUIDE
            and f"the {len(COURSE.exercises)} exercises, the {len(COURSE.quiz)} quiz questions and the "
                f"{len(COURSE.exam)} exam questions" in GUIDE)
    assert f"{sum(1 for objs, _ in rubric.values() if objs)} of the {len(rubric)} rubric rows" in GUIDE
    assert (f"questions on {WORDS[sum(1 for n in exam.values() if n)]} of the {WORDS[len(STATIC)]} objectives, "
            f"and no more than {WORDS[max(exam.values())]} on any one") in GUIDE
    with_n = {n: [i for i in STATIC if exam[i] == n] for n in (0, 1, 2)}
    assert (with_n[0], with_n[1], with_n[2]) == (
        ["S09", "S11", "S12", "S14"], ["S02"], ["S01", "S05", "S08", "S10", "S13"]), (
        "the exam's thin spots changed: rewrite step 3 of 'Next steps' in the instructor guide")
    assert ("S09, S11, S12 and S14 have no questions, S02 has one, and S01, S05, S08, S10 and S13 have two each."
            in GUIDE)
