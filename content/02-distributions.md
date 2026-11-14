# Lesson 2 - Distributions: how heavy is a penguin?

<p class="lede">An average hides almost everything interesting. Before you compare means, look at the whole spread: where values pile up, how wide they range, and whether there's more than one peak.</p>

**By the end of this lesson you can:**

- draw histograms with `histplot` and choose bin widths on purpose
- compare groups with overlaid steps instead of stacked bars
- draw smooth density curves with `kdeplot` and know when they mislead
- read an ECDF (`ecdfplot`) to answer "what fraction is below X?"

```python setup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks")
penguins = sns.load_dataset("penguins")
PENGUIN_COLORS = {"Adelie": "#FF8C00", "Chinstrap": "#A034F0", "Gentoo": "#159090"}
```

## A histogram in one line

```python run fig=02-hist-basic alt="Histogram of body mass for all penguins, ranging from about 2,700 to 6,300 grams with a lumpy, right-leaning shape."
ax = sns.histplot(data=penguins, x="body_mass_g")
ax.set(xlabel="Body mass (g)", ylabel="Number of penguins")
```

A histogram sorts values into **bins** and draws a bar for each bin's count. This one is lumpy, with a big hump on the left and a shoulder on the right. That's a clue that more than one group is mixed together.

## Bin width changes the story

Seaborn picks a bin width for you. It's a reasonable guess, but still a guess. Here are three choices side by side. `plt.subplots` makes a row of empty Axes, and each seaborn call draws into one of them with `ax=` (Lesson 6 covers this properly):

```python run fig=02-binwidths alt="Three histograms of body mass: 50 g bins look noisy, 250 g bins show two humps, 1,000 g bins hide the shape entirely."
fig, axes = plt.subplots(1, 3, figsize=(11, 3.2), sharey=False)
for ax, width in zip(axes, [50, 250, 1000]):
    sns.histplot(data=penguins, x="body_mass_g", binwidth=width, ax=ax)
    ax.set(title=f"binwidth = {width} g", xlabel="Body mass (g)", ylabel="")
axes[0].set_ylabel("Number of penguins")
```

Narrow bins show noise. Very wide bins wash out the two humps. Try a few widths, and pick one that shows real structure without inventing any. You can set `binwidth=` or `bins=` (a count).

## Compare groups: layer, don't stack

```python run fig=02-hist-stack alt="Stacked histogram of body mass by species; only the bottom layer, Adelie, sits on the axis, making the others hard to judge."
ax = sns.histplot(data=penguins, x="body_mass_g", hue="species",
                  palette=PENGUIN_COLORS, multiple="stack")
ax.set(xlabel="Body mass (g)", ylabel="Number of penguins", title="Stacked: hard to read")
```

Stacking answers "how many penguins in total per bin?" To compare species, though, you have to judge the Chinstrap and Gentoo bars from a floating baseline. Overlaid **step** outlines put every group on the same zero line:

```python run fig=02-hist-step alt="Overlaid step histograms of body mass by species: Adelie and Chinstrap overlap around 3,700 g while Gentoo sits higher around 5,000 g."
ax = sns.histplot(data=penguins, x="body_mass_g", hue="species",
                  palette=PENGUIN_COLORS, element="step", fill=False,
                  linewidth=2, binwidth=200)
ax.set(xlabel="Body mass (g)", ylabel="Number of penguins",
       title="Gentoos are a heavyweight class of their own")
```

`fill=False` draws outlines only. Filled layers would blend where they overlap: purple over orange turns muddy pink, a color that belongs to no species.

!!! few "Give comparisons a common baseline"
    People judge position along a shared scale far more accurately than length from a floating start. When readers must compare groups, give each one the same baseline. Use layered steps, or separate panels on shared axes (Lesson 5).

## Smooth curves: kernel density estimates

A KDE replaces bars with a smooth curve. It's easier to overlay, but it involves a choice you don't see.

```python run fig=02-kde alt="Filled density curves of body mass for each species; Adelie and Chinstrap peak near 3,700 g and Gentoo near 5,000 g."
ax = sns.kdeplot(data=penguins, x="body_mass_g", hue="species",
                 palette=PENGUIN_COLORS, fill=True, common_norm=False, alpha=0.3)
ax.set(xlabel="Body mass (g)", ylabel="Density")
```

Two settings to know:

- **`common_norm`.** By default (`True`) all the curves *together* have area 1, so a small group (68 Chinstraps) gets a short curve. `common_norm=False` gives each species area 1, which compares *shapes* fairly.
- **`bw_adjust`.** This sets how much smoothing to use. Too little gives spurious wiggles. Too much melts real peaks together:

```python run fig=02-kde-bw alt="Two density plots of all body masses: bw_adjust 0.25 shows many spiky bumps; bw_adjust 3 shows a single smooth hill that hides the two groups."
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
for ax, bw in zip(axes, [0.25, 3]):
    sns.kdeplot(data=penguins, x="body_mass_g", bw_adjust=bw, fill=True, ax=ax)
    ax.set(title=f"bw_adjust = {bw}", xlabel="Body mass (g)")
```

!!! warning "KDEs can draw data that doesn't exist"
    A density curve spills past the real minimum and maximum. It would happily suggest penguins weighing 2,000 g. For bounded or small data, prefer a histogram, or pass `cut=0` to stop the curve at the data's range.

## ECDF: the most honest distribution plot

An **empirical cumulative distribution function** answers questions like "what fraction of penguins weigh 4,500 g or less?" There are no bins and no smoothing to choose. Every point is plotted.

```python run fig=02-ecdf alt="ECDF of body mass by species with a dashed reference line at 4,500 g: about 95 percent of Adelies and Chinstraps fall below it, but only about 14 percent of Gentoos."
ax = sns.ecdfplot(data=penguins, x="body_mass_g", hue="species", palette=PENGUIN_COLORS)
ax.axvline(4500, color="gray", linestyle="--", linewidth=1)
ax.set(xlabel="Body mass (g)", ylabel="Proportion at or below",
       title="Only 1 in 7 Gentoos weighs 4,500 g or less")
```

Follow the dashed line up. About 95% of Adelies and 97% of Chinstraps are at or below 4,500 g, but only about 14% of Gentoos. You can check that with pandas:

```python run
(penguins.dropna(subset=["body_mass_g"])
    .assign(light=lambda d: d["body_mass_g"] <= 4500)
    .groupby("species")["light"].mean()
    .round(2))
```

!!! few "Show the distribution, not just the mean"
    Two groups can share a mean and still look nothing alike. Readers deserve to see the spread, the skew, and the outliers. Once you know the distribution, a summary like a mean or median can follow.

## Your turn

```python exercise id=2.1 title="Flipper lengths, species by species"
# Draw overlaid STEP histograms of flipper_length_mm, one per species,
# using PENGUIN_COLORS and a 3 mm bin width. Label the x-axis with units.
ax = sns.histplot(data=penguins, x="flipper_length_mm")
```

```python solution for=2.1
ax = sns.histplot(
    data=penguins,
    x="flipper_length_mm",
    hue="species",
    palette=PENGUIN_COLORS,
    element="step",
    fill=False,
    binwidth=3,
)
ax.set(xlabel="Flipper length (mm)", ylabel="Number of penguins")
```

```python check for=2.1
ax = chart_axes()[0]
assert {"Adelie", "Chinstrap", "Gentoo"} <= set(legend_labels(ax)), "Split the histogram by species with hue='species'."
assert near_color(PENGUIN_COLORS["Chinstrap"], colors_used(ax)), "Use palette=PENGUIN_COLORS."
assert len(ax.patches) == 0, "Use element='step' so the groups are outlines on a shared baseline, not bars."
lo, hi = ax.get_xlim()
assert lo > 150 and hi < 250, "x should be flipper_length_mm."
assert "mm" in ax.get_xlabel(), "Label the x-axis in plain English with units, e.g. 'Flipper length (mm)'."
print("Three clear peaks - flipper length alone nearly separates Gentoos from the rest.")
```

```python exercise id=2.2 title="What share of Chinstraps have bills over 45 mm?"
# 1. Draw an ECDF of bill_length_mm by species (PENGUIN_COLORS), with a
#    vertical reference line at 45 mm (ax.axvline).
# 2. Use pandas to print the share of Chinstraps with bill_length_mm > 45.
ax = sns.ecdfplot(data=penguins, x=___)

chinstraps = penguins[penguins["species"] == "Chinstrap"]
print(___)
```

```python solution for=2.2
ax = sns.ecdfplot(data=penguins, x="bill_length_mm", hue="species", palette=PENGUIN_COLORS)
ax.axvline(45, color="gray", linestyle="--", linewidth=1)
ax.set(xlabel="Bill length (mm)", ylabel="Proportion at or below")

chinstraps = penguins[penguins["species"] == "Chinstrap"]
print((chinstraps["bill_length_mm"] > 45).mean().round(2))
```

```python check for=2.2
ax = chart_axes()[0]
assert {"Adelie", "Chinstrap", "Gentoo"} <= set(legend_labels(ax)), "Draw one ECDF per species with hue='species'."
xs = [line.get_xdata() for line in ax.lines]
assert any(len(set(x)) == 1 and abs(x[0] - 45) < 0.01 for x in xs), "Add a vertical line at 45 with ax.axvline(45)."
lo, hi = ax.get_xlim()
assert 25 < lo < 40 and 55 < hi < 65, "x should be bill_length_mm."
print("About 0.91 - read it off the plot: the purple line crosses 45 mm near 0.09.")
```

## Quick quiz

```quiz
- q: "You draw a histogram with very wide bins and see a single smooth hump. What's the risk?"
  options:
    - "None - wider bins always reduce noise, so the single hump is the truth"
    - "Seaborn will raise an error when bins are wider than the data's standard deviation"
    - "Wide bins can merge separate peaks, hiding groups such as species"
    - "The y-axis switches from counts to densities, which changes the shape"
  answer: C
  explain: "Bin width is a modelling choice. Too wide hides structure (two humps become one); too narrow shows noise. Try several."
- q: "With `hue=\"species\"`, `kdeplot` uses `common_norm=True` by default. What does that mean?"
  options:
    - "Together the curves integrate to 1, so small groups look short"
    - "Each curve is scaled to the same peak height so shapes are comparable"
    - "The curves share a common bandwidth chosen from the largest group"
    - "Values are standardized to z-scores before the densities are estimated"
  answer: A
  explain: "With a common normalization, curve area reflects group size. Use `common_norm=False` when you want to compare shapes."
- q: "On an ECDF of body mass, the Gentoo line has height 0.14 at x = 4,500. What does that mean?"
  options:
    - "14 Gentoo penguins weigh exactly 4,500 g"
    - "Gentoos are 14% heavier than average at 4,500 g"
    - "The density of Gentoo weights peaks at 4,500 g"
    - "About 14% of Gentoos weigh 4,500 g or less"
  answer: D
  explain: "An ECDF's height at x is the proportion of observations at or below x."
- q: "Why are stacked histograms a poor choice for comparing groups?"
  options:
    - "Stacking always double-counts observations that fall on bin edges"
    - "Only the bottom layer sits on a shared baseline; the others float"
    - "Stacked histograms cannot use more than two colors"
    - "They require the data to be sorted before plotting"
  answer: B
  explain: "Upper layers start wherever the layer below ends, so their heights can't be compared by eye. Layer steps or use small multiples."
```

!!! note "Key takeaways"
    - `histplot` for counts. Choose `binwidth` on purpose.
    - Compare groups with `element="step"` or separate panels, not `multiple="stack"`.
    - `kdeplot` is smooth but invented. Mind `bw_adjust`, `common_norm`, and `cut`.
    - `ecdfplot` shows every point with no tuning, which makes it great for "what share is below X?"
