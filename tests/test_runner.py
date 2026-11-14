"""The cell runner is shared by the build and the browser, so test it directly."""
import runner
from conftest import ROOT

runner.DATA_PATH = str(ROOT / "data" / "penguins.csv")
SETUP = "import seaborn as sns\nimport matplotlib.pyplot as plt\npenguins = sns.load_dataset('penguins')"


def test_trailing_expression_is_echoed():
    result = runner.run_cell("penguins.shape", setup=SETUP)
    assert result["error"] is None
    assert result["stdout"].strip() == "(344, 7)"


def test_plot_objects_are_not_echoed():
    result = runner.run_cell("sns.histplot(data=penguins, x='body_mass_g')", setup=SETUP)
    assert result["stdout"] == ""
    assert len(result["figures"]) == 1
    assert result["figures"][0][:8] == b"\x89PNG\r\n\x1a\n"


def test_errors_point_at_the_learners_line():
    result = runner.run_cell("x = 1\nsns.scatterplot(data=penguins, x=bad_name)", setup=SETUP)
    assert "NameError" in result["error"]
    assert 'File "<your code>", line 2' in result["error"]
    assert "x=bad_name" in result["error"]


def test_check_passes_and_fails_with_messages():
    code = "ax = sns.scatterplot(data=penguins, x='bill_length_mm', y='bill_depth_mm')"
    ok = runner.run_cell(code, setup=SETUP, check="points(chart_axes()[0])\nprint('yay')")
    assert ok["check_ok"] is True and ok["check_message"] == "yay"
    bad = runner.run_cell(code, setup=SETUP, check="assert False, 'add a title'")
    assert bad["check_ok"] is False and bad["check_message"] == "add a title"


def test_check_is_skipped_when_code_errors():
    result = runner.run_cell("raise ValueError('boom')", setup=SETUP, check="print('never')")
    assert result["check_ok"] is False
    assert "Fix the error first" in result["check_message"]


def test_warnings_are_captured():
    result = runner.run_cell("import warnings\nwarnings.warn('careful', FutureWarning)", setup=SETUP)
    assert result["warnings"] == ["FutureWarning: careful"]


def test_each_cell_starts_fresh():
    runner.run_cell("leak = 42\nsns.set_theme(context='poster')", setup=SETUP)
    result = runner.run_cell("print('leak' in dir())\nimport matplotlib as m\nprint(m.rcParams['font.size'])",
                             setup=SETUP)
    first, size = result["stdout"].split()
    assert first == "False"
    assert float(size) == 10.0  # rcParams reset between cells


def test_json_entry_point_encodes_figures():
    import json

    payload = json.loads(runner.run_cell_json("sns.histplot(data=penguins, x='body_mass_g')", SETUP))
    assert isinstance(payload["figures"][0], str)  # base64 for the browser
