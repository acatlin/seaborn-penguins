# Seaborn with Penguins

<p class="lede">A hands-on course in making clear, honest, good-looking charts with <strong>seaborn</strong> and <strong>matplotlib</strong>. Seven short lessons use one friendly dataset. Every example runs live in your browser.</p>

![The Penguin Field Report you'll build in Lesson 7: four panels on island counts, body-mass distributions, male versus female mass, and bill shape.](img/07-report.png)

*The figure you'll build in Lesson 7. Every technique in it is taught along the way.*

## Who this is for

You're comfortable with Python basics and **pandas** (`read_csv`, selecting columns, `groupby`, filtering rows), and you want to make charts that are both quick to produce and good enough to show other people. You don't need any prior matplotlib or seaborn.

## The lessons

<div class="cards" markdown="0">
  <a class="card" href="01-first-plot.html"><strong>1 · Your first plot</strong><span>The grammar of seaborn, hue, labels, and a paradox hiding in the bills.</span></a>
  <a class="card" href="02-distributions.html"><strong>2 · Distributions</strong><span>Histograms, KDEs and ECDFs. How heavy is a penguin?</span></a>
  <a class="card" href="03-categories.html"><strong>3 · Comparing categories</strong><span>Counts, bars, boxes, violins, strips and points, done honestly.</span></a>
  <a class="card" href="04-relationships.html"><strong>4 · Relationships</strong><span>Trend lines, line charts, correlation heatmaps and pair plots.</span></a>
  <a class="card" href="05-small-multiples.html"><strong>5 · Small multiples</strong><span>Figure-level functions and facet grids.</span></a>
  <a class="card" href="06-polish.html"><strong>6 · Polish with matplotlib</strong><span>Themes, palettes, highlights, annotations and a full makeover.</span></a>
  <a class="card" href="07-capstone.html"><strong>7 · Capstone</strong><span>Plan and build a multi-panel Penguin Field Report.</span></a>
</div>

Each lesson takes about **45-75 minutes** and has the same rhythm. Worked examples come first, then a **design principle** callout, then graded **exercises** with solutions, then a short **quiz**.

## Meet the data: Palmer penguins

Between 2007 and 2009, Dr. Kristen Gorman and the Palmer Station Long Term Ecological Research program measured 344 penguins on three islands in the Palmer Archipelago, Antarctica. Allison Horst, Alison Hill and Kristen Gorman released the data as the friendly alternative to the overused iris dataset. It ships with seaborn:

```python
import seaborn as sns
penguins = sns.load_dataset("penguins")
```

| Column | Meaning | Type |
|---|---|---|
| `species` | Adelie, Chinstrap or Gentoo | category |
| `island` | Biscoe, Dream or Torgersen | category |
| `bill_length_mm` | length of the bill (culmen) | number |
| `bill_depth_mm` | depth (height) of the bill | number |
| `flipper_length_mm` | flipper length | number |
| `body_mass_g` | body mass in grams | number |
| `sex` | Female or Male (11 missing) | category |

It's small enough to see every point, but it's real data. It has missing values, three groups with different body plans, and a genuine statistical paradox waiting in Lesson 1.

## Three ways to follow along

1. **Right here in the browser (no install).** Click **Run** or **Edit & run** on any code cell. The first run downloads a Python runtime (Pyodide, about 30 MB) into your browser, which takes 10-30 seconds. After that, cells run in a second or two. Your exercise code is saved in this browser.
2. **Google Colab.** Each lesson has an **Open in Colab** link at the top, plus a solutions notebook.
3. **Your own machine.** Download the notebooks and install the libraries:

```bash
pip install "seaborn==0.13.2" "matplotlib>=3.8" "pandas>=2.0" jupyterlab
```

The code targets **seaborn 0.13**. Older versions use different names for some arguments (for example `ci=` instead of `errorbar=`).

> **Tip:** In a script (not a notebook), finish with `plt.show()` to open the chart window. Notebooks and this site display charts automatically.

## The design thread

Seaborn makes charts *quickly*. This course is just as concerned with making them *well*. Each lesson includes a **design principle** callout, drawn mostly from Stephen Few's *Show Me the Numbers* and from Edward Tufte. The core ideas:

- Start from the **question**, and choose the chart form that answers it.
- Encode the important comparison with **position or length** on a common scale.
- Use **color only when it means something**, the same way every time, and safe for colorblind readers.
- Remove ink that isn't data. **Label directly.** Write titles that **state the finding**.

Ready? Start with **[Lesson 1 - Your first plot](01-first-plot.html)**.

<small>Teaching this material? See the [instructor guide](instructor-guide.html).</small>
