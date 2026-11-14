# Lesson 4 - Relationships: trends, lines and correlations

<p class="lede">Do bigger flippers mean heavier penguins? How tightly do all the measurements move together? This lesson adds trend lines, line charts, correlation heatmaps and the "everything at once" pair plot to your toolkit.</p>

**By the end of this lesson you can:**

- add a fitted trend with `regplot` / `lmplot` and explain its shaded band
- use `lineplot` only where connecting the dots is meaningful
- build a correlation heatmap with a diverging palette centered on zero
- scan every pairwise relationship at once with `pairplot`

```python setup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks")
penguins = sns.load_dataset("penguins")
PENGUIN_COLORS = {"Adelie": "#FF8C00", "Chinstrap": "#A034F0", "Gentoo": "#159090"}
SEX_COLORS = {"Female": "#8c8c8c", "Male": "#333333"}
```

## A trend line with `regplot`

```python run fig=04-regplot alt="Scatter of flipper length versus body mass with a fitted straight line and a narrow shaded confidence band."
ax = sns.regplot(data=penguins, x="flipper_length_mm", y="body_mass_g",
                 scatter_kws={"alpha": 0.4, "s": 15}, line_kws={"color": "black"})
ax.set(xlabel="Flipper length (mm)", ylabel="Body mass (g)",
       title="Each extra mm of flipper adds about 50 g")
```

`regplot` fits a straight line by least squares and shades a **95% confidence interval for the line**. That band shows where the *average* trend plausibly lies, not where individual penguins fall. Notice how much narrower it is than the cloud of points.

!!! warning "A fitted line is a model, not the data"
    `regplot` draws a straight line through anything, even curved or clustered data. Look at the points first. Then ask whether a single line is honest, or whether groups need their own lines.

## One line per group with `lmplot`

`lmplot` is the figure-level sibling of `regplot` (more on figure-level functions in Lesson 5). It understands `hue`, so you get one fit per species:

```python run fig=04-lmplot alt="Bill length versus bill depth with a separate upward-sloping regression line for each species."
g = sns.lmplot(data=penguins, x="bill_length_mm", y="bill_depth_mm",
               hue="species", palette=PENGUIN_COLORS, height=4.5, aspect=1.3,
               scatter_kws={"alpha": 0.5, "s": 15})
g.set_axis_labels("Bill length (mm)", "Bill depth (mm)")
g.legend.set_title("Species")
```

`lmplot` returns a grid object, not an `Axes`, so the labels go through the grid: `g.set_axis_labels(...)` for the axes and `g.legend` for the legend.

## The paradox, in one picture

Remember Lesson 1's bill paradox? Draw the overall fit and the per-species fits on the same Axes and it jumps out:

```python run fig=04-paradox alt="Gray dashed line sloping down for all penguins combined, with three colored lines sloping up for each species: Simpson's paradox."
ax = sns.regplot(data=penguins, x="bill_length_mm", y="bill_depth_mm", scatter=False, ci=None,
                 line_kws={"color": "gray", "linestyle": "--"}, label="All penguins")
for species, group in penguins.groupby("species"):
    sns.regplot(data=group, x="bill_length_mm", y="bill_depth_mm", ax=ax, ci=None,
                color=PENGUIN_COLORS[species], label=species, scatter_kws={"s": 12, "alpha": 0.4})
ax.legend(frameon=False)
ax.set(xlabel="Bill length (mm)", ylabel="Bill depth (mm)",
       title="Overall trend: down. Within every species: up.")
```

Two useful patterns here: calling seaborn several times on the **same `ax`**, and looping over `groupby` to control each group exactly.

## Line charts: only when the x-axis has an order

A line says "follow me from left to right." That only makes sense when x is ordered: time, a dose, or a binned measurement. Penguins weren't measured over time here, but flipper length is ordered. Bin it and plot the average mass per bin:

```python run fig=04-line alt="Line chart of mean body mass by 5 mm flipper-length bin for each species, with shaded confidence bands; all three climb, with wobbly ends where a bin holds only one or two penguins."
binned = penguins.assign(flipper_bin=(penguins["flipper_length_mm"] // 5) * 5)
ax = sns.lineplot(data=binned, x="flipper_bin", y="body_mass_g",
                  hue="species", palette=PENGUIN_COLORS, marker="o")
ax.set(xlabel="Flipper length, 5 mm bins", ylabel="Mean body mass (g)",
       title="Within each species, mass climbs with flipper length")
ax.get_legend().set_title("Species")
```

`lineplot` aggregates repeated x values (here, several penguins per bin) to a mean, and shades a 95% CI band. Pass `errorbar=None` to drop the band, or `errorbar="sd"` to show spread. Notice the ragged ends: the extreme bins hold only one or two penguins, so their means jump around and the band vanishes where there is a single bird. Small groups deserve a caveat in the caption, or a minimum count before you plot them.

!!! few "Don't connect unordered categories"
    Lines between "Biscoe", "Dream" and "Torgersen" would suggest a path through islands. No such path exists. For nominal categories, use bars or dots.

## Correlation heatmaps

A correlation matrix gives a single number for every pair of numeric columns. A heatmap makes it scannable:

```python run fig=04-heatmap alt="Lower-triangle heatmap of correlations between four penguin measurements; flipper length and body mass are most strongly correlated at 0.87."
nice = {"bill_length_mm": "Bill length", "bill_depth_mm": "Bill depth",
        "flipper_length_mm": "Flipper length", "body_mass_g": "Body mass"}
corr = penguins.select_dtypes("number").rename(columns=nice).corr()
lower = corr.iloc[1:, :-1]                                  # drop the always-empty row and column
mask = np.triu(np.ones_like(lower, dtype=bool), k=1)       # hide the mirror-image upper half

ax = sns.heatmap(lower, mask=mask, annot=True, fmt=".2f", cmap="vlag",
                 center=0, vmin=-1, vmax=1, square=True, linewidths=2,
                 cbar_kws={"shrink": 0.7, "label": "Pearson r"})
ax.set(title="Flipper length and body mass move together (r = 0.87)")
```

The settings that make this honest:

- **`cmap="vlag"` with `center=0`.** This is a *diverging* palette. Blue means negative, red means positive, and near-white means "no relationship." A rainbow palette would give zero a random hue.
- **`vmin=-1, vmax=1`.** Colors mean the same thing on every heatmap you make.
- **`annot=True`.** Color gives the pattern and the printed numbers give exact values.
- **`mask` and the slice.** A correlation matrix is symmetric and its diagonal is always 1, so show each pair once and skip the rest.

Bill depth correlates *negatively* with mass overall (−0.47). By now you can probably guess why that's misleading.

## Everything at once: `pairplot`

```python run fig=04-pairplot alt="Corner pair plot: scatter plots for every pair of the four measurements and density curves on the diagonal, colored by species."
g = sns.pairplot(penguins, hue="species", palette=PENGUIN_COLORS,
                 corner=True, height=2, plot_kws={"s": 12, "alpha": 0.6})
```

A pair plot is an **exploration** tool. It's great for your first ten minutes with a dataset, but too dense for a presentation. That's why this one keeps the raw column names: it's for your eyes, not an audience's. Notice how clearly the three species separate on the bill length panels.

## Your turn

```python exercise id=4.1 title="Correlations within Gentoos only"
# Filter to Gentoo penguins, compute the correlation matrix of the
# numeric columns, and draw it as a heatmap with annotations,
# cmap="vlag", centered on 0, with vmin=-1 and vmax=1.
gentoo = ___
corr = ___
ax = sns.heatmap(corr)
```

```python solution for=4.1
gentoo = penguins[penguins["species"] == "Gentoo"]
corr = gentoo.select_dtypes("number").corr()
ax = sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag",
                 center=0, vmin=-1, vmax=1, square=True)
ax.set(title="Within Gentoos, every measurement correlates positively")
```

```python check for=4.1
ax = plt.gcf().axes[0]
mesh = [c for c in ax.collections if type(c).__name__ == "QuadMesh"]
assert mesh, "Draw the matrix with sns.heatmap."
lo, hi = mesh[0].get_clim()
assert (round(lo, 2), round(hi, 2)) == (-1, 1), "Fix the color scale with vmin=-1, vmax=1."
cmap = mesh[0].get_cmap()
low, mid, high = cmap(0.0), cmap(0.5), cmap(1.0)
assert low[2] > low[0] and high[0] > high[2] and sum(mid[:3]) > 2.4, "Use the diverging palette cmap='vlag' (blue = negative, red = positive)."
values = [float(t.get_text()) for t in ax.texts if t.get_text().strip()]
assert len(values) >= 6, "Print the numbers in the cells with annot=True."
assert min(values) > 0, "Those correlations don't look Gentoo-only - did you filter the rows?"
print("Every pair is positive within Gentoos - the negative overall correlations came from mixing species.")
```

```python exercise id=4.2 title="Deeper bills, heavier birds?"
# Use lmplot to fit body_mass_g (y) against bill_depth_mm (x),
# with one colored fit per species (PENGUIN_COLORS) and labeled axes.
g = sns.lmplot(data=penguins, x="bill_depth_mm", y="body_mass_g")
```

```python solution for=4.2
g = sns.lmplot(data=penguins, x="bill_depth_mm", y="body_mass_g",
               hue="species", palette=PENGUIN_COLORS, height=4.5, aspect=1.3)
g.set_axis_labels("Bill depth (mm)", "Body mass (g)")
g.legend.set_title("Species")
```

```python check for=4.2
ax = chart_axes()[0]
assert {"Adelie", "Chinstrap", "Gentoo"} <= set(legend_labels()), "Fit one line per species with hue='species'."
assert len(ax.lines) >= 3, "I expected three regression lines."
assert near_color(PENGUIN_COLORS["Gentoo"], colors_used(ax)), "Use palette=PENGUIN_COLORS."
xlabel, ylabel = ax.get_xlabel(), ax.get_ylabel()
assert "mm" in xlabel and ylabel.strip() and "_" not in xlabel + ylabel, "Label both axes in plain English with units: g.set_axis_labels(...)."
print("Three upward slopes - within species, deeper bills do go with heavier birds.")
```

## Quick quiz

```quiz
- q: "When is a line chart (`lineplot`) the right choice?"
  options:
    - "When x has a natural order, such as time or binned measurements"
    - "Whenever there are more than about ten categories on the x-axis"
    - "When you want to compare islands, species, or other named groups"
    - "When the y values are percentages that add up to 100"
  answer: A
  explain: "A line implies continuity from one x to the next. That only means something if x is ordered."
- q: "Why use a diverging palette such as `vlag` with `center=0` for a correlation heatmap?"
  options:
    - "Diverging palettes print more clearly in black and white"
    - "It makes the strongest correlation stand out in bright yellow"
    - "Zero becomes a neutral color, and the sign is shown by hue"
    - "A sequential palette would clip every negative correlation to its lowest color"
  answer: C
  explain: "Correlations have a meaningful midpoint (0) and two directions. Diverging palettes encode exactly that."
- q: "What does the shaded band around a `regplot` line show by default?"
  options:
    - "The range that contains 95% of the individual penguins in the data"
    - "A 95% confidence interval for the fitted regression line"
    - "One standard deviation above and below each point"
    - "The region where the data were interpolated"
  answer: B
  explain: "It's uncertainty about the line (the mean trend), which is why it's much narrower than the scatter of points."
- q: "What does `corner=True` do in `sns.pairplot`?"
  options:
    - "It moves the legend into the bottom-right corner of the figure"
    - "It only plots the first and last variables"
    - "It rounds the corners of each panel for a softer look"
    - "It drops the redundant mirror-image upper triangle"
  answer: D
  explain: "Every off-diagonal panel above the diagonal is a mirror of one below; `corner=True` hides them."
```

!!! note "Key takeaways"
    - `regplot`/`lmplot` add a fitted line plus a confidence band for the **line**. Use `hue` (in `lmplot`) or a `groupby` loop for per-group fits.
    - Only connect points with `lineplot` when x is ordered.
    - Correlation heatmaps: diverging palette, `center=0`, fixed `vmin`/`vmax`, annotate, mask the mirror half.
    - `pairplot` is for exploring, not presenting.
