"""Validate the generated website: pages, links, images, exercises, quizzes, notebooks."""
import collections
import functools
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
    """Each question is a labeled group, so screen readers announce the stem with its options."""
    for slug in LESSONS:
        text = (built_site["out"] / f"{slug}.html").read_text(encoding="utf-8")
        ids = set(re.findall(r'\sid="([^"]+)"', text))
        groups = re.findall(r'<div class="quiz-q"[^>]*role="group"[^>]*aria-labelledby="([^"]+)"', text)
        assert len(groups) == 4, f"{slug}: every quiz question should be a role=group"
        for stem_id in groups:
            assert stem_id in ids, f"{slug}: aria-labelledby points at a missing id {stem_id}"


def _contrast(rgb_a, rgb_b):
    """WCAG 2 contrast ratio of two sRGB colors given as 0-1 triples."""
    def luminance(rgb):
        r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    lighter, darker = sorted((luminance(rgb_a), luminance(rgb_b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_muted_text_keeps_aa_contrast_on_every_background():
    """`--ink-3` colors the small labels: lesson numbers in the sidebar, quiz option letters,
    the "Design principle" tag. They sit on the page, on cards, on the hover and callout
    surface, on the current sidebar item and on a graded quiz option. WCAG AA asks for
    4.5:1 on each of them, in the light theme and in the dark one."""
    css = (ROOT / "site_src" / "style.css").read_text(encoding="utf-8")
    themes = re.findall(r":root[^{]*\{([^}]*)\}", css)
    assert len(themes) == 2, "expected the light :root block and the dark one"
    tints = re.findall(r"label\.is-(?:correct|wrong) \{[^}]*"
                       r"color-mix\(in srgb, var\(--(\w+)\) (\d+)%, var\(--surface\)\)", css)
    assert len(tints) == 2, "expected a tinted background for right and for wrong quiz options"
    for theme, block in zip(("light", "dark"), themes):
        color = {name: tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
                 for name, value in re.findall(r"--([\w-]+):\s*#([0-9a-fA-F]{6})\b", block)}
        backgrounds = {name: color[name] for name in ("bg", "surface", "surface-2", "note")}
        for name, percent in tints:  # color-mix(in srgb, ...) blends the encoded channel values
            share = int(percent) / 100
            backgrounds[f"{name} tint"] = tuple(share * t + (1 - share) * s
                                                for t, s in zip(color[name], color["surface"]))
        for where, background in backgrounds.items():
            ratio = _contrast(color["ink-3"], background)
            assert ratio >= 4.5, f"{theme} theme: --ink-3 on {where} is only {ratio:.2f}:1"


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


Cell = collections.namedtuple("Cell", "name first_line changed legends")


@functools.lru_cache(maxsize=None)
def cells_in_notebook_order(slug):
    """Run a lesson's example and solution cells in notebook order, in one namespace.

    Returns one record per cell: its figure name, its first line, the rcParams it
    left changed, and the (title, entries) of every legend it drew. Cached, so the
    tests that read these records execute each lesson only once between them.
    """
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
    cells = []
    with warnings.catch_warnings():
        for pattern in runner.LIBRARY_WARNINGS:  # same allowance as the runner itself
            warnings.filterwarnings("ignore", message=pattern)
        for block in blocks:
            if block.kind not in ("run", "solution"):
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(block.body, "<cell>", "exec"), ns)
            legends = []
            for num in plt.get_fignums():
                fig = plt.figure(num)
                for legend in [*fig.legends, *(ax.get_legend() for ax in fig.axes)]:
                    if legend is not None:
                        legends.append((legend.get_title().get_text(), [t.get_text() for t in legend.get_texts()]))
            plt.close("all")
            changed = {k: (baseline[k], v) for k, v in matplotlib.rcParams.items() if baseline[k] != v}
            name = block.opts.get("fig") or (f"sol-{block.opts.get('for')}" if block.kind == "solution" else "")
            cells.append(Cell(name, block.body.splitlines()[0], changed, legends))
    matplotlib.rcdefaults()
    return tuple(cells)


@pytest.mark.parametrize("slug", LESSONS)
def test_no_cell_changes_global_style_for_later_cells(slug):
    """Run a lesson's cells in notebook order, in one namespace, and check that no
    example or solution leaves seaborn/matplotlib defaults changed. Otherwise a
    notebook user would see later charts drawn in a theme the site never shows."""
    for cell in cells_in_notebook_order(slug):
        assert not cell.changed, f"{slug}: cell starting {cell.first_line!r} changed {cell.changed}"


# Charts that show seaborn's raw column names in a legend on purpose. Every other legend is relabeled.
RAW_LEGENDS_ON_PURPOSE = {
    "01-scatter-hue": "the bare first hue example; the next section relabels it",
    "01-scatter-style": "two legend variables, so the column names are headings inside the legend, not a title",
    "04-pairplot": "an exploration tool shown with seaborn's defaults, and the text says so",
    "06-before": "the deliberately cluttered 'before' chart of the makeover",
}


def test_legends_are_titled_in_plain_english():
    """Seaborn titles a legend with the raw column name ("species", "sex"). Lesson 1 teaches
    learners to relabel it, so every finished chart on the site has to do the same."""
    columns = set((ROOT / "data" / "penguins.csv").read_text(encoding="utf-8").splitlines()[0].split(","))
    raw = {}
    for slug in LESSONS:
        for cell in cells_in_notebook_order(slug):
            shown = {text for title, entries in cell.legends for text in (title, *entries)}
            if shown & columns:
                raw[cell.name or cell.first_line] = sorted(shown & columns)
    unexpected = {name: names for name, names in raw.items() if name not in RAW_LEGENDS_ON_PURPOSE}
    assert not unexpected, (f"legends showing raw column names: {unexpected}. Relabel them with "
                            "ax.get_legend().set_title(...) or g.legend.set_title(...).")
    no_longer_raw = sorted(set(RAW_LEGENDS_ON_PURPOSE) - set(raw))
    assert not no_longer_raw, f"remove from RAW_LEGENDS_ON_PURPOSE, these legends are fine now: {no_longer_raw}"


def test_exercise_2_1_only_accepts_step_outlines():
    """The brief asks for outline-only step histograms, so every near miss has to earn a hint."""
    import build_site
    import runner

    text = (ROOT / "content" / "02-distributions.md").read_text(encoding="utf-8")
    _, blocks = build_site.split_blocks(text)
    setup = next(b.body for b in blocks if b.kind == "setup")
    check = next(b.body for b in blocks if b.kind == "check" and b.opts.get("for") == "2.1")
    by_species = 'data=penguins, x="flipper_length_mm", hue="species", palette=PENGUIN_COLORS'
    label = '\nax.set(xlabel="Flipper length (mm)")'
    near_misses = {
        f"ax = sns.histplot({by_species}, binwidth=3)": "element='step'",                             # bars
        f"ax = sns.histplot({by_species}, binwidth=3, fill=False)": "element='step'",                 # hollow bars
        f'ax = sns.histplot({by_species}, binwidth=3, element="step")': "fill=False",                  # filled steps
        f'ax = sns.histplot({by_species}, binwidth=3, element="poly", fill=False)': "element='step'",  # not steps
        f"ax = sns.kdeplot({by_species})": "element='step'",                                           # not a histogram
        f"ax = sns.ecdfplot({by_species})": "element='step'",                                          # steps, no bins
    }
    for code, hint in near_misses.items():
        result = runner.run_cell(code + label, setup=setup, check=check)
        assert result["error"] is None, result["error"]
        assert result["check_ok"] is False and hint in result["check_message"], (code, result["check_message"])
    outlines = f'ax = sns.histplot({by_species}, binwidth=3, element="step", fill=False)'
    unlabeled = runner.run_cell(outlines, setup=setup, check=check)  # seaborn's own label is "flipper_length_mm"
    assert unlabeled["check_ok"] is False and "plain English" in unlabeled["check_message"]
    result = runner.run_cell(outlines + label, setup=setup, check=check)
    assert result["check_ok"] is True, result["check_message"]


# Every exercise that asks for plain-English axis labels, with a line that puts seaborn's raw
# column names back on the solution's axes. The checker has to notice.
RAW_LABELS = {
    ("01-first-plot", "1.1"): 'ax.set(xlabel="bill_length_mm", ylabel="flipper_length_mm")',
    ("02-distributions", "2.1"): 'ax.set(xlabel="flipper_length_mm")',
    ("03-categories", "3.2"): 'ax.set(ylabel="bill_depth_mm")',
    ("04-relationships", "4.2"): 'g.set_axis_labels("Bill depth (mm)", "body_mass_g")',
    ("05-small-multiples", "5.1"): 'g.set_axis_labels("flipper_length_mm", "Count")',
    ("06-polish", "6.1"): 'ax.set(xlabel="bill_length_mm", ylabel="bill_depth_mm")',
}


@pytest.mark.parametrize("slug, ex_id", sorted(RAW_LABELS))
def test_exercises_reject_raw_column_names_as_axis_labels(slug, ex_id):
    """`flipper_length_mm` contains "mm", so a unit check alone passes a chart nobody labeled."""
    import build_site
    import runner

    _, blocks = build_site.split_blocks((ROOT / "content" / f"{slug}.md").read_text(encoding="utf-8"))
    setup = next(b.body for b in blocks if b.kind == "setup")
    solution = next(b.body for b in blocks if b.kind == "solution" and b.opts.get("for") == ex_id)
    check = next(b.body for b in blocks if b.kind == "check" and b.opts.get("for") == ex_id)
    result = runner.run_cell(solution + "\n" + RAW_LABELS[(slug, ex_id)], setup=setup, check=check)
    assert result["error"] is None, result["error"]
    assert result["check_ok"] is False, f"exercise {ex_id} accepts raw column names as axis labels"
    assert re.search(r"plain.English", result["check_message"]), result["check_message"]


# Every exercise whose brief asks for PENGUIN_COLORS. Without the palette the chart comes out
# in seaborn's default colors, and the checker has to say so.
ASK_FOR_PENGUIN_COLORS = [
    ("01-first-plot", "1.1"), ("02-distributions", "2.1"), ("02-distributions", "2.2"),
    ("03-categories", "3.1"), ("03-categories", "3.2"), ("04-relationships", "4.2"),
    ("05-small-multiples", "5.1"), ("06-polish", "6.1"),
]


@pytest.mark.parametrize("slug, ex_id", ASK_FOR_PENGUIN_COLORS)
def test_exercises_reject_seaborn_default_colors(slug, ex_id):
    """Exercise 2.2 named PENGUIN_COLORS in its brief and then passed an ECDF in seaborn's own colors."""
    import build_site
    import runner

    _, blocks = build_site.split_blocks((ROOT / "content" / f"{slug}.md").read_text(encoding="utf-8"))
    setup = next(b.body for b in blocks if b.kind == "setup")
    brief = next(b.body for b in blocks if b.kind == "exercise" and b.opts.get("id") == ex_id)
    solution = next(b.body for b in blocks if b.kind == "solution" and b.opts.get("for") == ex_id)
    check = next(b.body for b in blocks if b.kind == "check" and b.opts.get("for") == ex_id)
    assert "PENGUIN_COLORS" in brief, f"exercise {ex_id} no longer asks for PENGUIN_COLORS"
    default_colors, removed = re.subn(r",?\s*palette=PENGUIN_COLORS", "", solution)
    assert removed == 1, f"exercise {ex_id}: expected one palette=PENGUIN_COLORS in the solution"
    result = runner.run_cell(default_colors, setup=setup, check=check)
    assert result["error"] is None, result["error"]
    assert result["check_ok"] is False, f"exercise {ex_id} accepts seaborn's default colors"
    assert "PENGUIN_COLORS" in result["check_message"], result["check_message"]


# Solutions changed in one way that the exercise's brief rules out: (page, exercise, the text to
# replace in the solution, its replacement, a word of the hint the checker has to give).
RULED_OUT_BY_THE_BRIEF = [
    ("02-distributions", "2.2", "sns.ecdfplot(data=", "sns.histplot(data=", "ecdfplot"),                               # bars
    ("02-distributions", "2.2", "sns.ecdfplot(data=", 'sns.histplot(element="step", fill=False, data=', "ecdfplot"),  # outlines
    ("02-distributions", "2.2", "sns.ecdfplot(data=", "sns.kdeplot(data=", "ecdfplot"),                                # density
    ("06-polish", "6.1", "legend=False)", 'legend=False, style="island")', "style="),              # a shape for each island
    ("07-capstone", "7.1", ', layout="constrained"', "", "constrained"),                                # no layout engine
    ("07-capstone", "7.1", "    ax.get_legend().remove()", "    pass", "legends"),                      # a legend in every panel
]


@pytest.mark.parametrize("slug, ex_id, old, new, hint", RULED_OUT_BY_THE_BRIEF)
def test_exercises_reject_what_their_brief_rules_out(slug, ex_id, old, new, hint):
    """Exercise 2.2 asks for an ECDF and passed a histogram. Exercise 6.1 says to drop style= and
    passed a chart that kept it. Exercise 7.1 asks for a constrained layout and one legend, and
    tested neither."""
    import build_site
    import runner

    _, blocks = build_site.split_blocks((ROOT / "content" / f"{slug}.md").read_text(encoding="utf-8"))
    setup = next(b.body for b in blocks if b.kind == "setup")
    solution = next(b.body for b in blocks if b.kind == "solution" and b.opts.get("for") == ex_id)
    check = next(b.body for b in blocks if b.kind == "check" and b.opts.get("for") == ex_id)
    assert solution.count(old) == 1, f"exercise {ex_id}: expected {old!r} once in the solution"
    result = runner.run_cell(solution.replace(old, new), setup=setup, check=check)
    assert result["error"] is None, result["error"]
    assert result["check_ok"] is False, f"exercise {ex_id} accepts a solution with {old!r} replaced by {new!r}"
    assert hint in result["check_message"], result["check_message"]


def exercise_6_3_attempts():
    """Attempts at exercise 6.3 as {name: (code, a word of the hint it has to earn, or None if it
    should pass)}. Each is the solution's chart with a different ending."""
    import build_site

    _, blocks = build_site.split_blocks((ROOT / "content" / "06-polish.md").read_text(encoding="utf-8"))
    solution = next(b.body for b in blocks if b.kind == "solution" and b.opts.get("for") == "6.3")
    chart, rest = solution.split("lightest = ")
    assert "ax.annotate(" in rest and "set_major_formatter" in rest
    find = 'lightest = penguins.loc[penguins["body_mass_g"].idxmin()]\n'
    spot = 'xy=(lightest["flipper_length_mm"], lightest["body_mass_g"]), xytext=(200, 2750)'
    arrow = ', arrowprops={"arrowstyle": "->"})\n'
    kilograms = 'ax.yaxis.set_major_formatter(lambda value, pos: f"{value / 1000:.1f} kg")\n'
    good = chart + find + f'ax.annotate("Lightest bird", {spot}{arrow}'
    return {
        "words without an arrow (ax.text)": (chart + 'ax.text(200, 2750, "Lightest bird")\n' + kilograms, "ax.annotate"),
        "an annotation without an arrow": (chart + find + f'ax.annotate("Lightest bird", {spot})\n' + kilograms,
                                           "arrowprops"),
        "the arrow points at the heaviest bird": (good.replace("idxmin", "idxmax") + kilograms, "idxmin"),
        "an arrow without words": (good.replace('"Lightest bird"', '""') + kilograms, "some words"),
        "no tick formatter": (good, "tick formatter"),
        "grams with a thousands comma under a label that says kg": (
            good + 'ax.yaxis.set_major_formatter(lambda value, pos: f"{value:,.0f}")\nax.set(ylabel="Body mass (kg)")\n',
            "still shows grams"),
        "kilograms without a unit": (good + 'ax.yaxis.set_major_formatter(lambda value, pos: f"{value / 1000:.1f}")\n',
                                     "'kg'"),
        "the data divided by 1000": (chart.replace('y="body_mass_g"', 'y=penguins["body_mass_g"] / 1000') + kilograms,
                                     "in grams"),
        "the unit on the axis label": (good + 'ax.yaxis.set_major_formatter(lambda value, pos: f"{value / 1000:.1f}")\n'
                                       'ax.set(ylabel="Body mass (kg)")\n', None),
        "a format string as the formatter": (good + "from matplotlib.ticker import FuncFormatter\n"
                                             'ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v / 1000:g} kg"))\n',
                                             None),
    }


def test_exercise_6_3_wants_an_arrow_at_the_lightest_bird_and_kilograms():
    """Exercise 6.3 is the one that checks ax.annotate and a tick formatter. The lesson's own example
    annotates the heaviest bird, so pasting its lines must not pass, and neither may ax.text. Grams
    written with a thousands comma ("3,000") are still grams, whatever the axis label says."""
    import build_site
    import runner

    _, blocks = build_site.split_blocks((ROOT / "content" / "06-polish.md").read_text(encoding="utf-8"))
    setup = next(b.body for b in blocks if b.kind == "setup")
    check = next(b.body for b in blocks if b.kind == "check" and b.opts.get("for") == "6.3")
    for name, (code, hint) in exercise_6_3_attempts().items():
        result = runner.run_cell(code, setup=setup, check=check)
        assert result["error"] is None, (name, result["error"])
        if hint is None:
            assert result["check_ok"] is True, (name, result["check_message"])
        else:
            assert result["check_ok"] is False and hint in result["check_message"], (name, result["check_message"])


def exercise_6_4_attempts():
    """Attempts at exercise 6.4 as {name: (code, a word of the hint it has to earn, or None if it
    should pass)}."""
    def listed(*statements):
        return f"problems = {list(statements)!r}"

    one = "There are far too many things going on at once here."
    two = "I cannot tell what I am supposed to notice in it."
    three = "Half of the picture is hidden behind a box of text."
    return {
        "two statements": (listed(one, two, ""), "I count 2"),
        "the same statement twice": (listed(one, two, "  i cannot tell what I am   supposed to notice in it. "),
                                     "are the same"),
        "a statement of a few words": (listed(one, two, "bad colors"), "Say more than 'bad colors'"),
        "one long string, not a list": (f"problems = {one + ' ' + two + ' ' + three!r}", "list named problems"),
        "another name for the list": (f"faults = {[one, two, three]!r}", "list named problems"),
        "three statements the check has no word for": (listed(one, two, three), None),
        "three statements in a tuple": (f"problems = {(one, two, three)!r}", None),
    }


def test_exercise_6_4_counts_three_different_statements():
    """Exercise 6.4 asks for a critique in words before the page gives its own. Its check is lenient
    on purpose: it counts three different statements of some length, and says which kinds of fault it
    recognized. It cannot judge them (rubric row A3 R5 does), and it must not pretend to."""
    import build_site
    import runner

    _, blocks = build_site.split_blocks((ROOT / "content" / "06-polish.md").read_text(encoding="utf-8"))
    setup = next(b.body for b in blocks if b.kind == "setup")
    solution = next(b.body for b in blocks if b.kind == "solution" and b.opts.get("for") == "6.4")
    check = next(b.body for b in blocks if b.kind == "check" and b.opts.get("for") == "6.4")
    for name, (code, hint) in exercise_6_4_attempts().items():
        result = runner.run_cell(code, setup=setup, check=check)
        assert result["error"] is None, (name, result["error"])
        if hint is None:
            assert result["check_ok"] is True, (name, result["check_message"])
            assert "not judge them" in result["check_message"] and "You wrote about" not in result["check_message"]
        else:
            assert result["check_ok"] is False and hint in result["check_message"], (name, result["check_message"])
    model = runner.run_cell(solution, setup=setup, check=check)
    assert model["check_ok"] is True and not model["figures"]
    for kind in ("the encodings", "the colors", "the legend", "the labels", "the title"):
        assert kind in model["check_message"].split("Worth a second look")[0], (kind, model["check_message"])


def test_bin_width_panels_draw_the_widths_they_name():
    """seaborn fits a whole number of bins to the data's range unless binrange= is given,
    so a panel titled "binwidth = 1000 g" used to draw 900 g bins. The panels don't share a
    y-axis (wider bins hold more penguins), so each of them has to label its own."""
    import build_site
    import runner

    _, blocks = build_site.split_blocks((ROOT / "content" / "02-distributions.md").read_text(encoding="utf-8"))
    setup = next(b.body for b in blocks if b.kind == "setup")
    cell = next(b.body for b in blocks if b.opts.get("fig") == "02-binwidths")
    probe = ("import json\n"
             "print(json.dumps([[a.get_title(), a.get_ylabel(),"
             " sorted({round(p.get_width(), 6) for p in a.patches})] for a in plt.gcf().axes]))")
    panels = json.loads(runner.run_cell(cell, setup=setup, check=probe)["check_message"])
    assert len(panels) == 3
    for title, ylabel, widths in panels:
        named = float(re.search(r"binwidth = (\d+) g", title).group(1))
        assert widths == [named], f"the panel titled {title!r} draws bins of {widths} g"
        assert ylabel, f"the panel titled {title!r} has its own y scale but no y label"


def _without_carriage_returns(path):
    """File contents with Windows line endings folded, so a checkout's autocrlf setting can't matter."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def test_committed_docs_match_sources(built_site):
    """docs/ is what GitHub Pages serves - it must be rebuilt after content edits.

    Pages, notebooks, scripts, styles and data are compared with a fresh build.
    Figures are only checked for presence: a PNG's bytes depend on the machine that
    drew it, so they differ between the Windows machine that builds docs/ and the
    Linux CI runner.
    """
    fresh_root, docs = built_site["out"], ROOT / "docs"
    problems = []
    for fresh in sorted(p for p in fresh_root.rglob("*") if p.is_file()):
        rel = fresh.relative_to(fresh_root).as_posix()
        committed = docs / rel
        if not committed.is_file():
            problems.append(f"docs/{rel} is missing")
        elif fresh.suffix != ".png" and _without_carriage_returns(committed) != _without_carriage_returns(fresh):
            problems.append(f"docs/{rel} is stale")
    # The build empties these two folders before it writes them, so anything extra is an orphan.
    for folder, suffix in (("img", ".png"), ("notebooks", ".ipynb")):
        built = {p.name for p in (fresh_root / folder).iterdir()}
        problems += [f"docs/{folder}/{p.name} is no longer produced by the build"
                     for p in sorted((docs / folder).glob(f"*{suffix}")) if p.name not in built]
    assert not problems, "run python tools/build_site.py and commit docs/:\n  " + "\n  ".join(problems)


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
