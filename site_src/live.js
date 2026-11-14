// Live Python in the browser via Pyodide. Loaded lazily on the first Run click.
// The Python side is tools/runner.py - the same code the site build uses.
(function () {
  "use strict";
  var PYODIDE_VERSION = "0.27.2";
  var INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_VERSION + "/full/";
  var statusEl = document.querySelector("[data-py-status]");
  var setupEl = document.querySelector(".page-setup");
  var setup = setupEl ? JSON.parse(setupEl.textContent).setup : "";
  var pyPromise = null;

  function status(text, state) {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.dataset.state = state || "";
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("Could not download " + src)); };
      document.head.appendChild(s);
    });
  }

  function getPython() {
    if (pyPromise) return pyPromise;
    pyPromise = (async function () {
      status("Python: downloading (first time ~30 MB)...", "loading");
      await loadScript(INDEX_URL + "pyodide.js");
      var py = await window.loadPyodide({ indexURL: INDEX_URL });
      status("Python: installing pandas, matplotlib, seaborn...", "loading");
      await py.loadPackage(["numpy", "pandas", "matplotlib", "scipy", "micropip"]);
      // seaborn is pure Python: install the same version the site is built with from PyPI
      await py.runPythonAsync("import micropip\nawait micropip.install('seaborn==0.13.2')");
      var files = await Promise.all([
        fetch("data/penguins.csv").then(function (r) { return r.text(); }),
        fetch("assets/py/runner.py").then(function (r) { return r.text(); })
      ]);
      py.FS.writeFile("penguins.csv", files[0]);
      py.FS.writeFile("runner.py", files[1]);
      py.runPython("import sys; sys.path.insert(0, '.'); import runner");
      status("Python: ready", "ready");
      return py;
    })();
    pyPromise.catch(function (err) {
      status("Python: failed to load", "error");
      pyPromise = null;
      console.error(err);
    });
    return pyPromise;
  }

  async function runCode(code, check) {
    var py = await getPython();
    py.globals.set("_sbp_code", code);
    py.globals.set("_sbp_setup", setup);
    py.globals.set("_sbp_check", check || "");
    var out = py.runPython("runner.run_cell_json(_sbp_code, _sbp_setup, _sbp_check)");
    return JSON.parse(out);
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function show(liveBox, result, withCheck) {
    liveBox.innerHTML = "";
    liveBox.appendChild(el("div", "live-label", "Your output"));
    if (result.stdout && result.stdout.trim()) liveBox.appendChild(el("pre", "live-stdout", result.stdout.replace(/\s+$/, "")));
    if (result.warnings && result.warnings.length) {
      liveBox.appendChild(el("pre", "live-stdout", "Warnings (your chart still drew):\n" + result.warnings.join("\n")));
    }
    if (result.error) liveBox.appendChild(el("pre", "live-stdout live-error", result.error));
    result.figures.forEach(function (b64, i) {
      var img = el("img", "live-figure");
      img.src = "data:image/png;base64," + b64;
      img.alt = "Chart produced by your code" + (result.figures.length > 1 ? " (" + (i + 1) + ")" : "");
      liveBox.appendChild(img);
    });
    if (!result.error && !result.figures.length && !(result.stdout || "").trim()) {
      liveBox.appendChild(el("pre", "live-stdout", "(Ran without output - did you draw a chart?)"));
    }
    if (withCheck) {
      var msg = result.check_message || (result.check_ok ? "Nice work - that meets the brief." : "Not quite yet.");
      liveBox.appendChild(el("div", "check-result " + (result.check_ok ? "ok" : "no"),
        (result.check_ok ? "✅ " : "💡 ") + msg));
    }
  }

  async function execute(box, editor, liveBox, buttons, check) {
    buttons.forEach(function (b) { b.disabled = true; });
    liveBox.innerHTML = "";
    liveBox.appendChild(el("div", "live-label", "Running..."));
    try {
      await new Promise(function (r) { setTimeout(r, 30); });  // let the UI repaint
      var result = await runCode(editor.value, check);
      show(liveBox, result, Boolean(check));
    } catch (err) {
      liveBox.innerHTML = "";
      liveBox.appendChild(el("pre", "live-stdout live-error",
        "Could not start Python in this browser: " + err.message +
        "\nTry again, or use the Colab / notebook links at the top of the lesson."));
    } finally {
      buttons.forEach(function (b) { b.disabled = false; });
    }
  }

  function wireEditor(editor, runFn) {
    editor.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); runFn(); return; }
      if (e.key === "Tab" && !e.shiftKey && !editor.dataset.escaped) {
        e.preventDefault();
        var s = editor.selectionStart, end = editor.selectionEnd;
        editor.value = editor.value.slice(0, s) + "    " + editor.value.slice(end);
        editor.selectionStart = editor.selectionEnd = s + 4;
      }
      // Esc releases Tab so keyboard users can move on.
      if (e.key === "Escape") editor.dataset.escaped = "1";
    });
    editor.addEventListener("focus", function () { delete editor.dataset.escaped; });
  }

  // Worked examples: "Edit & run" swaps the static code for an editor.
  document.querySelectorAll("[data-cell]").forEach(function (cell) {
    var btn = cell.querySelector('[data-action="edit"]');
    if (!btn) return;
    var code = JSON.parse(cell.querySelector(".cell-data").textContent).code;
    var liveBox = cell.querySelector(".cell-live");
    btn.addEventListener("click", function () {
      var editor = el("textarea", "cell-editor");
      editor.value = code;
      editor.rows = Math.max(4, Math.min(22, code.split("\n").length + 1));
      editor.spellcheck = false;
      editor.setAttribute("aria-label", "Editable copy of the example code");
      var hl = cell.querySelector(".highlight");
      hl.replaceWith(editor);
      var toolbar = cell.querySelector(".cell-toolbar");
      toolbar.innerHTML = "";
      var run = el("button", "btn-primary", "Run");
      var reset = el("button", "btn-ghost", "Reset code");
      run.type = reset.type = "button";
      toolbar.append(run, reset);
      var go = function () { execute(cell, editor, liveBox, [run, reset]); };
      run.addEventListener("click", go);
      reset.addEventListener("click", function () { editor.value = code; });
      wireEditor(editor, go);
      editor.focus();
      go();
    });
  });

  // Exercises
  document.querySelectorAll("[data-exercise]").forEach(function (box) {
    var data = JSON.parse(box.querySelector(".cell-data").textContent);
    var editor = box.querySelector(".cell-editor");
    var liveBox = box.querySelector(".cell-live");
    var buttons = Array.prototype.slice.call(box.querySelectorAll(".cell-toolbar button"));
    var key = "sbp-ex-" + box.id;
    try { var saved = localStorage.getItem(key); if (saved) editor.value = saved; } catch (e) { /* storage blocked */ }
    editor.addEventListener("input", function () {
      try { localStorage.setItem(key, editor.value); } catch (e) { /* storage blocked */ }
    });
    var check = function () { execute(box, editor, liveBox, buttons, data.check); };
    box.querySelector('[data-action="check"]').addEventListener("click", check);
    box.querySelector('[data-action="run"]').addEventListener("click", function () {
      execute(box, editor, liveBox, buttons);
    });
    box.querySelector('[data-action="reset"]').addEventListener("click", function () {
      editor.value = data.starter;
      try { localStorage.removeItem(key); } catch (e) { /* storage blocked */ }
    });
    box.querySelector('[data-action="load-solution"]').addEventListener("click", function () {
      editor.value = data.solution;
      editor.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    wireEditor(editor, check);
  });
})();
