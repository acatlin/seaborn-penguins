"""Execute one lesson cell and collect its output.

This file is shared by two runtimes so that what the build checks is exactly
what learners run:

* tools/build_site.py imports it under CPython to render every figure and to
  test every exercise solution.
* The website copies it to docs/assets/py/runner.py and loads it into Pyodide
  (Python compiled to WebAssembly) to power the in-browser editors.
"""

import ast
import base64
import contextlib
import io
import re
import traceback
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

DATA_PATH = "penguins.csv"
_original_load_dataset = sns.load_dataset


def _load_dataset(name, *args, **kwargs):
    """Serve the bundled penguins CSV so lessons work offline and identically."""
    if name == "penguins":
        return pd.read_csv(DATA_PATH)
    return _original_load_dataset(name, *args, **kwargs)


sns.load_dataset = _load_dataset

# Warnings raised inside the libraries themselves (not caused by lesson code).
# seaborn 0.13 still passes `vert=` to matplotlib >= 3.10 boxplot/violinplot.
LIBRARY_WARNINGS = [r"vert: bool will be deprecated"]
plt.show = lambda *args, **kwargs: None  # figures are collected, not shown


# ---------------------------------------------------------------------------
# Helpers injected into the namespace of exercise *checks* (never shown to
# learners). They inspect the matplotlib objects a chart leaves behind.

def chart_axes():
    """All Axes in the current figure that contain plotted data."""
    axes = [ax for ax in plt.gcf().axes if ax.has_data()]
    if not axes:
        raise AssertionError("I can't find a chart yet - did your code draw one?")
    return axes


def points(ax):
    """(n, 2) array of every scatter point drawn on ax."""
    import numpy as np

    chunks = [np.asarray(c.get_offsets()) for c in ax.collections
              if type(c).__name__ == "PathCollection" and len(c.get_offsets())]
    if not chunks:
        raise AssertionError("I don't see any scatter points on the chart.")
    return np.vstack(chunks)


def legend_labels(ax=None):
    """Legend entries from the Axes legend and any figure-level legends."""
    found = []
    legends = [ax.get_legend()] if ax is not None else []
    legends += list(plt.gcf().legends)
    if ax is None:
        legends += [a.get_legend() for a in plt.gcf().axes]
    for leg in legends:
        if leg is not None:
            found += [t.get_text() for t in leg.get_texts()]
    return found


def colors_used(ax):
    """Set of hex colors used by the marks (points, bars, lines) on ax."""
    from matplotlib.colors import to_hex

    found = set()
    for c in ax.collections:
        for rgba in list(c.get_facecolors()) + list(c.get_edgecolors()):
            found.add(to_hex(rgba))
    for p in ax.patches:
        found.add(to_hex(p.get_facecolor()))
    for line in ax.lines:
        found.add(to_hex(line.get_color()))
    return found


def near_color(hex_color, used, tol=0.06):
    """True if a color close to hex_color is in the set `used`."""
    from matplotlib.colors import to_rgb

    target = to_rgb(hex_color)
    return any(max(abs(a - b) for a, b in zip(target, to_rgb(u))) <= tol for u in used)


CHECK_HELPERS = {
    "chart_axes": chart_axes,
    "points": points,
    "legend_labels": legend_labels,
    "colors_used": colors_used,
    "near_color": near_color,
}


def _exec_with_echo(code, ns, filename):
    """Run code like a notebook cell: echo the value of a trailing expression."""
    tree = ast.parse(code, filename=filename)
    last = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last = ast.Expression(tree.body.pop().value)
    exec(compile(tree, filename, "exec"), ns)
    if last is not None:
        value = eval(compile(last, filename, "eval"), ns)
        # Matplotlib/seaborn objects echo noisy reprs; notebooks hide them too.
        if value is not None and not _is_plot_object(value):
            print(repr(value))


def _is_plot_object(value):
    module = type(value).__module__ or ""
    if module.startswith(("matplotlib", "seaborn")):
        return True
    if isinstance(value, (list, tuple)) and value:
        return all(_is_plot_object(v) for v in value)
    return False


def _format_error(sources):
    """Traceback trimmed to the learner's own lines plus the final message."""
    lines = traceback.format_exc().splitlines()
    keep = [lines[0]]
    for line in lines:
        match = re.search(r'File "(<setup>|<your code>|<check>)", line (\d+)', line)
        if match:
            keep.append(line)
            src = sources.get(match.group(1), "").splitlines()
            lineno = int(match.group(2))
            if 0 < lineno <= len(src):
                keep.append("    " + src[lineno - 1].strip())
    keep.append(lines[-1])
    return "\n".join(keep)


def run_cell(code, setup="", check="", dpi=110, encode=False):
    """Run setup + code (+ optional check) in a fresh namespace.

    Returns a dict with keys: stdout, figures (PNG bytes, or base64 strings if
    encode=True), warnings, error, check_ok, check_message.
    """
    plt.close("all")
    matplotlib.rcdefaults()
    ns = {"__name__": "__main__"}
    out = io.StringIO()
    result = {
        "stdout": "",
        "figures": [],
        "warnings": [],
        "error": None,
        "check_ok": None,
        "check_message": "",
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for pattern in LIBRARY_WARNINGS:
            warnings.filterwarnings("ignore", message=pattern)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                if setup:
                    exec(compile(setup, "<setup>", "exec"), ns)
                _exec_with_echo(code, ns, "<your code>")
            except Exception:
                result["error"] = _format_error({"<setup>": setup, "<your code>": code})
        result["stdout"] = out.getvalue()
        if check and result["error"] is None:
            check_out = io.StringIO()
            with contextlib.redirect_stdout(check_out):
                try:
                    ns.update(CHECK_HELPERS)
                    exec(compile(check, "<check>", "exec"), ns)
                    result["check_ok"] = True
                except AssertionError as exc:
                    result["check_ok"] = False
                    print(str(exc) or "Not quite yet - compare with the task.")
                except Exception as exc:  # the learner's chart is missing a piece
                    result["check_ok"] = False
                    print(f"The checker could not inspect your chart ({type(exc).__name__}: {exc}).")
            result["check_message"] = check_out.getvalue().strip()
        elif check:
            result["check_ok"] = False
            result["check_message"] = "Fix the error first, then check again."

        for num in plt.get_fignums():
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
            data = buf.getvalue()
            result["figures"].append(base64.b64encode(data).decode("ascii") if encode else data)
    result["warnings"] = [f"{w.category.__name__}: {w.message}" for w in caught]
    plt.close("all")
    return result


def run_cell_json(code, setup="", check=""):
    """Entry point for the browser: returns JSON so JavaScript can parse it."""
    import json

    return json.dumps(run_cell(code, setup=setup, check=check, encode=True))
