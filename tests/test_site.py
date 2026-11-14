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
    assert longest / total <= 0.36, f"correct answer is the longest option in {longest}/{total}"


def test_quiz_questions_are_labelled_for_assistive_tech(built_site):
    """Each question is a labelled group, so screen readers announce the stem with its options."""
    for slug in LESSONS:
        text = (built_site["out"] / f"{slug}.html").read_text(encoding="utf-8")
        ids = set(re.findall(r'\sid="([^"]+)"', text))
        groups = re.findall(r'<div class="quiz-q"[^>]*role="group"[^>]*aria-labelledby="([^"]+)"', text)
        assert len(groups) == 4, f"{slug}: every quiz question should be a role=group"
        for stem_id in groups:
            assert stem_id in ids, f"{slug}: aria-labelledby points at a missing id {stem_id}"


@pytest.mark.parametrize("slug", LESSONS)
def test_notebook_callouts_render_as_blockquotes(built_site, slug):
    """Markdown admonitions have no meaning in Jupyter; the build turns them into blockquotes."""
    nb_dir = built_site["out"] / "notebooks"
    for name in (f"{slug}.ipynb", f"{slug}-solutions.ipynb"):
        nb = json.loads((nb_dir / name).read_text(encoding="utf-8"))
        prose = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
        assert "!!!" not in prose, f"{name}: raw admonition marker leaked into a notebook"
        assert "> **Design principle: " in prose, f"{name}: the design-principle callout is missing"
        assert "> **Note: Key takeaways**" in prose or "> **Note: Course takeaways**" in prose, name


@pytest.mark.parametrize("slug", LESSONS)
def test_no_cell_changes_global_style_for_later_cells(slug):
    """Run a lesson's cells in notebook order, in one namespace, and check that no
    example or solution leaves seaborn/matplotlib defaults changed. Otherwise a
    notebook user would see later charts drawn in a theme the site never shows."""
    import contextlib
    import io
    import warnings

    import matplotlib
    import matplotlib.pyplot as plt

    import build_site
    import runner  # patches sns.load_dataset to the bundled CSV

    text = (ROOT / "content" / f"{slug}.md").read_text(encoding="utf-8")
    _, blocks = build_site.split_blocks(text)
    setup = next(b.body for b in blocks if b.kind == "setup")
    matplotlib.rcdefaults()
    ns = {"__name__": "__main__"}
    exec(compile(setup, "<setup>", "exec"), ns)
    baseline = dict(matplotlib.rcParams)
    with warnings.catch_warnings():
        for pattern in runner.LIBRARY_WARNINGS:  # same allowance as the runner itself
            warnings.filterwarnings("ignore", message=pattern)
        for block in blocks:
            if block.kind not in ("run", "solution"):
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(block.body, "<cell>", "exec"), ns)
            plt.close("all")
            changed = {k: (baseline[k], v) for k, v in matplotlib.rcParams.items() if baseline[k] != v}
            assert not changed, f"{slug}: cell starting {block.body.splitlines()[0]!r} changed {changed}"
    matplotlib.rcdefaults()


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
