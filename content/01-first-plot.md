# Lesson 1 - Your first plot: the grammar of seaborn

<p class="lede">Seaborn has one big idea: you hand it a DataFrame, then tell it which column goes on which visual channel. Learn that idea and the rest of the library follows.</p>

**By the end of this lesson you can:**

- describe seaborn's "columns → visual channels" grammar
- draw a scatter plot and color it by a category with `hue`
- label a chart properly through the matplotlib `Axes` that seaborn returns
- spot a hidden grouping variable that flips a trend (Simpson's paradox)

Every page starts with the same setup cell. The in-browser editors run it for you before each cell. In your own notebook, run it once at the top.

```python setup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks")
penguins = sns.load_dataset("penguins")

# Fixed colors, reused on every chart in this course: one per species, and two
# grays for sex so that the species colors never mean anything else
PENGUIN_COLORS = {"Adelie": "#FF8C00", "Chinstrap": "#A034F0", "Gentoo": "#159090"}
SEX_COLORS = {"Female": "#8c8c8c", "Male": "#333333"}
```

## Meet the penguins

Each row is one penguin measured near Palmer Station, Antarctica.

```python run
penguins.head()
```

A few numbers are missing (`NaN`). Seaborn quietly drops missing values for each plot, so we can leave them in.

```python run
penguins.isna().sum()
```

## The one idea behind seaborn

Seaborn wants **tidy** data: one row per observation, one column per variable. You don't loop over rows or build lists of coordinates. You *name columns*, and seaborn maps each one to a visual channel:

| Argument | Visual channel | Typical column |
|---|---|---|
| `x`, `y` | position | numbers, or categories for bar/box charts |
| `hue` | color | a category (species), or a number |
| `style` | marker shape / line dash | a category with few levels |
| `size` | marker size / line width | a number |

## A first scatter plot

```python run fig=01-scatter-basic alt="Scatter plot of flipper length versus body mass for 342 penguins, showing a strong upward trend."
sns.scatterplot(data=penguins, x="flipper_length_mm", y="body_mass_g")
```

That's a real chart in one line. Seaborn picked the axis labels from the column names, chose sensible limits, and dropped the two penguins with missing measurements.

> **Tip:** Click **Edit & run** under any example to open it in a live editor. Change a column name and run it again. The first run downloads Python into your browser and takes a little while.

## Add a third variable with `hue`

```python run fig=01-scatter-hue alt="The same scatter plot with points colored by species: Gentoo penguins form a separate cluster of long-flippered, heavy birds."
sns.scatterplot(
    data=penguins,
    x="flipper_length_mm",
    y="body_mass_g",
    hue="species",
    palette=PENGUIN_COLORS,
)
```

`hue` mapped species to color and added a legend. Passing `palette=` a **dictionary** pins each species to its own color. That matters more than it sounds.

!!! few "Color follows the thing, not its position"
    If Gentoo is teal on one chart, it should be teal on every chart. Readers learn your color code once, then reuse it. A dict palette guarantees this even when a filter drops a species. A list of colors would be handed out by position and could repaint the survivors.

## Labels are part of the chart

Every "axes-level" seaborn function (`scatterplot`, `histplot`, `boxplot`, ...) draws onto a matplotlib **Axes** and returns it. Keep that object and you can finish the chart with matplotlib:

```python run fig=01-scatter-labeled alt="Labeled scatter plot titled 'Longer flippers, heavier penguins' with axis labels including units and a legend titled Species."
ax = sns.scatterplot(
    data=penguins,
    x="flipper_length_mm",
    y="body_mass_g",
    hue="species",
    palette=PENGUIN_COLORS,
)
ax.set(
    xlabel="Flipper length (mm)",
    ylabel="Body mass (g)",
    title="Longer flippers, heavier penguins",
)
ax.get_legend().set_title("Species")
```

The legend's title is a label too. Seaborn copies it from the column name, so the last line rewrites it in the same plain English as the axes.

!!! few "A title should state the finding"
    "Flipper length vs body mass" just names the axes, which the reader can already see. "Longer flippers, heavier penguins" tells them what to notice. Always include **units** in axis labels: raw names like `body_mass_g` read as code, not English.

## Plot twist: the paradox in the bills

Do penguins with longer bills have shallower bills? Look at all of them together:

```python run fig=01-bills-overall alt="Scatter of bill length versus bill depth for all penguins in one color; the cloud slopes slightly downward."
ax = sns.scatterplot(data=penguins, x="bill_length_mm", y="bill_depth_mm", color="gray")
ax.set(xlabel="Bill length (mm)", ylabel="Bill depth (mm)",
       title="All penguins: longer bills look shallower?")
```

The cloud slopes *down*. Now ask seaborn to split it by species:

```python run fig=01-bills-species alt="The same bill scatter colored by species: within each of the three species, longer bills are deeper - the trend reverses."
ax = sns.scatterplot(
    data=penguins,
    x="bill_length_mm",
    y="bill_depth_mm",
    hue="species",
    palette=PENGUIN_COLORS,
)
ax.set(xlabel="Bill length (mm)", ylabel="Bill depth (mm)",
       title="Within every species, longer bills are deeper")
ax.get_legend().set_title("Species")
```

Within **each** species the trend goes *up*. The downward slope came from mixing groups: Gentoos have long but shallow bills, Adelies short but deep ones. This is **Simpson's paradox**, and one `hue=` argument exposed it. Whenever you see a trend, ask: *what grouping might be hiding in here?*

## More channels: `style` and `size`

```python run fig=01-scatter-style alt="Bill scatter colored by species with circle markers for male and cross markers for female penguins; within each species the male markers sit up and to the right."
ax = sns.scatterplot(
    data=penguins,
    x="bill_length_mm",
    y="bill_depth_mm",
    hue="species",
    palette=PENGUIN_COLORS,
    style="sex",
)
ax.set(xlabel="Bill length (mm)", ylabel="Bill depth (mm)")
sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))  # park the legend outside the data
```

Within each species, the males (circles) sit up and to the right. They have bigger bills. Seaborn hands out markers, and colors, in the order the categories first appear in the data. The first penguin in the table is male, so males got the circle. Pass `hue_order=` or `style_order=` when you want to fix that order yourself. `sns.move_legend` moved the now-crowded legend off the data. Use these extra channels sparingly. Each one adds a block to the legend that the reader must decode (seaborn heads each block with the raw column name), and shape is much weaker than position or color.

## Your turn

Replace each `___` with real code, then press **Run & check**. The checker inspects your chart and gives hints. Your edits are saved in this browser.

```python exercise id=1.1 title="Do long bills come with long flippers?"
# Plot bill length (x) against flipper length (y),
# colored by species with PENGUIN_COLORS, with labeled axes (include units!).
ax = sns.scatterplot(
    data=penguins,
    x=___,
    y=___,
    hue=___,
    palette=PENGUIN_COLORS,
)
ax.set(xlabel=___, ylabel=___)
```

```python solution for=1.1
ax = sns.scatterplot(
    data=penguins,
    x="bill_length_mm",
    y="flipper_length_mm",
    hue="species",
    palette=PENGUIN_COLORS,
)
ax.set(xlabel="Bill length (mm)", ylabel="Flipper length (mm)")
ax.get_legend().set_title("Species")
```

```python check for=1.1
ax = chart_axes()[0]
pts = points(ax)
assert abs(pts[:, 0].mean() - penguins["bill_length_mm"].mean()) < 0.5, "x should be the bill_length_mm column."
assert abs(pts[:, 1].mean() - penguins["flipper_length_mm"].mean()) < 0.5, "y should be the flipper_length_mm column."
assert {"Adelie", "Chinstrap", "Gentoo"} <= set(legend_labels(ax)), "Color the points by species with hue='species'."
assert near_color(PENGUIN_COLORS["Gentoo"], colors_used(ax)), "Use palette=PENGUIN_COLORS so species keep their colors."
assert "_" not in ax.get_xlabel() and "_" not in ax.get_ylabel(), "Write the axis labels in plain English, e.g. 'Bill length (mm)'."
assert "mm" in ax.get_xlabel() and "mm" in ax.get_ylabel(), "Include the units (mm) in both axis labels."
print("Bills and flippers grow together, and each species has its own cluster.")
```

```python exercise id=1.2 title="Find another paradox"
# Is a deeper bill a sign of a heavier penguin?
# 1. Plot bill_depth_mm (x) against body_mass_g (y), colored by species.
# 2. Give it a title that states what you see WITHIN species.
ax = sns.scatterplot(data=penguins, x="bill_depth_mm", y="body_mass_g")
```

```python solution for=1.2
ax = sns.scatterplot(
    data=penguins,
    x="bill_depth_mm",
    y="body_mass_g",
    hue="species",
    palette=PENGUIN_COLORS,
)
ax.set(
    xlabel="Bill depth (mm)",
    ylabel="Body mass (g)",
    title="Within each species, deeper bills mean heavier penguins",
)
ax.get_legend().set_title("Species")
```

```python check for=1.2
ax = chart_axes()[0]
pts = points(ax)
assert abs(pts[:, 0].mean() - penguins["bill_depth_mm"].mean()) < 0.3, "x should be bill_depth_mm."
assert abs(pts[:, 1].mean() - penguins["body_mass_g"].mean()) < 30, "y should be body_mass_g."
assert {"Adelie", "Chinstrap", "Gentoo"} <= set(legend_labels(ax)), "Split the cloud by species with hue - that's where the paradox hides."
assert len(ax.get_title()) >= 15, "Add a title that states the finding, not just the variable names."
print("Overall, deeper bills look LIGHTER (Gentoos are heavy with shallow bills),\n"
      "but within each species the trend is positive. Simpson strikes again.")
```

## Quick quiz

```quiz
- q: "In `sns.scatterplot(data=penguins, x=\"flipper_length_mm\", y=\"body_mass_g\")`, what does `data=` expect?"
  options:
    - "A Python list containing the column names you want to plot"
    - "A DataFrame whose columns you then name in `x` and `y`"
    - "A NumPy array with exactly two rows, one for x and one for y"
    - "The file path of a CSV, which seaborn reads for you"
  answer: B
  explain: "Seaborn's grammar is built on tidy DataFrames: pass the frame once with `data=`, then refer to its columns by name."
- q: "What does adding `hue=\"species\"` to a scatter plot do?"
  options:
    - "It sorts the rows of the DataFrame by species before plotting"
    - "It draws a separate subplot for every species"
    - "It changes the marker shape for each species"
    - "It maps each species to a color and adds a legend"
  answer: D
  explain: "`hue` maps a column to color. Separate subplots come from `col=`/`row=` in figure-level functions (Lesson 5); marker shape is `style=`."
- q: "What do axes-level functions such as `sns.scatterplot` return?"
  options:
    - "A matplotlib `Axes` you can finish with `ax.set(...)`"
    - "A pandas DataFrame containing the plotted x and y values"
    - "A PNG image of the finished chart, as raw bytes"
    - "Nothing - they return `None` once the chart is drawn"
  answer: A
  explain: "Keeping the returned `Axes` is how you add labels, titles, reference lines and annotations with matplotlib."
- q: "Across all penguins, longer bills look shallower, but within each species longer bills are deeper. What's the lesson?"
  options:
    - "The overall trend is the true one; per-group trends are just noise"
    - "Negative correlations in scatter plots are usually artifacts"
    - "A hidden group can reverse a trend, so always check for groups"
    - "Scatter plots cannot show relationships between two measurements"
  answer: C
  explain: "This is Simpson's paradox. Coloring by a plausible grouping variable (`hue=`) is the cheapest way to check for it."
```

!!! note "Key takeaways"
    - Pass a tidy DataFrame with `data=`, then map columns to channels: `x`, `y`, `hue`, `style`, `size`.
    - Use a **dict** palette so each category keeps its color on every chart.
    - Keep the returned `ax` and finish the chart: plain-English labels with units (the legend title too), and a title that states the finding.
