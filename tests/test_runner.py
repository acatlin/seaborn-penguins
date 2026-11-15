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


def test_figures_with_randomness_are_reproducible():
    """Jitter (stripplot) and bootstrapped CIs (regplot, barplot) must not change between runs,
    so docs/img only changes when the content does."""
    for code in (
        "sns.stripplot(data=penguins, x='species', y='body_mass_g')",
        "sns.regplot(data=penguins, x='flipper_length_mm', y='body_mass_g')",
        "sns.barplot(data=penguins, x='species', y='body_mass_g')",
    ):
        first = runner.run_cell(code, setup=SETUP)["figures"][0]
        second = runner.run_cell(code, setup=SETUP)["figures"][0]
        assert first == second, code


FORMS = {
    'sns.histplot(data=penguins, x="body_mass_g", hue="species")': {"histogram"},
    'sns.histplot(data=penguins, y="body_mass_g", bins=5)': {"histogram"},
    'sns.histplot(data=penguins, x="body_mass_g", hue="species", element="step", fill=False)': {"histogram"},
    'sns.histplot(data=penguins, x="body_mass_g", element="step")': {"area"},
    'sns.kdeplot(data=penguins, x="body_mass_g", hue="species")': {"density"},
    'sns.kdeplot(data=penguins, y="bill_depth_mm", cut=0)': {"density"},
    'sns.kdeplot(data=penguins, x="body_mass_g", fill=True)': {"area"},
    'ax = sns.ecdfplot(data=penguins, x="body_mass_g", hue="species")\nax.axvline(4500)': {"ecdf"},
    'sns.boxplot(data=penguins, x="species", y="body_mass_g")': {"box"},
    'sns.boxplot(data=penguins, y="species", x="body_mass_g", hue="sex", fill=False)': {"box"},
    'sns.violinplot(data=penguins, x="species", y="body_mass_g")': {"violin"},
    'sns.stripplot(data=penguins, x="species", y="body_mass_g")': {"strip"},
    'sns.boxplot(data=penguins, x="species", y="body_mass_g")\n'
    'sns.stripplot(data=penguins, x="species", y="body_mass_g")': {"box", "strip"},
    'sns.barplot(data=penguins, x="species", y="body_mass_g")': {"bars"},
    'sns.countplot(data=penguins, y="island", hue="species")': {"bars"},
    'penguins.groupby("species")["body_mass_g"].mean().plot.bar()': {"bars"},
    'sns.pointplot(data=penguins, x="species", y="body_mass_g")': {"points", "joined"},
    'sns.pointplot(data=penguins, x="species", y="body_mass_g", hue="sex", linestyle="none")': {"points"},
    'sns.pointplot(data=penguins, x="species", y="body_mass_g", hue="species", linestyle="none")': {"points"},
    'sns.lineplot(data=penguins, x="species", y="body_mass_g")': {"joined"},
    'sns.lineplot(data=penguins, x="flipper_length_mm", y="body_mass_g")': {"line"},
    'sns.scatterplot(data=penguins, x="flipper_length_mm", y="body_mass_g", hue="species")': {"scatter"},
    'sns.regplot(data=penguins, x="flipper_length_mm", y="body_mass_g")': {"scatter", "line"},
    'sns.histplot(data=penguins, x="flipper_length_mm", y="body_mass_g")': {"mesh"},
    'sns.heatmap(penguins.select_dtypes("number").corr())': {"mesh"},
    'plt.pie(penguins["species"].value_counts())': {"pie"},
}


def test_chart_forms_names_what_is_on_the_axes():
    """Exercise 7.2 asks the learner to choose a chart form, so its check has to tell the forms
    apart from the objects each one leaves on the Axes."""
    for code, forms in FORMS.items():
        result = runner.run_cell(code, setup=SETUP, check="print(sorted(chart_forms(plt.gca())))")
        assert result["error"] is None and result["check_ok"], (code, result["error"], result["check_message"])
        assert result["check_message"] == str(sorted(forms)), code


def test_json_entry_point_encodes_figures():
    import json

    payload = json.loads(runner.run_cell_json("sns.histplot(data=penguins, x='body_mass_g')", SETUP))
    assert isinstance(payload["figures"][0], str)  # base64 for the browser
