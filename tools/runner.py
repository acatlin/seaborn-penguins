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
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

DATA_PATH = "penguins.csv"
RANDOM_SEED = 0
_default_rng = np.random.default_rng


def _seeded_default_rng(seed=None):
    """numpy's default_rng, seeded when the caller gives no seed.

    seaborn draws its bootstrapped confidence intervals (barplot, pointplot,
    lineplot, regplot) from ``np.random.default_rng(None)``, so without this every
    build and every browser run would shade a slightly different band. A fixed
    seed makes the rendered figures reproducible byte for byte.
    """
    return _default_rng(RANDOM_SEED if seed is None else seed)


np.random.default_rng = _seeded_default_rng
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


def chart_forms(ax):
    """Names of the chart forms drawn on ax, read from the objects that seaborn, matplotlib
    and pandas leave on an Axes. A chart built in layers has several.

    One measurement:      "histogram" (bars, step outlines), "density" (a KDE curve), "ecdf",
                          "area" (a filled histogram or density with no outline)
    Groups on an axis:    "bars" (one bar per group: a mean or a count), "box", "violin",
                          "strip" (one dot per row), "points" (one marker per group: a mean),
                          "joined" (a line that runs from one group to the next)
    Two measurements:     "scatter", "line" (a trend line or a line chart), "mesh" (a 2-D
                          histogram, a heatmap, density contours)
    Parts of a whole:     "pie"
    """
    import numpy as np

    forms = set()

    def numbers(values):
        try:
            return np.asarray(values, dtype=float)
        except (TypeError, ValueError):
            return np.array([])

    group_axis = next((name for name, axis in (("x", ax.xaxis), ("y", ax.yaxis))
                       if type(axis.get_units()).__name__ == "UnitData"), None)

    def along_groups(x, y):
        """The extent of something along the axis that carries the groups."""
        values = x if group_axis == "x" else y
        return float(np.ptp(values)) if len(values) else 0.0

    # ---- patches: wedges, boxes, bars
    kinds = [type(p).__name__ for p in ax.patches]
    if "Wedge" in kinds:
        forms.add("pie")
    if "PathPatch" in kinds or any(type(c).__name__ == "BoxPlotContainer" for c in ax.containers):
        forms.add("box")
    bars = [p for p in ax.patches if type(p).__name__ == "Rectangle" and (p.get_width() or p.get_height())]
    if bars:
        def touching(rects):
            """True if the bars stand edge to edge, as the bins of a histogram do."""
            for start, size in ((lambda p: p.get_x(), lambda p: p.get_width()),
                                (lambda p: p.get_y(), lambda p: p.get_height())):
                spans = sorted({(round(start(p), 6), round(start(p) + size(p), 6)) for p in rects})
                if len(spans) > 1 and all(abs(a[1] - b[0]) < 1e-6 * max(1.0, abs(a[1]))
                                          for a, b in zip(spans, spans[1:])):
                    return True
            return False

        groups = [list(c) for c in ax.containers if type(c).__name__ == "BarContainer"] or [bars]
        if group_axis is None and (len(bars) >= 8 or all(touching(g) for g in groups)):
            forms.add("histogram")
        else:
            forms.add("bars")

    # ---- collections: points, violins, bands, meshes
    filled = False
    for c in ax.collections:
        kind = type(c).__name__
        if kind in ("QuadMesh", "QuadContourSet"):
            forms.add("mesh")
        elif kind == "PathCollection" and len(c.get_offsets()):
            forms.add("strip" if group_axis else "scatter")
        elif "PolyCollection" in kind and c.get_paths():
            vertices = np.vstack([path.vertices for path in c.get_paths()])
            if group_axis and along_groups(vertices[:, 0], vertices[:, 1]) < 1:
                forms.add("violin")
            else:
                filled = True

    # ---- lines: steps, curves, markers, trend lines
    drawn = False
    for line in ax.lines:
        raw_x, raw_y = numbers(line.get_xdata(orig=False)), numbers(line.get_ydata(orig=False))
        if not len(raw_x) or len(raw_x) != len(raw_y):
            continue
        keep = np.isfinite(raw_x) & np.isfinite(raw_y)
        x, y = raw_x[keep], raw_y[keep]
        if not len(x):
            continue
        solid = line.get_linestyle() not in ("None", "none", "", " ")
        marked = line.get_marker() not in (None, "None", "none", "", " ")
        if group_axis:
            if marked and not (len(x) == 1 and solid):  # a violin marks its median with a one-point line
                forms.add("points")
            if len(x) == 5 and solid and x[0] == x[-1] and y[0] == y[-1]:
                forms.add("box")  # the outline of an unfilled box
            elif solid and len(x) > 1 and along_groups(x, y) >= 0.99:
                forms.add("joined")
            continue
        if not solid or len(x) < 2 or np.ptp(x) == 0 or np.ptp(y) == 0:
            continue  # markers alone, or a reference line (axvline, axhline)
        drawn = True
        if len(x) == 5 and x[0] == x[-1] and y[0] == y[-1]:
            forms.add("box")
        elif line.get_drawstyle().startswith("steps"):
            # seaborn starts an ECDF at minus infinity, so look at each coordinate's own finite values
            climbs = any(abs(v.min()) < 1e-9 and abs(v.max() - 1) < 1e-9 and (np.diff(v) >= 0).all()
                         for v in (raw_x[np.isfinite(raw_x)], raw_y[np.isfinite(raw_y)]))
            forms.add("ecdf" if climbs else "histogram")
        else:
            def area(base, height):
                order = np.argsort(base, kind="stable")
                base, height = base[order], height[order]
                return float(np.sum(np.diff(base) * (height[1:] + height[:-1]) / 2))

            chord = (y - y[0]) * (x[-1] - x[0]) - (x - x[0]) * (y[-1] - y[0])
            bent = len(x) >= 50 and float(np.abs(chord).max()) > 1e-6 * np.ptp(x) * np.ptp(y)
            curve = bent and any(height.min() >= 0 and 0.01 <= area(base, height) <= 1.05
                                 for base, height in ((x, y), (y, x)))
            forms.add("density" if curve else "line")
    if "box" in forms:
        forms.discard("points")  # the markers on a box plot are its outliers, not means
    if filled and not drawn and group_axis is None and not forms & {"scatter", "histogram", "bars"}:
        forms.add("area")
    return forms


CHECK_HELPERS = {
    "chart_axes": chart_axes,
    "points": points,
    "legend_labels": legend_labels,
    "colors_used": colors_used,
    "near_color": near_color,
    "chart_forms": chart_forms,
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
    np.random.seed(RANDOM_SEED)  # stripplot jitter and any np.random call in a cell
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
