"""Build the GitHub Pages site (docs/) from the Markdown lessons in content/.

Usage:  python tools/build_site.py            # writes docs/
        python tools/build_site.py --out DIR  # writes somewhere else (tests)

Markdown pages may contain these fenced blocks (the "info string" after the
backticks selects the behaviour):

    ```python setup                      code run before every cell on the page
    ```python run fig=NAME alt="..."     executed; code + figure (or output) shown
    ```python exercise id=ID title="..." starter code for an in-browser exercise
    ```python solution for=ID            the exercise's solution (hidden)
    ```python check for=ID               assertions that grade the exercise
    ```quiz                              YAML list of multiple-choice questions
    ```python                            plain, highlighted, not executed

The build is strict: it fails if any cell errors or warns, if a solution does
not pass its check, or if the untouched starter code *does* pass it.
"""

import argparse
import html
import json
import re
import shlex
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import markdown
import yaml
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SITE_SRC = ROOT / "site_src"
DATA_CSV = ROOT / "data" / "penguins.csv"

sys.path.insert(0, str(ROOT / "tools"))
import runner  # noqa: E402

runner.DATA_PATH = str(DATA_CSV)

LETTERS = "ABCD"
FENCE = re.compile(r"^```(?P<info>[^\n]*)\n(?P<body>.*?)^```[ \t]*$", re.M | re.S)


class BuildError(Exception):
    pass


@dataclass
class Block:
    kind: str  # setup | run | exercise | solution | check | quiz | code
    body: str
    opts: dict = field(default_factory=dict)


@dataclass
class PageReport:
    slug: str
    figures: list = field(default_factory=list)
    exercises: list = field(default_factory=list)
    quiz_answers: list = field(default_factory=list)


def parse_info(info):
    parts = shlex.split(info.strip())
    lang = parts[0] if parts else ""
    kind = "code"
    opts = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            opts[key] = value
        else:
            kind = part
    if lang == "quiz":
        kind = "quiz"
    elif lang != "python":
        kind = "code"
    opts["lang"] = lang
    return kind, opts


def split_blocks(text):
    """Return (markdown_with_placeholders, blocks)."""
    blocks = []

    def repl(match):
        kind, opts = parse_info(match.group("info"))
        blocks.append(Block(kind, match.group("body").rstrip("\n"), opts))
        return f"\n\nBLOCK{len(blocks) - 1}PLACEHOLDER\n\n"

    return FENCE.sub(repl, text), blocks


def code_html(code, label=None):
    rendered = highlight(code, PythonLexer(), HtmlFormatter(cssclass="highlight"))
    head = f'<div class="code-label">{html.escape(label)}</div>' if label else ""
    return head + rendered


def inline_md(text):
    out = markdown.markdown(str(text), extensions=["smarty"])
    return re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)


def json_script(data, cls):
    payload = json.dumps(data).replace("</", "<\\/")
    return f'<script type="application/json" class="{cls}">{payload}</script>'


def fail_on(result, where, allow_figures=True):
    if result["error"]:
        raise BuildError(f"{where} raised an error:\n{result['error']}")
    if result["warnings"]:
        raise BuildError(f"{where} emitted warnings:\n" + "\n".join(result["warnings"]))
    if not allow_figures and result["figures"]:
        raise BuildError(f"{where} drew a figure but has no fig= name")


def render_run(block, setup, slug, img_dir, report):
    result = runner.run_cell(block.body, setup=setup)
    where = f"{slug}: run block starting {block.body.splitlines()[0]!r}"
    name = block.opts.get("fig")
    fail_on(result, where, allow_figures=bool(name))
    parts = [f'<div class="cell" data-cell>{code_html(block.body)}']
    parts.append(json_script({"code": block.body}, "cell-data"))
    parts.append('<div class="cell-toolbar"><button type="button" class="btn-ghost" '
                 'data-action="edit" title="Open this example in a live Python editor">'
                 "Edit &amp; run</button></div>")
    if result["stdout"].strip():
        parts.append(f'<pre class="cell-stdout">{html.escape(result["stdout"].rstrip())}</pre>')
    if name:
        if len(result["figures"]) != 1:
            raise BuildError(f"{where} produced {len(result['figures'])} figures; expected 1")
        alt = block.opts.get("alt")
        if not alt:
            raise BuildError(f"{where} needs alt= text for accessibility")
        (img_dir / f"{name}.png").write_bytes(result["figures"][0])
        report.figures.append(name)
        caption = block.opts.get("caption")
        cap = f"<figcaption>{inline_md(caption)}</figcaption>" if caption else ""
        parts.append(f'<figure class="cell-figure"><img src="img/{name}.png" alt="{html.escape(alt)}" '
                     f'loading="lazy">{cap}</figure>')
    parts.append('<div class="cell-live"></div></div>')
    return "".join(parts)


def render_exercise(block, solution, check, setup, slug, img_dir, report):
    ex_id = block.opts.get("id")
    title = block.opts.get("title", "Your turn")
    if solution is None or check is None:
        raise BuildError(f"{slug}: exercise {ex_id} needs both a solution and a check block")
    where = f"{slug}: exercise {ex_id}"

    sol = runner.run_cell(solution.body, setup=setup, check=check.body)
    fail_on(sol, f"{where} solution")
    if not sol["check_ok"]:
        raise BuildError(f"{where}: solution fails its own check: {sol['check_message']}")
    starter = runner.run_cell(block.body, setup=setup, check=check.body)
    if starter["check_ok"]:
        raise BuildError(f"{where}: untouched starter code already passes the check")
    report.exercises.append(ex_id)

    figs = ""
    for i, fig in enumerate(sol["figures"]):
        name = f"sol-{ex_id}" + (f"-{i + 1}" if i else "")
        (img_dir / f"{name}.png").write_bytes(fig)
        report.figures.append(name)
        figs += (f'<figure class="cell-figure"><img src="img/{name}.png" '
                 f'alt="Solution chart for exercise {html.escape(ex_id)}" loading="lazy"></figure>')
    sol_out = ""
    if sol["stdout"].strip():
        sol_out = f'<pre class="cell-stdout">{html.escape(sol["stdout"].rstrip())}</pre>'
    data = {"starter": block.body, "solution": solution.body, "check": check.body}
    rows = max(6, min(22, block.body.count("\n") + 3))
    return f"""
<div class="exercise" id="ex-{ex_id}" data-exercise>
  <div class="exercise-head"><span class="exercise-tag">Exercise {html.escape(ex_id)}</span>
    <span class="exercise-title">{inline_md(title)}</span></div>
  <textarea class="cell-editor" rows="{rows}" spellcheck="false" autocapitalize="off"
    aria-label="Code editor for exercise {html.escape(ex_id)}">{html.escape(block.body)}</textarea>
  <div class="cell-toolbar">
    <button type="button" class="btn-primary" data-action="check">Run &amp; check</button>
    <button type="button" class="btn-ghost" data-action="run">Run only</button>
    <button type="button" class="btn-ghost" data-action="reset">Reset</button>
  </div>
  <div class="cell-live"></div>
  <details class="solution"><summary>Show a solution</summary>
    {code_html(solution.body)}{sol_out}{figs}
    <button type="button" class="btn-ghost" data-action="load-solution">Load solution into editor</button>
  </details>
  {json_script(data, "cell-data")}
</div>"""


def render_quiz(block, slug, report, start_number):
    questions = yaml.safe_load(block.body)
    out = ['<section class="quiz" aria-label="Quiz">']
    for i, q in enumerate(questions):
        number = start_number + i
        opts = q["options"]
        if len(opts) != 4 or q["answer"] not in LETTERS:
            raise BuildError(f"{slug}: quiz question {number} must have 4 options and answer A-D")
        if len(set(map(str, opts))) != 4:
            raise BuildError(f"{slug}: quiz question {number} has duplicate options")
        report.quiz_answers.append(q["answer"])
        qid = f"{slug}-q{number}"
        items = "".join(
            f'<li><label><input type="radio" name="{qid}" value="{LETTERS[j]}"> '
            f'<span class="opt-letter">{LETTERS[j]}.</span> {inline_md(opt)}</label></li>'
            for j, opt in enumerate(opts)
        )
        out.append(f"""
<div class="quiz-q" data-answer="{q['answer']}" id="{qid}" role="group" aria-labelledby="{qid}-stem">
  <p class="quiz-stem" id="{qid}-stem"><span class="quiz-num">Q{number}.</span> {inline_md(q['q'])}</p>
  <ol class="quiz-options">{items}</ol>
  <button type="button" class="btn-primary" data-action="grade">Check answer</button>
  <div class="quiz-feedback" aria-live="polite"></div>
  <div class="quiz-explain" hidden>{inline_md(q['explain'])}</div>
</div>""")
    out.append('<p class="quiz-score" aria-live="polite"></p></section>')
    return "".join(out), len(questions)


MD_EXTENSIONS = ["tables", "toc", "admonition", "attr_list", "md_in_html", "smarty", "sane_lists"]


def render_page(page, site, out_dir, img_dir):
    slug = page["slug"]
    text = (CONTENT / f"{slug}.md").read_text(encoding="utf-8")
    md_text, blocks = split_blocks(text)
    report = PageReport(slug)

    setups = [b for b in blocks if b.kind == "setup"]
    if len(setups) > 1:
        raise BuildError(f"{slug}: at most one setup block")
    setup = setups[0].body if setups else ""
    if setup:
        fail_on(runner.run_cell("", setup=setup), f"{slug}: setup")
    solutions = {b.opts.get("for"): b for b in blocks if b.kind == "solution"}
    checks = {b.opts.get("for"): b for b in blocks if b.kind == "check"}

    rendered = {}
    quiz_number = 1
    for i, block in enumerate(blocks):
        if block.kind == "setup":
            rendered[i] = (f'<div class="cell cell-setup">{code_html(block.body, "Setup - run this first")}</div>')
        elif block.kind == "run":
            rendered[i] = render_run(block, setup, slug, img_dir, report)
        elif block.kind == "exercise":
            ex_id = block.opts.get("id")
            rendered[i] = render_exercise(block, solutions.get(ex_id), checks.get(ex_id),
                                          setup, slug, img_dir, report)
        elif block.kind in ("solution", "check"):
            rendered[i] = ""
        elif block.kind == "quiz":
            rendered[i], n = render_quiz(block, slug, report, quiz_number)
            quiz_number += n
        else:
            if block.opts.get("lang") in ("python", ""):
                rendered[i] = code_html(block.body)
            else:
                rendered[i] = f"<pre><code>{html.escape(block.body)}</code></pre>"

    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs={"toc": {"permalink": False}})
    body = md.convert(md_text)
    for i, frag in rendered.items():
        body = body.replace(f"<p>BLOCK{i}PLACEHOLDER</p>", frag)
    if "PLACEHOLDER" in body:
        raise BuildError(f"{slug}: a block placeholder was not replaced (fence inside a list?)")

    pages = site["pages"]
    idx = next(i for i, p in enumerate(pages) if p["slug"] == slug)
    prev_p = pages[idx - 1] if idx > 0 else None
    next_p = pages[idx + 1] if idx + 1 < len(pages) else None

    nav = "".join(
        f'<li><a href="{p["slug"]}.html" data-page="{p["slug"]}"'
        f'{" aria-current=page" if p["slug"] == slug else ""}>'
        f'<span class="nav-num">{html.escape(str(p.get("num", "")))}</span>'
        f'<span class="nav-title">{html.escape(p["nav"])}</span></a></li>'
        for p in pages
    )
    pager = '<nav class="pager" aria-label="Previous and next lesson">'
    pager += (f'<a class="pager-prev" href="{prev_p["slug"]}.html"><small>Previous</small>'
              f'{html.escape(prev_p["title"])}</a>' if prev_p else "<span></span>")
    pager += (f'<a class="pager-next" href="{next_p["slug"]}.html"><small>Next</small>'
              f'{html.escape(next_p["title"])}</a>' if next_p else "<span></span>")
    pager += "</nav>"

    lesson_tools = ""
    if page.get("notebook"):
        nb = f"{slug}.ipynb"
        colab = (f"https://colab.research.google.com/github/{site['github_user']}/{site['repo']}"
                 f"/blob/main/docs/notebooks/{nb}")
        lesson_tools = (f'<div class="lesson-tools"><a href="{colab}" target="_blank" rel="noopener" '
                        f'title="Opens in a new tab">Open in Colab</a>'
                        f'<a href="notebooks/{nb}" download>Download notebook</a>'
                        f'<a href="notebooks/{slug}-solutions.ipynb" download>Solutions notebook</a></div>')

    template = (SITE_SRC / "page.html").read_text(encoding="utf-8")
    page_html = (template
                 .replace("{{title}}", html.escape(page["title"]))
                 .replace("{{site_title}}", html.escape(site["title"]))
                 .replace("{{description}}", html.escape(page.get("description", site["description"])))
                 .replace("{{slug}}", slug)
                 .replace("{{nav}}", nav)
                 .replace("{{lesson_tools}}", lesson_tools)
                 .replace("{{content}}", body)
                 .replace("{{pager}}", pager)
                 .replace("{{repo_url}}", f"https://github.com/{site['github_user']}/{site['repo']}")
                 .replace("{{setup_json}}", json_script({"setup": setup}, "page-setup")))
    (out_dir / f"{slug}.html").write_text(page_html, encoding="utf-8")

    if page.get("notebook"):
        write_notebooks(text, page, out_dir / "notebooks")
    return report


# ---------------------------------------------------------------- notebooks

def _nb_cell(kind, source):
    cell = {"cell_type": kind, "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}
    if kind == "code":
        cell.update({"execution_count": None, "outputs": []})
    return cell


ADMONITION_LABELS = {"few": "Design principle", "warning": "Warning", "note": "Note"}
ADMONITION_RE = re.compile(r'^!!!\s+(\w+)\s*(?:"([^"]*)")?\s*$')


def _admonitions_to_blockquotes(prose):
    """Rewrite `!!! kind "Title"` callouts as blockquotes for the notebooks.

    Jupyter has no admonition extension: left alone, the marker line shows as
    text and the indented body renders as a code block.
    """
    lines = prose.splitlines()
    out = []
    i = 0
    while i < len(lines):
        m = ADMONITION_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        label = ADMONITION_LABELS.get(m.group(1), m.group(1).title())
        heading = f"**{label}: {m.group(2)}**" if m.group(2) else f"**{label}**"
        body = []
        i += 1
        while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
            body.append(lines[i][4:] if lines[i].startswith("    ") else "")
            i += 1
        while body and not body[-1].strip():
            body.pop()
        out.append(f"> {heading}")
        out.append(">")
        out.extend(f"> {b}".rstrip() for b in body)
        out.append("")
    return "\n".join(out)


def _clean_prose(prose):
    prose = re.sub(r"<!--.*?-->", "", prose, flags=re.S)
    prose = re.sub(r"\{[:#.][^}]*\}", "", prose)  # attr_list markers
    prose = _admonitions_to_blockquotes(prose)
    return prose.strip()


def write_notebooks(text, page, nb_dir):
    nb_dir.mkdir(parents=True, exist_ok=True)
    for with_solutions in (False, True):
        cells = []
        pos = 0
        for m in FENCE.finditer(text):
            prose = _clean_prose(text[pos:m.start()])
            pos = m.end()
            if prose:
                cells.append(_nb_cell("markdown", prose))
            kind, opts = parse_info(m.group("info"))
            body = m.group("body")
            if kind in ("setup", "run", "code"):
                cells.append(_nb_cell("code", body))
            elif kind == "exercise":
                title = opts.get("title", "Your turn")
                cells.append(_nb_cell("markdown", f"**Exercise {opts.get('id')}: {title}**"))
                if not with_solutions:
                    cells.append(_nb_cell("code", body))
            elif kind == "solution" and with_solutions:
                cells.append(_nb_cell("code", f"# Solution to exercise {opts.get('for')}\n" + body))
            elif kind == "quiz":
                cells.append(_nb_cell("markdown", "*The quiz for this lesson is interactive on the website.*"))
        tail = _clean_prose(text[pos:])
        if tail:
            cells.append(_nb_cell("markdown", tail))
        nb = {
            "cells": cells,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                         "language_info": {"name": "python"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        for i, cell in enumerate(nb["cells"]):
            cell["id"] = f"{page['slug']}-{i}"
        name = f"{page['slug']}-solutions.ipynb" if with_solutions else f"{page['slug']}.ipynb"
        (nb_dir / name).write_text(json.dumps(nb, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- assets

def write_assets(out_dir):
    assets = out_dir / "assets"
    (assets / "py").mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "app.js", "live.js"):
        shutil.copy(SITE_SRC / name, assets / name)
    light = HtmlFormatter(style="friendly").get_style_defs(".highlight")
    dark = HtmlFormatter(style="monokai").get_style_defs(".highlight")
    dark_scoped = "\n".join(
        f"  :root:not([data-theme=light]) {line}" for line in dark.splitlines() if line.startswith(".highlight")
    )
    (assets / "pygments.css").write_text(
        light + "\n@media (prefers-color-scheme: dark) {\n" + dark_scoped + "\n}\n", encoding="utf-8")
    shutil.copy(ROOT / "tools" / "runner.py", assets / "py" / "runner.py")
    (out_dir / "data").mkdir(exist_ok=True)
    shutil.copy(DATA_CSV, out_dir / "data" / "penguins.csv")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")


def build(out_dir):
    out_dir = Path(out_dir)
    site = yaml.safe_load((CONTENT / "_site.yml").read_text(encoding="utf-8"))
    for sub in ("img", "notebooks"):
        if (out_dir / sub).exists():
            shutil.rmtree(out_dir / sub)
    img_dir = out_dir / "img"
    img_dir.mkdir(parents=True)
    write_assets(out_dir)
    reports = []
    for page in site["pages"]:
        print(f"  building {page['slug']} ...", flush=True)
        reports.append(render_page(page, site, out_dir, img_dir))
    return site, reports


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "docs"))
    args = parser.parse_args()
    try:
        _, reports = build(args.out)
    except BuildError as exc:
        print(f"\nBUILD FAILED\n{exc}", file=sys.stderr)
        sys.exit(1)
    figs = sum(len(r.figures) for r in reports)
    exs = sum(len(r.exercises) for r in reports)
    qs = sum(len(r.quiz_answers) for r in reports)
    print(f"Built {len(reports)} pages, {figs} figures, {exs} graded exercises, {qs} quiz questions.")


if __name__ == "__main__":
    main()
