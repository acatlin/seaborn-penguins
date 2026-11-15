"""Check the built site in a real browser: a headless Chrome driven over the DevTools protocol.

Usage:  python tools/browser_check.py run [SLUG ...]     every exercise and every example
        python tools/browser_check.py widths             no page wider than a phone
        python tools/browser_check.py snapshot FILE      store the layout of every page at 1600 px
        python tools/browser_check.py compare OLD NEW    what moved between two snapshots

The test suite runs the lessons under CPython and the pinned matplotlib. Learners run them in the
browser, on Pyodide, whose matplotlib is older. This script is the check of that second runtime.
It is not part of the test suite and CI does not run it: it needs Chrome, the network (Pyodide
comes from a CDN) and one package that requirements.txt does not list:

        pip install websocket-client

Chrome is looked for in the usual places. Set the environment variable CHROME to its path if it
is somewhere else. The script serves docs/ itself, on a free port, and stops the server when done.

run       For each exercise: the solution, the untouched starter, and every attempt that
          tests/test_site.py keeps in a function named exercise_N_N_attempts. Each goes through
          the page's own "Run & check" button, and its verdict, its message and its number of
          figures are compared with tools/runner.py under CPython. For each example: "Edit &
          run" must give no error, and the same output and number of figures as the build.
          A full pass takes about five minutes.
widths    Opens every page at 320, 360, 390, 414, 600, 768 and 860 px and compares the width of
          the page with the width of the window.
snapshot  The position and size of every element of every page at 1600 px, as JSON. Take one
          before a change to the stylesheet or to a page and one after, then compare.
compare   Pages whose elements are all where they were, and for the others: what was added,
          what changed size, and whether everything else only moved down or up as a block.
"""

import base64
import difflib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

CHROME_PLACES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
]
WIDTHS = (320, 360, 390, 414, 600, 768, 860)

# Run in the page: figures on the site are loaded lazily, so a measurement has to ask for them.
EAGER = """(async () => {
  document.querySelectorAll('img').forEach(i => { i.loading = 'eager'; });
  await Promise.race([Promise.all([...document.images].map(i => i.complete ? 1 : new Promise(r => { i.onload = i.onerror = r; }))),
                      new Promise(r => setTimeout(r, 15000))]);
  await new Promise(r => setTimeout(r, 200));
  return document.images.length;
})()"""

LAYOUT = """(() => JSON.stringify([...document.querySelectorAll('body *')].map(e => {
  const r = e.getBoundingClientRect();
  return [e.tagName + (e.id ? '#' + e.id : ''), +(r.left + scrollX).toFixed(2), +(r.top + scrollY).toFixed(2),
          +r.width.toFixed(2), +r.height.toFixed(2)];
})))()"""

# Setting an editor's value from a script fires no input event, so nothing is stored for the learner.
HARNESS = """
window.__wait = (box) => new Promise((resolve) => {
  const started = Date.now();
  const tick = () => {
    const live = box.querySelector('.cell-live');
    const busy = [...box.querySelectorAll('.cell-toolbar button')].some(b => b.disabled);
    const label = live.querySelector('.live-label');
    if (!busy && label && label.textContent !== 'Running...') return resolve();
    if (Date.now() - started > 240000) return resolve();
    setTimeout(tick, 100);
  };
  setTimeout(tick, 150);
});
window.__read = (box) => {
  const res = box.querySelector('.check-result');
  const err = box.querySelector('.live-error');
  return JSON.stringify({ok: res ? res.classList.contains('ok') : null, message: res ? res.textContent.slice(2).trim() : '',
                         error: err ? err.textContent : null, figures: box.querySelectorAll('img.live-figure').length,
                         stdout: [...box.querySelectorAll('.live-stdout:not(.live-error)')].map(e => e.textContent).join('\\n')});
};
window.__exercise = async (id, code) => {
  const box = document.getElementById('ex-' + id);
  box.querySelector('.cell-editor').value = code;
  box.querySelector('[data-action="check"]').click();
  await window.__wait(box);
  return window.__read(box);
};
window.__example = async (n) => {
  const cell = document.querySelectorAll('[data-cell]')[n];
  cell.querySelector('[data-action="edit"]').click();
  await window.__wait(cell);
  return window.__read(cell);
};
"""


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def find_chrome():
    for place in [os.environ.get("CHROME")] + CHROME_PLACES:
        if place and (Path(place).is_file() or shutil.which(place)):
            return place if Path(place).is_file() else shutil.which(place)
    sys.exit("Chrome was not found. Set the environment variable CHROME to the path of chrome.")


class Browser:
    """A headless Chrome with its own profile, and a server for docs/."""

    def __init__(self):
        try:
            import websocket
        except ImportError:
            sys.exit("This script needs one more package: pip install websocket-client")
        self.scratch = tempfile.mkdtemp(prefix="browser-check-")
        self.site_port, debug_port = free_port(), free_port()
        self.server = subprocess.Popen([sys.executable, "-m", "http.server", str(self.site_port), "--bind", "127.0.0.1",
                                        "-d", str(ROOT / "docs")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.chrome = subprocess.Popen([find_chrome(), "--headless=new", f"--remote-debugging-port={debug_port}",
                                        f"--user-data-dir={self.scratch}", "--no-first-run", "--disable-gpu",
                                        "--window-size=1600,1000", "about:blank"],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json").read())
                page = next(t for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.5)
        else:
            self.close()
            sys.exit("Chrome did not start.")
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], suppress_origin=True, timeout=600)
        self.calls = 0
        for method in ("Page.enable", "Runtime.enable", "Network.enable"):
            self.call(method)
        self.call("Network.setCacheDisabled", cacheDisabled=True)  # or a snapshot may use the old stylesheet

    def call(self, method, **params):
        self.calls += 1
        mine = self.calls
        self.ws.send(json.dumps({"id": mine, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == mine:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    def open(self, slug, width=1600, height=1000):
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
        self.call("Page.navigate", url=f"http://127.0.0.1:{self.site_port}/{slug}.html?v={time.time()}")
        for _ in range(300):
            if self.js("document.readyState") == "complete":
                return
            time.sleep(0.1)
        raise RuntimeError(f"{slug}.html did not load")

    def js(self, expression, wait=False):
        result = self.call("Runtime.evaluate", expression=expression, awaitPromise=wait, returnByValue=True)
        if "exceptionDetails" in result:
            raise RuntimeError(json.dumps(result["exceptionDetails"])[:1500])
        return result["result"].get("value")

    def picture(self, path):
        Path(path).write_bytes(base64.b64decode(self.call("Page.captureScreenshot", format="png")["data"]))

    def close(self):
        try:
            self.call("Browser.close")
        except Exception:
            pass
        for process in (getattr(self, "chrome", None), getattr(self, "server", None)):
            if process is None:
                continue
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
        shutil.rmtree(self.scratch, ignore_errors=True)


def site_pages():
    import yaml

    site = yaml.safe_load((ROOT / "content" / "_site.yml").read_text(encoding="utf-8"))
    return site["pages"]


def attempts_for(ex_id):
    """{name: (code, hint or None)} from tests/test_site.py, if it keeps attempts for this exercise."""
    import test_site

    function = getattr(test_site, "exercise_" + ex_id.replace(".", "_") + "_attempts", None)
    return function() if function else {}


def run(slugs):
    import build_site
    import runner

    runner.DATA_PATH = str(ROOT / "data" / "penguins.csv")
    slugs = slugs or [p["slug"] for p in site_pages() if p.get("notebook")]
    count = {"exercises": 0, "attempts": 0, "examples": 0, "figures drawn by examples": 0}
    problems = []
    browser = Browser()
    try:
        for slug in slugs:
            _, blocks = build_site.split_blocks((ROOT / "content" / f"{slug}.md").read_text(encoding="utf-8"))
            setup = next((b.body for b in blocks if b.kind == "setup"), "")
            browser.open(slug)
            browser.js(HARNESS)
            started = time.time()
            for block in blocks:
                if block.kind != "exercise":
                    continue
                ex = block.opts["id"]
                check = next(b.body for b in blocks if b.kind == "check" and b.opts.get("for") == ex)
                tries = {"solution": next(b.body for b in blocks if b.kind == "solution" and b.opts.get("for") == ex),
                         "starter": block.body}
                tries.update({name: code for name, (code, _hint) in attempts_for(ex).items()})
                count["exercises"] += 1
                count["attempts"] += len(tries) - 2
                for name, code in tries.items():
                    got = json.loads(browser.js(f"window.__exercise({json.dumps(ex)}, {json.dumps(code)})", wait=True))
                    want = runner.run_cell(code, setup=setup, check=check)
                    same = (got["ok"] == bool(want["check_ok"]) and got["message"] == want["check_message"]
                            and bool(got["error"]) == bool(want["error"]) and got["figures"] == len(want["figures"]))
                    if not same or (name == "solution" and got["ok"] is not True):
                        problems.append(f"{slug}, exercise {ex}, {name}:\n      browser: {got['ok']} | {got['message']}"
                                        f" | figures {got['figures']} | {got['error'] or ''}\n      build:   "
                                        f"{want['check_ok']} | {want['check_message']} | figures {len(want['figures'])}")
            for n, block in enumerate(b for b in blocks if b.kind == "run"):
                got = json.loads(browser.js(f"window.__example({n})", wait=True))
                want = runner.run_cell(block.body, setup=setup)
                count["examples"] += 1
                count["figures drawn by examples"] += got["figures"]
                if got["error"] or got["figures"] != len(want["figures"]) or got["stdout"].strip() != want["stdout"].strip():
                    problems.append(f"{slug}, example starting {block.body.splitlines()[0]!r}:\n      browser: "
                                    f"{got['error'] or got['stdout']!r} | figures {got['figures']}\n      build:   "
                                    f"{want['stdout']!r} | figures {len(want['figures'])}")
            print(f"  {slug}: {round(time.time() - started)} s", flush=True)
        versions = browser.js("(async () => { const py = await loadPyodide({indexURL: document.querySelector('script[src*=pyodide]')"
                              ".src.replace('pyodide.js', '')}); await py.loadPackage('matplotlib'); return py.runPython("
                              "'import sys, matplotlib; sys.version.split()[0] + \" and matplotlib \" + matplotlib.__version__'); })()",
                              wait=True)
        print(f"In the browser: Python {versions}.")
    finally:
        browser.close()
    print(", ".join(f"{n} {what}" for what, n in count.items()))
    print(f"Differences between the browser and the build: {len(problems)}")
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


def widths():
    browser = Browser()
    wide = []
    pages = [p["slug"] for p in site_pages()]
    try:
        for width in WIDTHS:
            for slug in pages:
                browser.open(slug, width, 900)
                browser.js(EAGER, wait=True)
                page, window = json.loads(browser.js("JSON.stringify([document.documentElement.scrollWidth, window.innerWidth])"))
                if page > window:
                    wide.append(f"{slug} is {page} px wide in a window of {window} px")
    finally:
        browser.close()
    print(f"{len(pages)} pages at {len(WIDTHS)} widths ({WIDTHS[0]} to {WIDTHS[-1]} px). Wider than the window: {len(wide)}")
    for line in wide:
        print("  " + line)
    return 1 if wide else 0


def snapshot(path):
    browser = Browser()
    layout = {}
    try:
        for page in site_pages():
            browser.open(page["slug"])
            browser.js(EAGER, wait=True)
            layout[page["slug"]] = json.loads(browser.js(LAYOUT))
    finally:
        browser.close()
    Path(path).write_text(json.dumps(layout), encoding="utf-8")
    print(f"{sum(len(v) for v in layout.values())} elements on {len(layout)} pages, written to {path}")
    return 0


def compare(old_path, new_path):
    old_layout = json.loads(Path(old_path).read_text(encoding="utf-8"))
    new_layout = json.loads(Path(new_path).read_text(encoding="utf-8"))
    for slug in sorted(set(old_layout) | set(new_layout)):
        old, new = old_layout.get(slug, []), new_layout.get(slug, [])
        if old == new:
            print(f"{slug}: {len(old)} elements, all where they were")
            continue

        def shape(element):  # everything but the distance from the top of the page
            return element[0], element[1], element[3], element[4]

        matcher = difflib.SequenceMatcher(a=[shape(e) for e in old], b=[shape(e) for e in new], autojunk=False)
        unmoved, shifts, gone, added = 0, [], [], []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                gone += old[i1:i2]
                added += new[j1:j2]
                continue
            for before, after in zip(old[i1:i2], new[j1:j2]):
                by = round(after[2] - before[2], 1)
                unmoved += by == 0
                if by:
                    shifts.append(by)
        kinds = {}
        for element in gone:
            kinds[element[0].split("#")[0]] = kinds.get(element[0].split("#")[0], 0) + 1
        print(f"{slug}: {len(old)} -> {len(new)} elements. {unmoved} where they were. {len(shifts)} kept their size and "
              f"left edge and moved by {sorted(set(shifts))[:8]} px. {len(added)} new or resized, and {len(gone)} of the old "
              f"ones resized or gone: {kinds}")
    return 0


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("run", "widths", "snapshot", "compare"):
        sys.exit(__doc__)
    if args[0] == "run":
        return run(args[1:])
    if args[0] == "widths":
        return widths()
    if args[0] == "snapshot" and len(args) == 2:
        return snapshot(args[1])
    if args[0] == "compare" and len(args) == 3:
        return compare(args[1], args[2])
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
