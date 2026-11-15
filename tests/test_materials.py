"""Validate the exam, the assignments and the generated Word documents."""
import collections
import re

import pytest
import yaml
from conftest import ROOT

import build_materials

INSTRUCTOR = ROOT / "instructor"
EXAM = yaml.safe_load((INSTRUCTOR / "exam_questions.yaml").read_text(encoding="utf-8"))
SPEC = yaml.safe_load((INSTRUCTOR / "assignments.yaml").read_text(encoding="utf-8"))


def test_exam_has_25_well_formed_questions():
    assert len(EXAM) == 25
    for n, q in enumerate(EXAM, 1):
        assert len(q["options"]) == 4, f"Q{n}"
        assert len(set(q["options"])) == 4, f"Q{n} has duplicate options"
        assert q["answer"] in "ABCD", f"Q{n}"
        assert q["explain"].strip(), f"Q{n} needs an explanation"
        assert not any("all of the above" in o.lower() or "none of the above" in o.lower()
                       for o in q["options"]), f"Q{n}: avoid all/none of the above"


def test_exam_answers_are_evenly_distributed():
    counts = collections.Counter(q["answer"] for q in EXAM)
    assert set(counts) == set("ABCD")
    assert max(counts.values()) - min(counts.values()) <= 1, counts


def test_exam_has_no_long_runs_or_obvious_pattern():
    letters = "".join(q["answer"] for q in EXAM)
    assert not re.search(r"(.)\1\1", letters), f"three in a row: {letters}"
    assert "ABCD" * 2 not in letters and "DCBA" * 2 not in letters


def test_correct_answer_is_not_usually_the_longest():
    longest = sum(
        len(q["options"]["ABCD".index(q["answer"])]) == max(len(o) for o in q["options"])
        for q in EXAM
    )
    assert longest / len(EXAM) <= 0.36, f"correct option is longest in {longest}/25"


def test_exam_covers_every_lesson():
    assert {q["lesson"] for q in EXAM} == set(range(1, 8))


def test_three_assignments_increasing_and_rubrics_total_100():
    """Three assignments that grow, and one short task that is smaller than any of them: 'Questions
    only', in which the learner chooses each chart form (PLAN.md, step C)."""
    assignments, tasks = SPEC["assignments"], SPEC["tasks"]
    assert len(assignments) == 3 and len(tasks) == 1
    for a in assignments + tasks:
        assert sum(r[1] for r in a["rubric"]) == 100, a["title"]
    sizes = [sum(len(p.get("code", "")) for p in a["solution"]) for a in assignments]
    assert sizes == sorted(sizes), "assignments should grow in complexity"
    assert "30 minutes" in tasks[0]["time"], "the map counts the short task as half an hour of project work"
    assert len(tasks[0]["tasks"]) <= 4, "a fifth item would be numbered '5.', which the numbering test reads as a run-on"
    named = " ".join(tasks[0]["tasks"]).lower()
    for form in ("histogram", "scatter", "bar chart", "box plot", "count chart", "ecdf"):
        assert form not in named, f"the short task must not name a chart form, and it names '{form}'"


@pytest.fixture(scope="module")
def solution_results():
    return build_materials.run_solutions(SPEC)


def test_every_solution_runs_and_draws(solution_results):
    for (a, p), result in solution_results.items():
        part = build_materials.graded_work(SPEC)[a]["solution"][p]
        assert result["error"] is None, part["title"]
        if "plt" in part["code"] or "sns." in part["code"]:
            assert result["figures"], f"{part['title']} drew nothing"


def test_assignment3_classifier_is_accurate(solution_results):
    out = solution_results[(2, 0)]["stdout"]
    overall = float(re.search(r"Overall accuracy: ([\d.]+)%", out).group(1))
    assert overall > 90


@pytest.fixture(scope="module")
def docs(tmp_path_factory):
    from docx import Document

    questions = build_materials.load_exam()
    results = build_materials.run_solutions(SPEC)
    out = tmp_path_factory.mktemp("docx")
    paths = {}
    for name, instructor in (("inst", True), ("stud", False)):
        build_materials.build_assessment(questions, SPEC, results, instructor).save(out / f"{name}.docx")
        paths[name] = Document(out / f"{name}.docx")
    build_materials.build_guide(build_materials.guide_markdown()).save(out / "guide.docx")
    paths["guide"] = Document(out / "guide.docx")
    return paths


def _texts(doc):
    return [p.text for p in doc.paragraphs]


def test_instructor_edition_marks_exactly_the_right_answers(docs):
    marked = [t for t in _texts(docs["inst"]) if "✓ correct answer" in t]
    assert len(marked) == 25
    assert [t.strip()[0] for t in marked] == [q["answer"] for q in EXAM]


def test_student_edition_has_questions_but_no_answers(docs):
    texts = _texts(docs["stud"])
    assert sum(bool(re.match(r"Q\d+\. ", t)) for t in texts) == 25
    joined = "\n".join(texts)
    assert "✓" not in joined and "Model solution" not in joined and "Why:" not in joined


def test_instructor_edition_has_solutions_and_figures(docs):
    joined = "\n".join(_texts(docs["inst"]))
    assert joined.count("Model solution") == 4
    assert len(docs["inst"].inline_shapes) >= 10


def test_both_editions_explain_the_scoring_scale(docs):
    for name in ("inst", "stud"):
        joined = "\n".join(_texts(docs[name]))
        assert "How the rubrics are scored." in joined, name
        assert SPEC["scoring"].split(".")[0] in joined, name


def test_task_lists_restart_at_one_for_every_assignment(docs):
    for name in ("inst", "stud"):
        paragraphs = docs[name].paragraphs
        starts = [i for i, p in enumerate(paragraphs) if p.text == "Tasks" and p.style.name.startswith("Heading")]
        assert len(starts) == 4, name
        for i in starts:
            assert paragraphs[i + 1].text.startswith("1.\t"), f"{name}: tasks after paragraph {i} don't start at 1"
        assert not any(p.text.startswith(("5.\t", "9.\t")) for p in paragraphs), f"{name}: numbering ran on"


def test_guide_docx_has_structure(docs):
    headings = [p.text for p in docs["guide"].paragraphs if p.style.name.startswith("Heading")]
    assert "Lesson-by-lesson notes" in headings
    assert len(docs["guide"].tables) >= 5
    assert "{{" not in "\n".join(_texts(docs["guide"]))


def test_committed_word_files_exist():
    for name in ("Seaborn_Assessment_Pack_INSTRUCTOR.docx", "Seaborn_Assessment_Pack_STUDENT.docx",
                 "Seaborn_Instructor_Guide.docx"):
        assert (INSTRUCTOR / name).stat().st_size > 20_000, name
