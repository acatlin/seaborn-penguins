# Lesson 5 - Small multiples with figure-level functions

<p class="lede">When one chart gets crowded, don't cram in more colors. Split it into a grid of small charts that share the same axes. Seaborn's figure-level functions do this in one argument.</p>

**By the end of this lesson you can:**

- tell axes-level functions from figure-level ones, and pick the right one
- split any chart into panels with `col=`, `row=` and `col_wrap=`
- size and label a grid (`height`, `aspect`, `set_axis_labels`, `set_titles`)
- explain why shared axes are the default and when to keep them

```python setup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks")
penguins = sns.load_dataset("penguins")
PENGUIN_COLORS = {"Adelie": "#FF8C00", "Chinstrap": "#A034F0", "Gentoo": "#159090"}
SEX_COLORS = {"Female": "#8c8c8c", "Male": "#333333"}
```

## Two kinds of seaborn function

| Family | Axes-level (draws on one `ax`) | Figure-level (makes a whole grid) |
|---|---|---|
| Relationships | `scatterplot`, `lineplot` | `relplot(kind="scatter" / "line")` |
| Distributions | `histplot`, `kdeplot`, `ecdfplot` | `displot(kind="hist" / "kde" / "ecdf")` |
| Categories | `boxplot`, `barplot`, `stripplot`, ... | `catplot(kind="box" / "bar" / "strip" / ...)` |
| Regression | `regplot` | `lmplot` |

**Axes-level** functions take `ax=` and return an `Axes`. Use them when *you* build the layout with matplotlib (Lessons 6 and 7). **Figure-level** functions create their own figure, accept `col=` and `row=`, and return a **`FacetGrid`**. You size them with `height=` (inches per panel) and `aspect=` (width ÷ height), not `figsize`.

## One panel per island

```python run fig=05-relplot-col alt="Three scatter panels of flipper length versus body mass, one per island, colored by species, sharing the same axes."
g = sns.relplot(data=penguins, x="flipper_length_mm", y="body_mass_g",
                hue="species", palette=PENGUIN_COLORS,
                col="island", height=3.4, aspect=0.9)
g.set_axis_labels("Flipper length (mm)", "Body mass (g)")
g.set_titles("{col_name}")
```

One argument, `col="island"`, gave three aligned panels. `set_titles("{col_name}")` swaps the default "island = Biscoe" titles for just the name. Because the axes are **shared**, you can compare positions across panels directly. The Biscoe giants are Gentoos, and Torgersen is all Adelie.

## Rows *and* columns

```python run fig=05-displot-grid alt="Grid of six histograms of body mass: rows for female and male, columns for each species; males are heavier in every species."
g = sns.displot(data=penguins, x="body_mass_g", col="species", row="sex",
                hue="species", palette=PENGUIN_COLORS, legend=False,
                binwidth=200, height=2.4, aspect=1.3)
g.set_axis_labels("Body mass (g)", "Penguins")
g.set_titles("{col_name} · {row_name}")
```

Each row is a sex and each column a species, giving six histograms on identical scales. Reading down a column compares females with males. Reading across compares species. Penguins with missing `sex` simply don't appear.

## Categorical grids with `catplot`

```python run fig=05-catplot alt="Three box-plot panels, one per species, comparing body mass of female and male penguins; males are heavier in each."
g = sns.catplot(data=penguins, x="sex", y="body_mass_g", col="species",
                kind="box", hue="sex", palette=SEX_COLORS,
                legend=False, height=3.4, aspect=0.8)
g.set_axis_labels("", "Body mass (g)")
g.set_titles("{col_name}")
g.figure.suptitle("Males are heavier in every species", y=1.04)
```

`g.figure` is the underlying matplotlib `Figure`, so `suptitle` adds a title over the whole grid. `y=1.04` nudges it up, clear of the panel titles. The x-axis already names each sex, so `legend=False` drops a legend that would only repeat it.

!!! few "Small multiples beat a crowded chart"
    Edward Tufte and Stephen Few both champion **small multiples**: the same chart repeated for each subset, on the same scales. The eye learns the design once, then spends its effort on the differences. If a single chart needs more than about four colors, or its lines tangle, facet it.

## Shared axes: keep them (usually)

Figure-level functions share x and y across panels by default. That's what makes panel-to-panel comparison honest. Unsharing (`facet_kws={"sharey": False}`) lets each panel zoom in on its own range, but then equal heights no longer mean equal values. Only do it when the panels are *not* meant to be compared, and say so.

## Wrapping a long row

With many panels, `col_wrap=` wraps them into rows:

```python run fig=05-colwrap alt="Four histogram panels of flipper length by island-and-sex combinations wrapped into two rows."
subset = penguins.dropna(subset=["sex"]).assign(
    group=lambda d: d["island"] + " · " + d["sex"])
subset = subset[subset["island"].isin(["Biscoe", "Dream"])]
g = sns.displot(data=subset, x="flipper_length_mm", col="group", col_wrap=2,
                hue="species", palette=PENGUIN_COLORS, element="step",
                fill=False, binwidth=4, height=2.4, aspect=1.4)
g.set_axis_labels("Flipper length (mm)", "Penguins")
g.set_titles("{col_name}")
```

## Custom panels with `FacetGrid`

Under the hood, every figure-level function builds a `FacetGrid`. You can build one directly and map any plotting function onto it:

```python run fig=05-facetgrid alt="Three panels by species, each a scatter of bill length versus bill depth with female and male penguins in different grays."
g = sns.FacetGrid(penguins, col="species", hue="sex", palette=SEX_COLORS, height=3.2)
g.map_dataframe(sns.scatterplot, x="bill_length_mm", y="bill_depth_mm", s=18)
g.add_legend(title="")
g.set_axis_labels("Bill length (mm)", "Bill depth (mm)")
g.set_titles("{col_name}")
```

## Your turn

```python exercise id=5.1 title="A six-panel flipper report"
# Use displot to draw flipper_length_mm histograms with one COLUMN per
# species and one ROW per sex. Color by species with PENGUIN_COLORS,
# hide the legend (the column titles already name species), and set
# plain-English axis labels.
g = sns.displot(data=penguins, x="flipper_length_mm")
```

```python solution for=5.1
g = sns.displot(data=penguins, x="flipper_length_mm", col="species", row="sex",
                hue="species", palette=PENGUIN_COLORS, legend=False,
                binwidth=3, height=2.4, aspect=1.3)
g.set_axis_labels("Flipper length (mm)", "Penguins")
g.set_titles("{col_name} · {row_name}")
```

```python check for=5.1
axes = chart_axes()
assert len(axes) == 6, f"I expected 6 panels (3 species x 2 sexes) but found {len(axes)}. Use col= and row=."
xlims = {tuple(round(v) for v in ax.get_xlim()) for ax in axes}
assert len(xlims) == 1, "Keep the x-axes shared so the panels are comparable."
assert not legend_labels(), "Drop the legend with legend=False - the panel titles already name the species."
assert near_color(PENGUIN_COLORS["Chinstrap"], set().union(*[colors_used(a) for a in axes]), tol=0.1), "Color by species: hue='species', palette=PENGUIN_COLORS."
assert any("mm" in ax.get_xlabel() for ax in axes), "Label the x-axis with units, e.g. g.set_axis_labels('Flipper length (mm)', 'Penguins')."
print("Six aligned panels on shared scales: species differences dominate, and males run longer in each.")
```

```python exercise id=5.2 title="Clean panel titles"
# Draw a relplot of bill_length_mm (x) vs bill_depth_mm (y), one column
# per species, colored by sex. Make each panel title JUST the species
# name (e.g. "Gentoo"), and add a figure title with g.figure.suptitle.
g = sns.relplot(data=penguins, x="bill_length_mm", y="bill_depth_mm", col="species")
```

```python solution for=5.2
g = sns.relplot(data=penguins, x="bill_length_mm", y="bill_depth_mm",
                col="species", hue="sex", palette=SEX_COLORS, height=3.2)
g.set_axis_labels("Bill length (mm)", "Bill depth (mm)")
g.set_titles("{col_name}")
g.figure.suptitle("Males have bigger bills in every species", y=1.04)
```

```python check for=5.2
axes = chart_axes()
assert len(axes) == 3, "Make one column per species with col='species'."
titles = sorted(ax.get_title() for ax in axes)
assert titles == ["Adelie", "Chinstrap", "Gentoo"], f"Panel titles are {titles}; use g.set_titles('{{col_name}}')."
assert {"Female", "Male"} <= set(legend_labels()), "Color the points by sex with hue='sex'."
sup = plt.gcf()._suptitle
assert sup is not None and len(sup.get_text()) >= 10, "Add a figure title with g.figure.suptitle(...)."
print("Clean titles, shared axes, one message on top.")
```

## Quick quiz

```quiz
- q: "Which figure-level function is the counterpart of `sns.histplot`?"
  options:
    - "`sns.catplot`"
    - "`sns.displot`"
    - "`sns.relplot`"
    - "`sns.FacetGrid`"
  answer: B
  explain: "`displot` covers the distribution family: `kind=\"hist\"` (default), `\"kde\"` and `\"ecdf\"`. `FacetGrid` is the class every figure-level function builds on, not a counterpart of `histplot`."
- q: "What do figure-level functions such as `relplot` return?"
  options:
    - "A single matplotlib `Axes`, just like `scatterplot` returns"
    - "A pandas DataFrame of the aggregated values for each panel"
    - "A list of PNG images, one for each panel in the grid"
    - "A grid object (e.g. `FacetGrid`) managing the figure"
  answer: D
  explain: "The grid object exposes `.figure`, `.axes`, and helpers like `set_axis_labels` and `set_titles`."
- q: "Why do facets share their axes by default?"
  options:
    - "So equal positions mean equal values across panels"
    - "Because matplotlib cannot draw different scales in one figure"
    - "To save memory when there are many panels"
    - "So the legend can be drawn only once"
  answer: A
  explain: "Shared scales are what make small multiples work. Unshare only when panels aren't meant to be compared - and tell the reader."
- q: "How do you set the size of a `relplot` figure?"
  options:
    - "Pass `figsize=(10, 4)` to `relplot`"
    - "Call `plt.figure(figsize=(10, 4))` immediately before calling `relplot`"
    - "Use `height=` (inches per panel) and `aspect=` (width/height)"
    - "Increase the `dpi=` argument until it looks right"
  answer: C
  explain: "Figure-level functions create their own figure, so a `plt.figure` call beforehand only leaves an empty figure behind. Size is set per panel with `height` and `aspect`."
```

!!! note "Key takeaways"
    - Axes-level functions take `ax=`. Figure-level functions (`relplot`, `displot`, `catplot`, `lmplot`) build a grid and return it.
    - Facet with `col=`, `row=`, `col_wrap=`. Size with `height=` and `aspect=`.
    - Tidy the grid with `set_axis_labels`, `set_titles("{col_name}")`, and `g.figure.suptitle`.
    - Small multiples on shared axes beat one overloaded chart.
