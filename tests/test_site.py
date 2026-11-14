"""Validate the generated website: pages, links, images, exercises, quizzes, notebooks."""
import collections
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml
from conftest import ROOT

SITE = yaml.safe_load((ROOT / "content" / "_site.yml").read_text(encoding="utf-8"))
LESSONS = [p["slug"] for p in SITE["pages"] if p.get("notebook")]


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.images, self.ids = [], [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag in ("img", "script", "link") and (a.get("src") or a.get("href")):
            target = a.get("src") or a.get("href")
            self.images.append((tag, target, a.get("alt")))


def parse(path):
    c = Collector()
    c.feed(path.read_text(encoding="utf-8"))
    return c


def test_page_count_is_within_brief():
    # Home + 7 lessons = 8 teaching pages (the brief asked for 6-8), plus the instructor guide.
    teaching = [p for p in SITE["pages"] if p["slug"] != "instructor-guide"]
    assert 6 <= len(teaching) <= 8


def test_every_page_built(built_site):
    for page in SITE["pages"]:
        assert (built_site["out"] / f"{page['slug']}.html").exists()


def test_local_links_and_assets_resolve(built_site):
    out = built_site["out"]
    for html_file in out.glob("*.html"):
        c = parse(html_file)
        for href in c.links:
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, frag = href.partition("#")
            path = out / target if target else html_file
            assert path.exists(), f"{html_file.name}: broken link {href}"
            if frag and path.suffix == ".html":
                assert frag in parse(path).ids, f"{html_file.name}: missing anchor {href}"
        for tag, src, _ in c.images:
            if src.startswith(("http", "data:")):
                continue
            assert (out / src).exists(), f"{html_file.name}: missing {tag} {src}"


def test_images_have_alt_text(built_site):
    for html_file in built_site["out"].glob("*.html"):
        for tag, src, alt in parse(html_file).images:
            if tag == "img" and not src.startswith("data:"):
                assert alt and len(alt) > 15, f"{html_file.name}: {src} needs descriptive alt text"


def test_no_unrendered_template_or_markdown(built_site):
    for html_file in built_site["out"].glob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        leftover = re.findall(r"\{\{(title|site_title|description|slug|nav|lesson_tools|content|pager|"
                              r"repo_url|setup_json)\}\}", text)
        assert not leftover, f"{html_file.name}: unreplaced template variables {leftover}"
        assert "PLACEHOLDER" not in text
        assert "```" not in text, f"{html_file.name}: raw code fence leaked into HTML"


@pytest.mark.parametrize("slug", LESSONS)
def test_lessons_have_exercises_and_quiz(built_site, slug):
    report = built_site["reports"][slug]
    assert len(report.exercises) >= 1
    assert len(report.quiz_answers) == 4
    assert len(set(report.quiz_answers)) == 4, f"{slug}: each quiz should use A-D once"
    assert len(report.figures) >= 3


def test_quiz_answers_balanced_overall(built_site):
    answers = [a for r in built_site["reports"].values() for a in r.quiz_answers]
    counts = collections.Counter(answers)
    assert max(counts.values()) - min(counts.values()) <= 1, counts


def test_quiz_correct_option_is_not_usually_longest():
    longest = total = 0
    fence = re.compile(r"^```quiz\n(.*?)^```", re.M | re.S)
    for slug in LESSONS:
        text = (ROOT / "content" / f"{slug}.md").read_text(encoding="utf-8")
        for block in fence.findall(text):
            for q in yaml.safe_load(block):
                lengths = [len(o) for o in q["options"]]
                total += 1
                longest += lengths["ABCD".index(q["answer"])] == max(lengths)
    assert longest / total <= 0.40, f"correct answer is the longest option in {longest}/{total}"


def test_committed_docs_match_sources(built_site):
    """docs/ is what GitHub Pages serves - it must be rebuilt after content edits."""
    for fresh in built_site["out"].glob("*.html"):
        committed = ROOT / "docs" / fresh.name
        assert committed.exists(), f"run python tools/build_site.py ({fresh.name} missing)"
        assert committed.read_text(encoding="utf-8") == fresh.read_text(encoding="utf-8"), (
            f"docs/{fresh.name} is stale - run python tools/build_site.py")


@pytest.mark.parametrize("slug", LESSONS)
def test_notebooks_are_valid(built_site, slug):
    nb_dir = built_site["out"] / "notebooks"
    student = json.loads((nb_dir / f"{slug}.ipynb").read_text(encoding="utf-8"))
    solutions = json.loads((nb_dir / f"{slug}-solutions.ipynb").read_text(encoding="utf-8"))
    for nb in (student, solutions):
        assert nb["nbformat"] == 4 and nb["cells"]
    sol_code = "".join("".join(c["source"]) for c in solutions["cells"] if c["cell_type"] == "code")
    stu_code = "".join("".join(c["source"]) for c in student["cells"] if c["cell_type"] == "code")
    assert "# Solution to exercise" in sol_code
    assert "# Solution to exercise" not in stu_code


@pytest.mark.slow
@pytest.mark.parametrize("slug", LESSONS)
def test_solution_notebooks_execute(built_site, slug, tmp_path):
    """Run each solutions notebook top to bottom in a real Jupyter kernel."""
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(built_site["out"] / "notebooks" / f"{slug}-solutions.ipynb", as_version=4)
    # use the bundled CSV so the test doesn't need the network
    shim = nbformat.v4.new_code_cell(
        "import seaborn as _sns, pandas as _pd\n"
        f"_sns.load_dataset = lambda name, **kw: _pd.read_csv(r'{ROOT / 'data' / 'penguins.csv'}')\n"
        "import matplotlib\nmatplotlib.use('Agg')")
    nb.cells.insert(0, shim)
    nbclient.NotebookClient(nb, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(tmp_path)}}).execute()
