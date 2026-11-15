# Lesson 6 - From default to deliberate: polish with matplotlib

<p class="lede">Seaborn gets you a correct chart fast. Matplotlib gets you the last 20%: the labels, highlights and annotations that turn a chart into a message. This lesson is a makeover.</p>

**By the end of this lesson you can:**

- set a theme and context with `sns.set_theme`
- choose categorical, sequential or diverging palettes for the right job
- lay out several charts with `plt.subplots` and `ax=`
- highlight, annotate, directly label, and format a chart
- save publication-quality files

```python setup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks")
penguins = sns.load_dataset("penguins")
PENGUIN_COLORS = {"Adelie": "#FF8C00", "Chinstrap": "#A034F0", "Gentoo": "#159090"}
SEX_COLORS = {"Female": "#8c8c8c", "Male": "#333333"}
```

## How seaborn and matplotlib fit together

A matplotlib **Figure** is the canvas. Each **Axes** is one plotting area on it, with its own x-axis, y-axis, title and legend. Seaborn's axes-level functions draw *into* an Axes. Everything you add afterwards (labels, lines, text, tick formats) is plain matplotlib called on that same `ax`.

## Themes and contexts

`sns.set_theme(style=..., context=...)` changes defaults for every chart that follows. `style` controls the background and grid, and `context` scales fonts and lines for where the chart will be shown (`"paper"`, `"notebook"`, `"talk"`, `"poster"`).

```python run fig=06-styles alt="The same histogram drawn in four seaborn styles: darkgrid, whitegrid, ticks and white."
fig = plt.figure(figsize=(12, 2.8))
for i, style in enumerate(["darkgrid", "whitegrid", "ticks", "white"]):
    with sns.axes_style(style):          # temporarily switch style
        ax = fig.add_subplot(1, 4, i + 1)
    sns.histplot(data=penguins, x="body_mass_g", binwidth=250, ax=ax)
    ax.set(title=f'style="{style}"', xlabel="Body mass (g)", ylabel="")
fig.tight_layout()
```

This course uses `"ticks"`. It's quiet, with no gridlines competing with the data. Use `"whitegrid"` when readers need to read values off the axis.

## Palettes do jobs

Pick a palette by what color has to *say*:

```python run fig=06-palettes alt="Three color strips: colorblind categorical colors, the crest sequential light-to-dark ramp, and the vlag blue-white-red diverging ramp."
from matplotlib.colors import ListedColormap

palettes = {
    'Categorical - which group?   sns.color_palette("colorblind")': sns.color_palette("colorblind", 6),
    'Sequential - how much?   sns.color_palette("crest")': sns.color_palette("crest", 7),
    'Diverging - above or below a midpoint?   sns.color_palette("vlag")': sns.color_palette("vlag", 7),
}
fig, axes = plt.subplots(3, 1, figsize=(8, 3.4))
for ax, (name, pal) in zip(axes, palettes.items()):
    ax.imshow([list(range(len(pal)))], cmap=ListedColormap(pal), aspect="auto")
    ax.set_title(name, loc="left", fontsize=10)
    ax.set_axis_off()
fig.tight_layout()
```

- **Categorical** for identity (species, island). Hues differ, none "bigger" than another. `"colorblind"` is a safe default.
- **Sequential** for magnitude (counts, mass). One hue, light to dark.
- **Diverging** for data with a meaningful middle (correlation, change from average). Two hues with a neutral center.

!!! warning "Avoid rainbow palettes"
    Rainbows (`"hsv"`, `"jet"`) have no natural order. They create false boundaries where hues shift, and they fail for colorblind readers. About 1 in 12 men has some color-vision deficiency. This course's `PENGUIN_COLORS` were tested to stay distinguishable under the common types.

## Highlight: gray is your best color

When the story is about *one* group, make everything else gray:

```python run fig=06-highlight alt="Bill scatter with Adelie and Chinstrap points in light gray and Gentoo points in teal, labeled directly on the chart."
focus = "Gentoo"
colors = {sp: (PENGUIN_COLORS[sp] if sp == focus else "#cccccc") for sp in PENGUIN_COLORS}

ax = sns.scatterplot(data=penguins, x="bill_length_mm", y="bill_depth_mm",
                     hue="species", palette=colors, legend=False)
ax.text(55, 14.2, "Gentoo", color=PENGUIN_COLORS[focus], fontweight="bold")
ax.set(xlabel="Bill length (mm)", ylabel="Bill depth (mm)",
       title="Gentoos have long but shallow bills")
sns.despine()
```

!!! few "Use color sparingly, and only to mean something"
    Stephen Few's advice: use soft, muted colors for most of the data and save bright, saturated color for what you want noticed. If everything is bright, nothing stands out.

## Layouts: `plt.subplots` + `ax=`

To combine *different* chart types, build the grid with matplotlib and hand each Axes to seaborn:

```python run fig=06-subplots alt="Two side-by-side charts: a step histogram of body mass by species and box plots of body mass by sex, under one figure title."
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")

sns.histplot(data=penguins, x="body_mass_g", hue="species", palette=PENGUIN_COLORS,
             element="step", fill=False, binwidth=200, ax=axes[0])
axes[0].set(xlabel="Body mass (g)", ylabel="Penguins", title="By species")
axes[0].get_legend().set_title("Species")

sns.boxplot(data=penguins, x="sex", y="body_mass_g", color="#bbbbbb", ax=axes[1])
axes[1].set(xlabel="", ylabel="Body mass (g)", title="By sex")

fig.suptitle("What drives a penguin's weight? Species first, sex second.")
```

`layout="constrained"` spaces titles and labels automatically. Use it for every multi-panel figure.

## The makeover

Here is a chart made with every default and every option turned on:

```python run fig=06-before alt="A cluttered scatter plot with rainbow colors, three different marker shapes, varying point sizes and a large legend overlapping the data."
with sns.axes_style("darkgrid"):     # the busiest style, scoped to this one chart
    ax = sns.scatterplot(data=penguins, x="flipper_length_mm", y="body_mass_g",
                         hue="species", style="island", size="bill_depth_mm", palette="hsv")
```

Three encodings, a rainbow palette, a legend covering the data, and raw column names. It *contains* the data, but it doesn't *say* anything. Here's the same data made deliberate:

```python run fig=06-after alt="Clean scatter of flipper length versus body mass with species colored and labeled directly, the heaviest penguin annotated, kilogram tick labels and the title 'Gentoos are in a weight class of their own'."
fig, ax = plt.subplots(figsize=(7.5, 4.6))
sns.scatterplot(data=penguins, x="flipper_length_mm", y="body_mass_g",
                hue="species", palette=PENGUIN_COLORS, s=22, alpha=0.75,
                legend=False, ax=ax)

# 1. Label the groups directly - no legend to decode
for species, (x, y) in {"Adelie": (171, 4500), "Chinstrap": (204, 3050),
                        "Gentoo": (224, 4300)}.items():
    ax.text(x, y, species, color=PENGUIN_COLORS[species], fontweight="bold")

# 2. Annotate the one point worth talking about
heaviest = penguins.loc[penguins["body_mass_g"].idxmax()]
ax.annotate("Heaviest bird: a 6.3 kg Gentoo",
            xy=(heaviest["flipper_length_mm"], heaviest["body_mass_g"]),
            xytext=(186, 6050), color="0.25", fontsize=9,
            arrowprops={"arrowstyle": "->", "color": "0.4"})

# 3. Units people think in
ax.yaxis.set_major_formatter(lambda value, pos: f"{value / 1000:.1f} kg")

# 4. Plain words, a title that makes the point, no box
ax.set(xlabel="Flipper length (mm)", ylabel="Body mass",
       title="Gentoos are in a weight class of their own")
sns.despine()
```

Every change removes work for the reader. They don't look back and forth to a legend. Their eye goes to the one point worth mentioning. They read "5.0 kg" instead of "5000", and the title tells them what to see.

!!! few "Stephen Few's checklist, applied"
    | Principle | In code |
    |---|---|
    | Maximize data-ink, cut non-data ink | `style="ticks"`, `sns.despine()`, no redundant legend |
    | One encoding per variable, only the ones you need | drop `style=` and `size=` that don't serve the question |
    | Label directly when you can | `legend=False` + `ax.text(...)` |
    | Highlight what matters | gray context + one strong color, `ax.annotate(...)` |
    | Titles and labels in plain language with units | `ax.set(title=..., xlabel=...)`, tick formatters |
    | Consistent color for the same thing | one dict palette, reused everywhere |

## Saving your work

```python
fig.savefig("penguin-makeover.png", dpi=200, bbox_inches="tight")  # sharp raster for slides/docs
fig.savefig("penguin-makeover.svg", bbox_inches="tight")            # vector: crisp at any size
```

`bbox_inches="tight"` trims empty margins and keeps labels from being cut off. With a figure-level grid, call `g.savefig(...)` (or `g.figure.savefig(...)`).

## Your turn

```python exercise id=6.1 title="Make over a messy chart"
# This chart works but says nothing. Make it deliberate:
#  - back to the course's quiet theme: sns.set_theme(style="ticks")
#  - PENGUIN_COLORS for species, and drop the style= and size= encodings
#  - no legend (label the species directly with ax.text if you like)
#  - axis labels in plain English with units, and a title that states a finding
#  - remove the top and right spines with sns.despine()
sns.set_theme(style="darkgrid")
ax = sns.scatterplot(data=penguins, x="bill_length_mm", y="bill_depth_mm",
                     hue="species", style="island", size="body_mass_g", palette="hsv")
```

```python solution for=6.1
sns.set_theme(style="ticks")
ax = sns.scatterplot(data=penguins, x="bill_length_mm", y="bill_depth_mm",
                     hue="species", palette=PENGUIN_COLORS, legend=False)
for species, (x, y) in {"Adelie": (33, 21.6), "Chinstrap": (52, 21.2),
                        "Gentoo": (54, 14.0)}.items():
    ax.text(x, y, species, color=PENGUIN_COLORS[species], fontweight="bold")
ax.set(xlabel="Bill length (mm)", ylabel="Bill depth (mm)",
       title="Each species has a bill shape of its own")
sns.despine()
```

```python check for=6.1
ax = chart_axes()[0]
pts = points(ax)
assert abs(pts[:, 0].mean() - penguins["bill_length_mm"].mean()) < 0.5, "Keep bill_length_mm on x and bill_depth_mm on y."
assert near_color(PENGUIN_COLORS["Gentoo"], colors_used(ax)), "Swap the rainbow for palette=PENGUIN_COLORS."
sizes = set().union(*[set(c.get_sizes()) for c in ax.collections])
assert len(sizes) == 1, "Drop size= - point size shouldn't encode anything here."
shapes = {path.vertices.tobytes() for c in ax.collections for path in c.get_paths()}
assert len(shapes) == 1, "Drop style= - marker shape shouldn't encode anything here."
assert ax.get_legend() is None, "Remove the legend with legend=False (direct labels are optional)."
assert "mm" in ax.get_xlabel() and "mm" in ax.get_ylabel() and "_" not in ax.get_xlabel() + ax.get_ylabel(), "Use plain-English axis labels with units, e.g. 'Bill length (mm)'."
assert len(ax.get_title()) >= 15, "Add a title that states a finding."
assert tuple(ax.get_facecolor()[:3]) == (1.0, 1.0, 1.0), "Switch back to the quiet theme first: sns.set_theme(style='ticks')."
assert not ax.spines["top"].get_visible() and not ax.spines["right"].get_visible(), "Call sns.despine() to remove the top and right spines."
print("From noise to message. Compare it with the starter - same data, very different chart.")
```

```python exercise id=6.2 title="Spotlight the Chinstraps"
# Chinstraps hide among Adelies on a flipper-vs-mass scatter.
# Make every species gray except Chinstrap (in its PENGUIN_COLORS purple),
# turn the legend off, label "Chinstrap" directly with ax.text,
# and write a title that mentions Chinstraps.
colors = ___

ax = sns.scatterplot(data=penguins, x="flipper_length_mm", y="body_mass_g",
                     hue="species", palette=colors)
```

```python solution for=6.2
colors = {sp: (PENGUIN_COLORS[sp] if sp == "Chinstrap" else "#cccccc") for sp in PENGUIN_COLORS}

ax = sns.scatterplot(data=penguins, x="flipper_length_mm", y="body_mass_g",
                     hue="species", palette=colors, legend=False)
ax.text(205, 3000, "Chinstrap", color=PENGUIN_COLORS["Chinstrap"], fontweight="bold")
ax.set(xlabel="Flipper length (mm)", ylabel="Body mass (g)",
       title="Chinstraps overlap with Adelies on size alone")
sns.despine()
```

```python check for=6.2
ax = chart_axes()[0]
used = colors_used(ax)
assert near_color(PENGUIN_COLORS["Chinstrap"], used), "Chinstraps should keep their purple."
assert not near_color(PENGUIN_COLORS["Adelie"], used) and not near_color(PENGUIN_COLORS["Gentoo"], used), "Make Adelie and Gentoo gray so only Chinstraps stand out."
assert ax.get_legend() is None, "Turn the legend off with legend=False and label directly."
assert any("Chinstrap" in t.get_text() for t in ax.texts), "Add a direct label with ax.text(x, y, 'Chinstrap', ...)."
assert "chinstrap" in ax.get_title().lower(), "Mention Chinstraps in the title."
print("Spotlight on. Gray is doing the heavy lifting here.")
```

## Quick quiz

```quiz
- q: "Edward Tufte's \"data-ink ratio\", which Stephen Few builds on, says you should..."
  options:
    - "use as much ink as possible so charts look substantial"
    - "always print charts in black ink only"
    - "maximize the share of ink showing data; cut the rest"
    - "add gridlines to every chart so values can be read precisely"
  answer: C
  explain: "Every non-data mark - heavy borders, backgrounds, redundant legends - competes with the data for attention. Remove or mute it."
- q: "What is the main advantage of labeling lines or groups directly instead of using a legend?"
  options:
    - "Readers needn't look back and forth to a legend"
    - "Direct labels make the saved figure file noticeably smaller"
    - "Matplotlib draws text faster than legends"
    - "Legends cannot show more than three categories"
  answer: A
  explain: "A legend is a lookup table. Direct labels put the answer where the eye already is."
- q: "How do you draw a seaborn chart into the second panel of `fig, axes = plt.subplots(1, 2)`?"
  options:
    - "Call `plt.subplot(2)` after the seaborn function has drawn"
    - "Pass `ax=axes[1]` to `sns.relplot`, the figure-level function"
    - "Call `sns.set_theme(ax=axes[1])` before drawing the chart"
    - "Pass `ax=axes[1]` to an axes-level seaborn function"
  answer: D
  explain: "Axes-level functions accept `ax=`. Figure-level functions don't - they make their own figure."
- q: "Your chart is about one species. What does Few recommend for color?"
  options:
    - "Use a rainbow palette so every species is equally vivid and distinct"
    - "Gray out the others; give only the focus group a strong color"
    - "Use the brightest available color for every group"
    - "Remove all color and rely on marker shapes"
  answer: B
  explain: "Muted context plus one saturated highlight tells the reader exactly where to look."
```

!!! note "Key takeaways"
    - `set_theme(style, context)` sets defaults. Pick palettes by job: categorical, sequential or diverging.
    - Combine chart types with `plt.subplots(..., layout="constrained")` and `ax=`.
    - Polish with matplotlib on the returned `ax`: `set`, `text`, `annotate`, `axhline`/`axvline`, tick formatters, `sns.despine()`.
    - Save with `fig.savefig(..., dpi=200, bbox_inches="tight")`.
