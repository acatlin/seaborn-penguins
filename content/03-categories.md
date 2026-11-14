# Lesson 3 - Comparing categories: bars, boxes and dots

<p class="lede">Which island has the most penguins? Which species is heaviest? Questions about groups are the bread and butter of everyday charts, and also where most chart crimes happen.</p>

**By the end of this lesson you can:**

- count categories with `countplot`
- summarize a number per group with `barplot`, and read its error bars
- sort and orient bars so the ranking reads at a glance
- show whole distributions per group with box, violin and strip plots
- use `pointplot` when a zero baseline isn't meaningful

```python setup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks")
penguins = sns.load_dataset("penguins")
PENGUIN_COLORS = {"Adelie": "#FF8C00", "Chinstrap": "#A034F0", "Gentoo": "#159090"}
SEX_COLORS = {"Female": "#8c8c8c", "Male": "#333333"}
```

## Counting: who lives where?

```python run fig=03-count alt="Count of penguins on each island by species, islands sorted from most to fewest penguins: Biscoe has Adelie and Gentoo, Dream has Adelie and Chinstrap, Torgersen has only Adelie."
island_order = penguins["island"].value_counts().index   # most to fewest penguins
ax = sns.countplot(data=penguins, x="island", hue="species", palette=PENGUIN_COLORS,
                   order=island_order)
ax.set(xlabel="", ylabel="Number of penguins",
       title="Adelies live everywhere; Gentoos and Chinstraps each keep to one island")
ax.get_legend().set_title("Species")
```

Here's a fun fact the chart makes obvious: **Gentoos were only found on Biscoe and Chinstraps only on Dream**, while Adelies live on all three islands. `countplot` is just a bar chart of `value_counts()`. Two small decisions already make it easier to read. `order=` lists the islands from busiest to quietest (`value_counts()` is already sorted, so its index is a ready-made order). Without it, seaborn uses the order in which the islands first appear in the data, which means nothing to a reader. And the x-label is blank: "island" adds nothing when the tick labels are island names.

## Bars for a summary statistic

`barplot` computes a statistic per group (the mean by default) and draws it as a bar:

```python run fig=03-bar-default alt="Bar chart of mean body mass by species with black error bars; Gentoo is tallest at about 5,000 g."
ax = sns.barplot(data=penguins, x="species", y="body_mass_g")
ax.set(xlabel="", ylabel="Mean body mass (g)")
```

The black lines are **error bars**. By default they show a 95% confidence interval for the mean, found by bootstrapping. Control them with `errorbar=`:

| `errorbar=` | Shows | Use it to say... |
|---|---|---|
| `("ci", 95)` (default) | uncertainty of the *mean* | "how precisely do we know the average?" |
| `"sd"` | standard deviation of the *data* | "how spread out are individual penguins?" |
| `("pi", 50)` | the middle 50% of the data | "where do typical penguins fall?" |
| `None` | nothing | when the bars alone tell the story |

Always say which one you used in a caption or title. "Error bar" on its own means nothing to a reader.

## Make the ranking obvious: sort and turn sideways

```python run fig=03-bar-sorted alt="Horizontal bar chart of mean body mass sorted from Gentoo (heaviest, about 5,076 g) to Chinstrap and Adelie (about 3,700 g)."
order = (penguins.groupby("species")["body_mass_g"]
         .mean().sort_values(ascending=False).index)

ax = sns.barplot(data=penguins, y="species", x="body_mass_g", order=order,
                 hue="species", palette=PENGUIN_COLORS, errorbar=None)
ax.set(xlabel="Mean body mass (g)", ylabel="",
       title="Gentoos outweigh the other species by more than 1.3 kg")
```

Three deliberate choices here:

1. **Sorted** with `order=`, so the ranking reads top to bottom.
2. **Horizontal** (categorical column on `y`), so long labels never need tilting.
3. **Colored by species with a dict**, the same colors as in every other lesson. Passing `hue=` along with `palette=` is how seaborn 0.13 wants it.

!!! few "Bars must start at zero"
    A bar encodes its value by its **length**. Cut the axis and the lengths lie. The chart below starts at 3,500 g and makes the Gentoo bar nearly eight times longer than the Adelie bar, when Gentoos are really only about 1.4 times heavier.

```python run fig=03-bar-truncated alt="Deliberately bad bar chart with the axis starting at 3,500 g, exaggerating the difference between species."
ax = sns.barplot(data=penguins, x="species", y="body_mass_g", errorbar=None, color="gray")
ax.set_ylim(3500, 5200)
ax.set(xlabel="", ylabel="Mean body mass (g)", title="DON'T: truncated bars exaggerate")
```

If zero isn't meaningful for your data, don't use bars. Use **points** (see `pointplot` below).

## Beyond the mean: boxes, violins and strips

A bar of means hides the spread. These three charts show the whole distribution for each group:

```python run fig=03-three-ways alt="Box plot, violin plot and strip plot of flipper length by species, side by side."
fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
kw = dict(data=penguins, x="species", y="flipper_length_mm",
          hue="species", palette=PENGUIN_COLORS, legend=False)
sns.boxplot(ax=axes[0], **kw)
sns.violinplot(ax=axes[1], **kw)
sns.stripplot(ax=axes[2], alpha=0.6, **kw)
for ax, name in zip(axes, ["boxplot", "violinplot", "stripplot"]):
    ax.set(title=name, xlabel="", ylabel="Flipper length (mm)")
```

- **Box plot:** the median, the middle 50% (the box), whiskers, and outliers. It's compact and great for many groups.
- **Violin plot:** a mirrored KDE. It shows the shape, but carries the KDE's smoothing caveats.
- **Strip plot:** every penguin as a dot, with no hiding. It gets crowded with big data.

A strong default for modest data is a **box plot with the raw points on top**:

```python run fig=03-box-strip alt="Box plots of body mass by species with every individual penguin overlaid as a semi-transparent black dot."
ax = sns.boxplot(data=penguins, x="species", y="body_mass_g",
                 hue="species", palette=PENGUIN_COLORS, legend=False,
                 fliersize=0, boxprops={"alpha": 0.4})
sns.stripplot(data=penguins, x="species", y="body_mass_g",
              color="black", size=3, alpha=0.5, ax=ax)
ax.set(xlabel="", ylabel="Body mass (g)", title="Every penguin, plus the summary")
```

`fliersize=0` hides the box plot's own outlier dots, because the strip already shows every point.

## Point plots: compare when zero isn't meaningful

```python run fig=03-point alt="Point plot of mean body mass by species for female and male penguins; males are heavier in every species."
ax = sns.pointplot(data=penguins, x="species", y="body_mass_g", hue="sex",
                   palette=SEX_COLORS, dodge=0.3, linestyle="none", markers=["o", "s"])
ax.set(xlabel="", ylabel="Body mass (g), mean and 95% CI",
       title="Males are heavier in every species")
ax.get_legend().set_title("Sex")
```

`linestyle="none"` removes the lines `pointplot` would otherwise draw *between species*. Lines imply a continuous path, and there's nothing "between" an Adelie and a Chinstrap. `SEX_COLORS` is the second fixed palette from the setup cell: two grays, so a chart about sex never borrows the species colors, and the marker shapes carry the distinction even without color.

!!! few "Save the pie for dessert"
    People compare angles and areas poorly but lengths and positions well. A sorted bar or dot chart beats a pie chart for almost any comparison. Seaborn has no pie function, and that's no accident.

## Your turn

```python exercise id=3.1 title="Rank the species by flipper length"
# Make a HORIZONTAL bar chart of mean flipper_length_mm by species,
# sorted longest at the top, colored with PENGUIN_COLORS, no error bars,
# and a title stating the finding.
order = ___

ax = sns.barplot(data=penguins, x="species", y="flipper_length_mm")
```

```python solution for=3.1
order = (penguins.groupby("species")["flipper_length_mm"]
         .mean().sort_values(ascending=False).index)

ax = sns.barplot(data=penguins, y="species", x="flipper_length_mm", order=order,
                 hue="species", palette=PENGUIN_COLORS, errorbar=None)
ax.set(xlabel="Mean flipper length (mm)", ylabel="",
       title="Gentoos have the longest flippers")
```

```python check for=3.1
ax = chart_axes()[0]
bars = [p for p in ax.patches if p.get_width() > 0 and p.get_height() > 0]
assert len(bars) == 3, "I expected exactly three bars - one per species."
widths = [b.get_width() for b in bars]
heights = [b.get_height() for b in bars]
assert max(widths) > 100 and max(heights) < 2, "Make the bars horizontal: put species on y and flipper length on x."
bars.sort(key=lambda b: b.get_y())
w = [b.get_width() for b in bars]
assert w == sorted(w, reverse=True), "Sort the bars longest-first with order=... (top of the chart = first in order)."
assert len(ax.lines) == 0, "Turn off the error bars with errorbar=None."
assert near_color(PENGUIN_COLORS["Gentoo"], colors_used(ax)), "Color by species: hue='species', palette=PENGUIN_COLORS."
assert len(ax.get_title()) >= 10, "Add a title that states the finding."
print("Sorted, horizontal, zero-based, consistently colored - a textbook bar chart.")
```

```python exercise id=3.2 title="Show every penguin's bill depth"
# Box plot of bill_depth_mm by species (PENGUIN_COLORS, no legend),
# with every penguin overlaid as small black dots using stripplot(ax=ax).
# Label the y-axis in plain English, with units.
ax = sns.boxplot(data=penguins, x="species", y="bill_depth_mm")
```

```python solution for=3.2
ax = sns.boxplot(data=penguins, x="species", y="bill_depth_mm",
                 hue="species", palette=PENGUIN_COLORS, legend=False, fliersize=0)
sns.stripplot(data=penguins, x="species", y="bill_depth_mm",
              color="black", size=3, alpha=0.5, ax=ax)
ax.set(xlabel="", ylabel="Bill depth (mm)", title="Gentoos have the shallowest bills")
```

```python check for=3.2
ax = chart_axes()[0]
assert len(ax.patches) >= 3, "Draw a box plot first."
pts = points(ax)
assert len(pts) > 300, "Overlay every penguin with sns.stripplot(..., ax=ax)."
assert near_color(PENGUIN_COLORS["Adelie"], colors_used(ax), tol=0.15), "Color the boxes by species: hue='species', palette=PENGUIN_COLORS."
assert ax.get_legend() is None, "The species names are already on the axis - pass legend=False."
assert "_" not in ax.get_ylabel() and "mm" in ax.get_ylabel(), "Label the y-axis in plain English with units, e.g. 'Bill depth (mm)'."
print("Box for the summary, dots for the truth. Gentoo bills are clearly shallower.")
```

## Quick quiz

```quiz
- q: "Why must the value axis of a bar chart start at zero?"
  options:
    - "Matplotlib cannot draw bars that start anywhere else"
    - "Starting at zero makes the error bars symmetric about the mean value"
    - "Zero-based axes leave more room for the legend"
    - "Bars encode value by length, so a cut axis distorts comparisons"
  answer: D
  explain: "Readers compare bar lengths. A truncated axis makes small differences look huge. If zero isn't meaningful, use points instead of bars."
- q: "By default, what do the black lines on top of `sns.barplot` bars show?"
  options:
    - "The minimum and maximum value in each group"
    - "A bootstrapped 95% confidence interval for the mean"
    - "One standard deviation of the individual data points"
    - "The interquartile range of each group"
  answer: B
  explain: "The default `errorbar=(\"ci\", 95)` shows uncertainty in the estimated mean. Use `\"sd\"` or `(\"pi\", 50)` to show spread of the data instead - and say which you used."
- q: "You want to compare the full distribution of flipper length across three species and still see every bird. Which is best?"
  options:
    - "A pie chart of mean flipper length per species"
    - "A bar chart of mean flipper length per species"
    - "A box plot with a strip plot of the raw points on top"
    - "A 3D bar chart with species on one axis and island on another"
  answer: C
  explain: "The box summarizes, the strip shows every observation. Bars of means and pies both hide the distribution."
- q: "What is the main benefit of sorting bars by value (e.g. with `order=`)?"
  options:
    - "The ranking can be read at a glance"
    - "Seaborn computes the group means faster when the bars are sorted"
    - "The longest category label ends up next to the axis, so nothing overlaps"
    - "The error bars shrink, because neighbouring groups are compared in order"
  answer: A
  explain: "Unless the categories have a natural order (like months), sort by value so the comparison the reader wants is already done."
```

!!! note "Key takeaways"
    - `countplot` counts. `barplot` summarizes. Say what the error bars mean.
    - Sort bars, lay long labels horizontally, and always start bars at zero.
    - Show distributions with box + strip (or violin). Use `pointplot` when zero isn't meaningful.
    - Skip pie charts. Lengths and positions beat angles.
