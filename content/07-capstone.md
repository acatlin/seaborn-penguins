# Lesson 7 - Capstone: the Penguin Field Report

<p class="lede">The station chief at Palmer wants a one-page figure for the season's briefing. It should answer four questions: Who lives where? How big are they? Do males and females differ? Can you tell species apart by their bills? You'll use everything from Lessons 1-6.</p>

**By the end of this lesson you can:**

- plan a multi-panel figure from the questions it must answer
- build it panel by panel with `plt.subplots` and axes-level functions
- give a whole figure one legend, one title and a consistent color story
- review your own chart against a design checklist

```python setup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks")
penguins = sns.load_dataset("penguins")
PENGUIN_COLORS = {"Adelie": "#FF8C00", "Chinstrap": "#A034F0", "Gentoo": "#159090"}
SEX_COLORS = {"Female": "#8c8c8c", "Male": "#333333"}
```

## Step 1: questions first, charts second

| Question | Data job | Chart (lesson) |
|---|---|---|
| Who lives where? | counts by two categories | `countplot` (3) |
| How big are they? | distribution per group | step `histplot` or `kdeplot` (2) |
| Do males and females differ? | compare a mean across groups (zero not meaningful) | `pointplot` (3) |
| Can bills tell species apart? | relationship between two numbers, by group | `scatterplot` (1) |

Picking the chart *from the question* is the most important step in the whole course. If you can't name the question a panel answers, cut the panel.

Choosing a form also means ruling others out. Three forms mislead, and you have met each of them:

- **Bars for a mean when zero means nothing.** Bars start at zero, so three bill depths between 15 and 18 mm become three bars of nearly the same height (Lesson 3). Use points.
- **A line between groups that have no order.** It draws a trend from one species to the next, and there is none (Lesson 4).
- **A pie.** People compare angles poorly, and lengths and positions well (Lesson 3).

Now try it with three questions the chief did not ask. Nobody names the chart this time.

```python exercise id=7.2 title="Questions only: choose the form"
# Draw one panel for each question, in a chart form that answers it:
#   A. How are flipper lengths spread within each species?
#   B. Which species has the deepest bill on average?
#   C. Do penguins with longer flippers weigh more?
# Pass ax=axes[0], ax=axes[1] and ax=axes[2].
# The check looks at the form of each panel, and at nothing else.
fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")

# A
___

# B
___

# C
___
```

```python solution for=7.2
fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")

# A. How one measurement is spread: a distribution, one outline per species
sns.histplot(data=penguins, x="flipper_length_mm", hue="species", palette=PENGUIN_COLORS,
             element="step", fill=False, binwidth=3, ax=axes[0])
axes[0].set(xlabel="Flipper length (mm)", ylabel="Penguins",
            title="A. Gentoo flippers are the longest")
axes[0].get_legend().set_title("Species")

# B. A mean compared across groups, where zero means nothing: points, not bars,
#    and no line from one species to the next
sns.pointplot(data=penguins, x="species", y="bill_depth_mm", hue="species",
              palette=PENGUIN_COLORS, linestyle="none", legend=False, ax=axes[1])
axes[1].set(xlabel="", ylabel="Mean bill depth (mm), 95% CI",
            title="B. Adelie and Chinstrap bills are the deepest")

# C. Two measurements of the same penguin: a relationship, one point per bird
sns.scatterplot(data=penguins, x="flipper_length_mm", y="body_mass_g", hue="species",
                palette=PENGUIN_COLORS, s=18, legend=False, ax=axes[2])
axes[2].set(xlabel="Flipper length (mm)", ylabel="Body mass (g)",
            title="C. Longer flippers, heavier penguins")
sns.despine(fig=fig)
```

```python check for=7.2
axes = chart_axes()
assert len(axes) == 3, f"Draw three panels, one for each question, by passing ax=axes[0], ax=axes[1] and ax=axes[2]. I found {len(axes)} with a chart on it."
spread = {"histogram", "density", "ecdf", "area", "box", "violin", "strip"}
a, b, c = (chart_forms(ax) for ax in axes)
for panel, forms in zip("ABC", (a, b, c)):
    assert "pie" not in forms, f"Panel {panel}: a pie makes the reader compare angles. Choose a form that compares lengths or positions."

assert "joined" not in a, "Panel A: a line from one species to the next draws a trend, and species have no order. The question asks how flipper lengths are spread: draw a distribution."
assert "bars" not in a, "Panel A: one bar per species shows one number, a mean or a count. The question asks how the flipper lengths are spread, so show the whole distribution: a histogram, a density curve, an ECDF, or a box, violin or strip plot."
if not a & spread:
    assert "points" not in a, "Panel A: a point plot shows a mean and its interval, two numbers per species. The question asks how the flipper lengths are spread, so show the whole distribution: a histogram, a density curve, an ECDF, or a box, violin or strip plot."
    assert not a & {"scatter", "line", "mesh"}, "Panel A: that form relates two measurements. This question is about one, flipper length: draw its distribution for each species."
    assert False, "Panel A: I can't tell which form this is. For a question about spread I know a histogram, a density curve, an ECDF, and a box, violin or strip plot."

assert "joined" not in b, "Panel B: a line from one species to the next draws a trend, and species have no order. Keep the points and drop the line: linestyle=\"none\" in sns.pointplot."
assert "bars" not in b, "Panel B: bars start at zero, and a bill 0 mm deep means nothing. Drawn from zero, depths of 15 to 18 mm look nearly alike. Use points (sns.pointplot with linestyle=\"none\"), or show each species' spread with a box, violin or strip plot."
if not b & (spread | {"points"}):
    assert not b & {"scatter", "line", "mesh"}, "Panel B: that form relates two measurements. This question compares the species on one, bill depth: put species on one axis."
    assert False, "Panel B: I can't tell which form this is. For a mean compared across groups I know a point plot, and a box, violin or strip plot."

assert "bars" not in c, "Panel C: bars compare groups. This question relates two measurements of the same penguin, so give each an axis: a scatter plot, with a trend line if you like."
if not c & {"scatter", "line", "mesh"}:
    assert not c & {"histogram", "density", "ecdf", "area"}, "Panel C: that shows how one measurement is spread. This question relates two, flipper length and body mass, so give each an axis: a scatter plot, with a trend line if you like."
    assert not c & {"box", "violin", "strip", "points", "joined"}, "Panel C: that compares groups. This question relates two measurements of the same penguin, so give each an axis: a scatter plot, with a trend line if you like."
    assert False, "Panel C: I can't tell which form this is. For a relationship between two measurements I know a scatter plot, a trend line and a 2-D histogram."

plain = {"histogram": "a histogram", "density": "density curves", "ecdf": "ECDFs", "area": "filled outlines",
         "box": "a box plot", "violin": "a violin plot", "strip": "a strip plot", "points": "a point plot",
         "scatter": "a scatter plot", "line": "a line", "mesh": "a 2-D histogram"}
def named(forms):
    return " with ".join(plain.get(form, form) for form in sorted(forms))
print(f"Three questions, three forms that answer them. A: {named(a)}. B: {named(b)}. C: {named(c)}. I looked at the forms only. Whether the labels and titles do their job is for the pre-flight checklist in Step 4.")
```

## Step 2: lay out the canvas

```python run fig=07-canvas alt="An empty two-by-two grid of axes with panel letters A to D."
fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout="constrained")
for ax, letter in zip(axes.flat, "ABCD"):
    ax.set_title(f"Panel {letter}", loc="left")
```

`axes` is a 2×2 NumPy array. Index it as `axes[row, col]`, or flatten it with `axes.flat`.

## Step 3: fill the panels

The full report is below. Read it panel by panel. Every line is something you've already met.

```python run fig=07-report alt="Four-panel penguin field report: counts per island, body mass distributions, male versus female mass, and a bill-shape scatter, sharing one species legend and one title."
fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout="constrained")
species_order = ["Adelie", "Chinstrap", "Gentoo"]

# A. Who lives where?
ax = axes[0, 0]
sns.countplot(data=penguins, y="island", hue="species", palette=PENGUIN_COLORS,
              hue_order=species_order, order=["Biscoe", "Dream", "Torgersen"],  # busiest first
              legend=False, ax=ax)
ax.set(xlabel="Penguins counted", ylabel="",
       title="A. Gentoos only on Biscoe, Chinstraps only on Dream")

# B. How big are they?
ax = axes[0, 1]
sns.histplot(data=penguins, x="body_mass_g", hue="species", palette=PENGUIN_COLORS,
             hue_order=species_order, element="step", fill=False, linewidth=1.8,
             binwidth=200, legend=False, ax=ax)
ax.xaxis.set_major_formatter(lambda v, pos: f"{v / 1000:.1f} kg")
ax.set(xlabel="Body mass", ylabel="Penguins",
       title="B. Gentoos are more than 1.3 kg heavier on average")

# C. Do males and females differ?
ax = axes[1, 0]
sns.pointplot(data=penguins, x="species", y="body_mass_g", hue="sex",
              order=species_order, palette=SEX_COLORS,
              dodge=0.35, linestyle="none", markers=["o", "s"], ax=ax)
ax.yaxis.set_major_formatter(lambda v, pos: f"{v / 1000:.1f} kg")
ax.set(xlabel="", ylabel="Mean body mass (95% CI)",
       title="C. Males outweigh females in every species")
ax.legend(title="", frameon=False, loc="upper left")

# D. Can bills tell species apart?
ax = axes[1, 1]
sns.scatterplot(data=penguins, x="bill_length_mm", y="bill_depth_mm", hue="species",
                palette=PENGUIN_COLORS, hue_order=species_order, s=18, alpha=0.8,
                legend=False, ax=ax)
ax.set(xlabel="Bill length (mm)", ylabel="Bill depth (mm)",
       title="D. Bill shape alone nearly separates the species")

# One legend for the species colors, one title for the figure
handles = [plt.Line2D([], [], marker="o", linestyle="", color=PENGUIN_COLORS[s], label=s)
           for s in species_order]
fig.legend(handles=handles, loc="outside lower center", ncols=3, frameon=False)
fig.suptitle("Palmer Station penguins: three species, three body plans",
             fontsize=15, fontweight="bold")
sns.despine(fig=fig)
```

The design choices to notice:

- **One color story.** Species are the same three colors in every panel, so a single figure-level legend (`fig.legend`) covers A, B and D. Panel C uses `SEX_COLORS`, two grays, so the two encodings can't be confused.
- **Panel titles state findings and carry letters**, so the chief can say "look at panel C."
- **`hue_order` everywhere** keeps the species in the same order in every panel.
- **`loc="outside lower center"`** works with `layout="constrained"` and places the legend below the panels, never on the data.

## Step 4: review before you share

!!! few "Pre-flight checklist"
    1. **Question:** Can I name the question each panel answers, and is the answer visible in five seconds?
    2. **Form:** Is the chart type right for the data's job (Lesson 3's bars vs. points, Lesson 4's lines only for ordered x)?
    3. **Honesty:** Do bars start at zero? Are facet scales shared? Are error bars explained?
    4. **Color:** Is color used only where it means something, consistently, and colorblind-safe?
    5. **Ink:** Is there anything I can delete, such as a redundant legend, a heavy border, or a gridline nobody needs?
    6. **Words:** Plain-English labels with units, on axes and legends alike, and titles that state findings.

## Your turn: the sex-differences report

```python exercise id=7.1 title="Build a three-panel report on sex differences"
# Build a 1 x 3 figure (plt.subplots(1, 3, ..., layout="constrained")).
# Each panel compares Female vs Male for one measurement, split by species:
#   body_mass_g, flipper_length_mm, bill_length_mm
# Give every panel a title, and give the figure a suptitle that states the finding.
fig, axes = plt.subplots(___)

for ax, column in zip(axes, ["body_mass_g", "flipper_length_mm", "bill_length_mm"]):
    ___
```

```python solution for=7.1
fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
measures = {"body_mass_g": "Body mass (g)",
            "flipper_length_mm": "Flipper length (mm)",
            "bill_length_mm": "Bill length (mm)"}

for ax, (column, label) in zip(axes, measures.items()):
    sns.pointplot(data=penguins, x="species", y=column, hue="sex", palette=SEX_COLORS,
                  dodge=0.35, linestyle="none", markers=["o", "s"], ax=ax)
    ax.set(xlabel="", ylabel=label, title=label.split(" (")[0])
    ax.get_legend().remove()          # one figure-level legend instead of three

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="outside upper right", frameon=False)
fig.suptitle("Males are larger on every measure, in every species", fontweight="bold")
sns.despine(fig=fig)
```

```python check for=7.1
fig = plt.gcf()
axes = chart_axes()
assert len(axes) == 3, f"I expected 3 panels, found {len(axes)}."
assert type(fig.get_layout_engine()).__name__ == "ConstrainedLayoutEngine", "Create the figure with plt.subplots(1, 3, ..., layout=\"constrained\"), so titles, labels and the legend get their own room."
assert all(len(ax.get_title()) >= 4 for ax in axes), "Give every panel a title."
assert fig._suptitle is not None and len(fig._suptitle.get_text()) >= 15, "Add a fig.suptitle(...) that states the finding."
ylabels = " ".join(ax.get_ylabel().lower() for ax in axes)
for word in ["mass", "flipper", "bill"]:
    assert word in ylabels, f"I couldn't find a panel for {word} - check your y-axis labels."
assert {"Female", "Male"} <= set(legend_labels()), "Split each panel by sex (hue='sex') and keep one legend."
legends = len(fig.legends) + sum(ax.get_legend() is not None for ax in fig.axes)
assert legends == 1, f"I found {legends} legends. Keep one: remove each panel's with ax.get_legend().remove(), then add one for the whole figure with fig.legend(...)."
print("A clean, comparable three-panel report. You're ready to brief the station chief.")
```

## Final quiz

```quiz
- q: "In a multi-panel figure where every panel colors by species, where should the species legend go?"
  options:
    - "Repeated inside every panel, so each panel stands alone"
    - "Nowhere - readers can infer the colors from the data"
    - "In the first panel only, since readers start reading at the top left"
    - "Once, at figure level (or as direct labels)"
  answer: D
  explain: "Repeating legends is non-data ink. A single `fig.legend(...)` or direct labels do the job once."
- q: "What does `layout=\"constrained\"` do in `plt.subplots`?"
  options:
    - "It forces all panels to share the same x and y limits, like `sharex=True`"
    - "It makes room automatically so titles, labels and legends don't overlap"
    - "It limits the figure to at most four panels"
    - "It converts the figure to a vector format when saved"
  answer: B
  explain: "Constrained layout makes room for decorations automatically - use it for every multi-panel figure."
- q: "\"How is body mass distributed within each species?\" Which chart answers this best?"
  options:
    - "A pie chart of total body mass per species"
    - "A line chart connecting species means"
    - "Step histograms (or ECDFs) of body mass, one per species"
    - "A correlation heatmap of all numeric columns, one cell per pair"
  answer: C
  explain: "A distribution question needs a distribution chart: histogram, KDE, ECDF, or box/strip."
- q: "According to the pre-flight checklist, what should you confirm first before sharing a chart?"
  options:
    - "That it clearly answers a question at a glance"
    - "That every panel uses a different chart type, for variety"
    - "That every data point is labeled with its value"
    - "That the colors match the organization's branding"
  answer: A
  explain: "Form, color and polish all serve the question. If the question isn't clear, no styling will save the chart."
```

## Where to next?

- **seaborn's objects interface** (`seaborn.objects as so`): a newer, composable API that's worth exploring once these functions feel natural.
- **Interactive charts:** Plotly or Altair, when readers need to hover, zoom or filter.
- **Read more:** Stephen Few, *Show Me the Numbers*. Claus Wilke, *Fundamentals of Data Visualization* (free online). The [seaborn tutorial](https://seaborn.pydata.org/tutorial.html) and [gallery](https://seaborn.pydata.org/examples/index.html).
- **Practice:** make your own field report from another seaborn dataset, such as `sns.load_dataset("tips")`, `"mpg"` or `"taxis"`.

!!! note "Course takeaways"
    - Start from the **question**, pick the **form**, then polish.
    - Tidy DataFrame in, column names to channels: `x`, `y`, `hue`, `col`, `row`.
    - Axes-level functions + `plt.subplots` for custom layouts. Figure-level functions for quick small multiples.
    - Honest scales, purposeful color, direct labels, plain words.
