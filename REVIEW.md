# Review: Seaborn with Penguins

Independent review of the course as published from `main` (commit `161c53b`), done as a
data-visualization instructor and seaborn/matplotlib maintainer would do it: every claim
and code example checked against seaborn 0.13.2 / matplotlib 3.10.6 and against the data,
every rendered figure in `docs/img/` inspected, the three Word files opened (rendered to
PDF through Word), the notebooks opened, and the quizzes, exam, rubrics and instructor
guide read as assessment instruments.

The test suite was green before any change (50 passed). Findings are ranked by severity.
"Fixed" means the fix is in the repository; "left alone" means it is documented here only.
The High and Medium fixes were made with the review itself. Five of the Low items were fixed
in a follow-up pass. That pass turned up three more Low findings (L13-L15) and fixed two of
them. A second follow-up fixed L6-L9 and the palette half of L15, and wrote down six more Low
findings (L16-L21) without acting on them.

Severity scale:

- **High**: a learner-facing statement or artifact is wrong or broken.
- **Medium**: the material contradicts its own stated principles, an assessment item is
  weak, an accessibility gap, or a maintenance hazard.
- **Low**: polish. Left alone unless the fix was a one-liner made in passing.

## Summary

| # | Severity | Finding | Status |
|---|---|---|---|
| H1 | High | Lesson 1 alt text swaps the marker shapes for male and female | Fixed |
| H2 | High | Notebooks render every design callout as a code block | Fixed |
| H3 | High | Lesson 6 notebook draws the makeover "after" chart in `darkgrid` | Fixed |
| M1 | Medium | Lesson 2 KDE example blends overlapping fills, which the previous paragraph forbids | Fixed |
| M2 | Medium | Lesson 3 count chart leaves islands in order of first appearance | Fixed |
| M3 | Medium | Four different gray pairs for sex across lessons; light gray below 3:1 contrast | Fixed |
| M4 | Medium | Exam: six items with absurd distractors; capstone covered by one numpy-indexing question | Fixed |
| M5 | Medium | Quizzes: implausible distractors, data-ink misattributed to Few, correct option longest in 36% | Fixed |
| M6 | Medium | Quiz options are not programmatically associated with their question | Fixed |
| M7 | Medium | Rubrics describe full credit only; no scoring scale | Fixed |
| M8 | Medium | Word pack: task numbering runs on across assignments; part titles orphaned | Fixed |
| M9 | Medium | Figures are not reproducible: unseeded jitter and bootstrap CIs | Fixed |
| M10 | Medium | Lesson 4 line-chart alt text claims a steady rise; ragged small-n ends unexplained | Fixed |
| L1-L3, L10, L11 | Low | Legend titles, "1.3 kg", panel order, HTML-only stale-docs test, lax exercise 2.1 checker | Fixed in a follow-up |
| L4, L5, L12 | Low | Raw pair-plot labels, box frames in Lessons 1-5, a correct exam option that is the longest | Left alone, see below |
| L6-L9 | Low | Bin-width panels without a y label, an invented exam distractor, muted text under 4.5:1, raw names in exercise 4.1's solution | Fixed in a second follow-up |
| L13, L14 | Low | Found in the follow-up: `binwidth=` is approximate; unit checks pass on raw column names | Fixed in the follow-up |
| L15 | Low | Found in the follow-up: exercise 2.2 checks neither its palette nor its printed answer | Palette check fixed in the second follow-up; the printed answer left alone |
| L16-L21 | Low | Found in the second follow-up: a give-away exam item, a 4.46:1 tick mark, heatmap label rotation, layout advice the course does not follow, an unnamed y-axis, an unshared x-axis | Left alone, see below |

## High

### H1. Lesson 1: alt text describes the wrong markers (fixed)

`01-scatter-style` is described as "circle markers for female and cross markers for male".
Seaborn assigns markers in order of first appearance in the data, and the first penguin in
the table is male, so males are circles and females crosses. The body text had it right;
the alt text, which is all a screen-reader user gets, had it backwards.

Fix: corrected the alt text, and added a sentence explaining that hue and style levels
follow order of appearance and that `hue_order=`/`style_order=` take control. The same
point was added to the Lesson 1 misconceptions in the instructor guide.

### H2. Notebooks: design callouts render as code (fixed)

The Markdown admonitions (`!!! few "Title"` plus an indented body) are the course's second
curriculum, and the notebook export copied them verbatim. Jupyter and Colab have no
admonition extension, so every callout showed a literal `!!! few "..."` line followed by
its body as a monospaced code block. Fourteen notebooks were affected.

Fix: `build_site.py` now rewrites admonitions as blockquotes with a bold label
("Design principle: ...", "Warning", "Note") when it writes notebooks. A new test fails if a
raw marker leaks into any notebook or if the design-principle callout is missing.

### H3. Lesson 6 notebook: the makeover is drawn in the wrong theme (fixed)

The "before" cell called `sns.set_theme(style="darkgrid")`. On the site every cell runs in a
fresh process-like state, so the "after" chart was fine. In the notebooks state persists, so
the "after" chart, the centrepiece of the lesson, rendered with a gray grid background
that contradicts both the text ("no box") and the figure on the site.

Fix: the "before" cell now scopes the style with `with sns.axes_style("darkgrid"):`, a
construct introduced earlier in the same lesson. Exercise 6.1 keeps the bare
`set_theme(style="darkgrid")` in its starter on purpose, now says so in its instructions,
and its checker insists on the reset, so learners meet the "someone changed the theme
three cells ago" bug once, deliberately. A new test runs every lesson's example and
solution cells in notebook order in one namespace and fails if any cell leaves
`matplotlib.rcParams` changed for the cells after it.

## Medium

### M1. Lesson 2: the KDE example does what the previous paragraph warns against (fixed)

Two paragraphs after "filled layers would blend where they overlap: purple over orange
turns muddy pink, a color that belongs to no species", the KDE example used
`fill=True, alpha=0.3`, and the rendered figure shows exactly that muddy overlap between
Adelie and Chinstrap. Fix: outlines (`linewidth=2`), with a sentence saying why.

### M2. Lesson 3: the first chart doesn't model the lesson's own principle (fixed)

The island count chart showed Torgersen, Biscoe, Dream, which is the order the islands
first appear in the CSV, meaningless to a reader. The same lesson teaches "sort by value".
Fix: `order=penguins["island"].value_counts().index`, explained in the text, with the alt
text updated.

### M3. Sex colors are inconsistent, and one gray is too light (fixed)

The course's strongest habit is "the same thing has the same color everywhere", yet sex was
drawn with four different gray pairs: `#7a7a7a/#222222` (Lesson 3), `#9a9a9a/#4a4a4a`
(Lesson 5 catplot), `#a0a0a0/#303030` (Lesson 5 FacetGrid and exercise 5.2) and
`#9a9a9a/#333333` (Lesson 7 and the assignments). `#9a9a9a` on white is 2.8:1, below the
3:1 WCAG minimum for graphical objects.

Fix: every setup cell (and the assignment setup) now defines
`SEX_COLORS = {"Female": "#8c8c8c", "Male": "#333333"}` next to `PENGUIN_COLORS`, and every
sex-colored chart uses it. `#8c8c8c` is 3.4:1 on white. Lesson 3 explains the second
dictionary; the capstone and the instructor guide refer to it.

### M4. Exam item quality and coverage (fixed)

Six items were effectively two-option questions because two distractors were absurd
("The chart becomes too tall to fit on a slide", "Panels are drawn in random order",
"can no longer be saved as PNG, only SVG", "because `ax` is a DataFrame", "A histogram
with 20 bins", "It makes the chart start at zero"). The capstone, the lesson that
integrates everything, was assessed by one question on 2-D array indexing, while Lesson 3
had five questions including a pure recall item (`stripplot`).

Fix: rewrote the weak distractors as plausible misconceptions (Q4, Q7, Q11, Q12, Q20, Q22
in the new numbering); replaced the indexing question and the `stripplot` recall item with
two capstone questions that test design reasoning (why the figure legend is built from
proxy handles; why panel C uses grays). Every lesson now has at least two questions.
Answers stay balanced (A 6, B 6, C 7, D 6), no runs of three, and the correct option is the
longest in 1 of 25 and the shortest in 3 of 25. The instructor guide's exam table and
statistics were updated.

### M5. Quiz item quality (fixed)

Similar problems in the website quizzes: "`sns.histgrid`" (does not exist, so it is not a
distractor), "Pass `hue=axes[1]`", "In a separate image file attached to the report", "That
the figure is exported as SVG", "Seaborn will raise an error when bins are wider than the
standard deviation", and so on. One stem attributed the data-ink ratio to Stephen Few
("from Edward Tufte" in parentheses); it is Tufte's idea, which Few builds on. One
explanation said `plt.figure` before `relplot` "has no effect", but it leaves an empty
figure that a notebook will display. The correct option was the longest in 10 of 28
questions (36%), well above the 25% chance rate.

Fix: rewrote the distractors above, corrected the attribution and the explanation, and
trimmed or lengthened options so that no quiz question now has the correct option as the
longest. Each lesson still uses A-D once. The test threshold was tightened from 40% to
36% to match the README's claim.

### M6. Quiz accessibility (fixed)

Each question was a `div` with a `p` stem and a list of radio inputs. Nothing connected
the stem to the options, so a screen-reader user tabbing through the radios heard option
text without the question. Fix: each question is now `role="group"` with
`aria-labelledby` pointing at the stem. A test checks every page.

### M7. Rubrics without a scale (fixed)

The rubrics (which are specific and well weighted) only described what full credit looks
like, so two graders could give 7/15 and 12/15 for the same "present but flawed" work.
Fix: a three-level scale (full / about half for present-but-flawed / zero) is now stated
in `assignments.yaml` and rendered at the top of Part 2 in both editions, with examples of
"flawed". The instructor guide mentions it. A test checks both editions.

### M8. Word pack layout (fixed)

Word's "List Number" style counts across the whole document, so Assignment 2's tasks were
numbered 5-8 and Assignment 3's 9-12. Model-solution part titles (plain paragraphs) could
be orphaned at the bottom of a page with their code on the next, and this happened twice
in the instructor edition. Fix: numbered lists are written with explicit labels and a
hanging indent (also in the guide), and part titles, the "Output:" label and the intern
chart's lead-in are set to keep with the next paragraph. A test checks that each task list
starts at 1.

### M9. Figures are not reproducible (fixed)

The README promises a byte-for-byte reproducible site, but `stripplot` jitter uses the
legacy NumPy RNG and seaborn's bootstrapped CIs (`barplot`, `pointplot`, `lineplot`,
`regplot`, `lmplot`) use `np.random.default_rng(None)`. Thirteen PNGs changed on a no-op
rebuild, which makes every content PR a noisy image diff and means the in-browser result
of an example never quite matches the figure beside it.

Fix: the shared runner seeds the legacy RNG before every cell and gives `default_rng` a
fixed seed when the caller passes none. Because the browser loads the same `runner.py`,
site and in-browser figures now agree. A test renders a strip plot, a regression and a bar
chart twice and requires identical bytes, and a second full build into a temporary folder
was compared against `docs/img/` (all 52 files identical).

### M10. Lesson 4 line chart: alt text and the ragged ends (fixed)

The alt text said all three lines "rise steadily"; Adelie dips at the 210 mm bin and
Gentoo starts with a lone point, because those bins hold one or two penguins, and the CI
band vanishes where n = 1. Learners were not told why. Fix: the alt text now describes the
wobble, and the text explains it and suggests a caveat or a minimum count.

## Low

Fixed in passing (one-liners):

- Exercise 7.1's solution removed legends through the private attribute `ax.legend_`;
  now `ax.get_legend().remove()`.
- Instructor guide, learning outcome 2 listed "composition" as a chart form the course
  teaches; it doesn't (deliberately). Reworded.
- Instructor guide said whiskers "reach 1.5 x IQR"; they extend to the furthest point
  within 1.5 x IQR of the box. Reworded.
- The Colab link opens a new tab without saying so; added a `title`.

Fixed in a follow-up pass:

- **L1. Legend titles were raw column names** ("species", "sex") in Lessons 1-6, while the
  text says raw names "read as code". Fix: Lesson 1 now treats the legend title as one more
  label, in the section that introduces axis labels, and rewrites it with
  `ax.get_legend().set_title("Species")`. Every later finished chart does the same
  (`g.legend.set_title(...)` on figure-level grids, explained with `lmplot` in Lesson 4),
  including six exercise solutions and the model solution for Assignment 1, chart 2.
  Nineteen site figures changed. Four legends keep seaborn's names on purpose: the bare
  first `hue` example (the next section relabels it), the pair plot (an exploration tool,
  and the text now says that is why its names are raw), the makeover's "before" chart, and
  the `hue` + `style` legend in Lesson 1. In that last one the column names are headings
  inside the legend rather than a title, there is no one-line fix, and the text now points
  at them as part of the price of extra channels. A new test fails if any other legend
  shows a column name, or if a listed exception no longer needs listing.
- **L2. "Gentoos outweigh the other species by about 1.3 kg"** (Lesson 3 title, capstone
  panel B). The mean gaps are 1,343 g (vs Chinstrap) and 1,375 g (vs Adelie), so "about
  1.3" described only the nearer competitor. Fix: the titles now say "by more than 1.3 kg"
  and "more than 1.3 kg heavier on average", which is true against either species and
  against the two pooled (1,365 g).
- **L3. Lesson 5's `relplot(col="island")`** showed panels in order of first appearance
  (Torgersen, Biscoe, Dream). Fix: `col_order=["Biscoe", "Dream", "Torgersen"]`, busiest
  first, the order Lesson 3 and the capstone already use. The paragraph underneath says
  what the argument does and what happens without it, so the example still reads as "one
  argument makes the panels", plus one that orders them.
- **L10. `test_committed_docs_match_sources` compared HTML only.** Fix: it now compares
  every file the build writes (pages, notebooks, scripts, styles, the runner copy, the data
  file) with line endings folded, and lists every problem at once. Figures are checked for
  presence only, because PNG bytes differ between the Windows machine that builds `docs/`
  and the Linux CI runner. `docs/img` and `docs/notebooks` may not hold files the build no
  longer produces. A figure or notebook that was never added to git, or was left behind by
  a rename, now fails CI.
- **L11. Exercise 2.1's checker** only rejected bars. Filled steps passed, and so did an
  unstepped outline, a KDE and an ECDF. So did a chart with no axis label at all, because
  seaborn's own label, `flipper_length_mm`, contains the "mm" the checker looked for. Hollow
  bars were sent after the wrong problem ("Use palette=PENGUIN_COLORS"). Fix: the brief now
  says "outlines only (no fill)", and the checker requires three step outlines over evenly
  spaced bins, no filled areas and a plain-English label, testing shape before color so
  that each hint is true. The bin width is deliberately not checked (see L13). A new test
  runs seven near misses through the checker.

- **L13. `binwidth=` is approximate in seaborn 0.13** (found during the follow-up).
  `histplot` turns it into a whole number of bins across the data's range, so in Lesson 2's
  `02-binwidths` figure the panel titled "binwidth = 250 g" had 257 g bins and the one titled
  "binwidth = 1000 g" had 900 g bins. Fix: the example passes `binrange=(2500, 6500)`, which
  makes all three widths exact, and the paragraph underneath says what `binrange=` is for
  and that seaborn otherwise rounds. The instructor guide lists it as a misconception, and a
  new test checks that each panel draws the width its title names. Elsewhere the course asks
  for a width without quoting the result (`binwidth=3` on flipper length draws 2.95 mm
  bins), which is why exercise 2.1 does not test it.
- **L14. Unit checks passed on raw column names** (found during the follow-up). Exercises
  3.2, 5.1 and 6.1 looked for "mm" in an axis label, which `bill_depth_mm`,
  `flipper_length_mm` and `bill_length_mm` satisfy untouched, so their "label the axes"
  hints never fired. Exercise 4.2 checked its x label properly but ignored its y label. Fix:
  each checker now also rejects an underscore, as 1.1 already did, and 3.2's brief asks for
  the label its checker expects. A new test puts the raw names back on each solution's axes
  and requires a hint.

Fixed in a second follow-up pass:

- **L6. Only the first `02-binwidths` panel named its y-axis.** The three panels do not share
  a y-axis, and should not: wider bins hold more penguins, so the tallest bar stands for 14
  birds at 50 g and for 153 at 1,000 g. One label on the first panel is the convention for a
  *shared* axis. Fix: every panel sets `ylabel="Number of penguins"`. Three y labels do
  not fit matplotlib's default spacing (the second and third ran into the frame of the panel
  to their left), so the figure is built with `layout="constrained"`, which the sentence
  above the code introduces with its pointer to Lesson 6. Constrained layout makes the Axes a
  little shorter, and at the old height that put the ticks of the 50 g panel at every 2.5
  penguins, so the figure is now 3.5 in tall instead of 3.2. A new paragraph under the figure
  tells learners to read the y-axes before they compare heights, and says what the
  `sharey=False` in the code is for. The bin-width test also requires a y label on every
  panel.
- **L7. Exam Q5's distractor `sns.histplot(cumulative="ecdf")`** used an invented value for
  a real keyword. Fix: option C is now `sns.histplot(element="step")`, a call taught in the
  same lesson. It tempts for a real reason, since an ECDF is drawn as steps too (exercise
  2.1's checker already treats an ECDF as a near miss of a step histogram), and it is plainly
  wrong. The real value, `cumulative=True`, would not have been: a cumulative histogram is a
  binned ECDF, and a learner who chose it could argue the point. The explanation gained a
  sentence on the step histogram. The option keeps its place and is still the longest of the
  four, so the answer balance and the option-length figures given under M4 and in the
  instructor guide stand. Both editions of the assessment pack were rebuilt.
- **L8. `--ink-3` text fell below 4.5:1 on tinted backgrounds.** The finding named the hover
  surface (4.24:1). The same gray on the same surface is also the "Design principle" tag at
  the head of every design callout, which is not a hover state, and it measured 4.41:1 on the
  number of the current lesson in the sidebar and 4.23:1 on the letter of a graded quiz
  option. Fix: the light theme's `--ink-3` is `#646b78` instead of `#6b7280`. That gives
  4.69:1 or better wherever the token is used: 4.71 on the hover and callout surface, 4.89 on
  the current sidebar item, 4.69 and 4.70 on a right and a wrong quiz option, 5.14 on the
  page and 5.36 on white. The ratios are computed from the stylesheet; those on the hover
  surface, the callout, the sidebar item and the quiz tints were also measured on the
  rendered page in Chrome. The token stays well apart from `--ink-2` (7.0:1 or more). The
  dark theme already passed (4.56:1 at worst) and is unchanged. A new test computes the ratio
  from `site_src/style.css` for both themes, the two quiz tints included.
- **L9. Exercise 4.1's solution heatmap** showed raw column names and an unlabelled
  colorbar. Fix: the solution renames the columns with the lesson's own `nice` dictionary and
  passes `cbar_kws={"label": "Pearson r"}`, under a comment that marks both as optional
  polish. The brief and the checker are as they were, so the exercise is no longer than
  before and an answer with raw names still passes. The solution still shows the whole
  matrix: the slice-and-mask idiom is the hardest code in the course, and the brief does not
  ask for it.
- **L15, first half. Exercise 2.2 did not check its palette.** Fix: once the checker has
  found the three species, it requires the Chinstrap purple among the lines, with the hint
  "Use palette=PENGUIN_COLORS so the Chinstrap line is purple." A new test takes
  `palette=PENGUIN_COLORS` out of the solution of each of the eight exercises whose brief
  names that palette and requires a hint. The other seven already gave one. The second half
  of L15 is still open, see below.

Left alone, with reasons:

- **L4. `pairplot` keeps raw axis labels.** The text frames it as an exploration tool, and
  since the L1 fix it says in so many words that this is why the names are raw.
- **L5. Lessons 1-5 keep the full box frame** (`despine` is taught in Lesson 6). A
  deliberate progression; Few would despine from the first chart.
- **L12. The exam's Q10 (sorting bars)** has the correct option as the longest because it
  is real code; a learner who knows `order=` is not helped by that.

Found during the follow-up passes, and left alone:

- **L15, second half. Exercise 2.2 cannot check its printed answer.** The second task asks
  learners to print the share of Chinstraps, and a checker sees the chart and the variables a
  cell leaves behind, not what the cell printed. Closing this takes a change to
  `tools/runner.py`, which the browser shares: the captured output would have to be handed to
  the check block.
- **L16. Exam Q5 still gives itself away.** `sns.ecdfplot` is the only option that contains
  the initials of the term the stem spells out, so it can be picked without knowing what an
  ECDF is, and no distractor changes that. It is a recall item of the kind M4 replaced
  (`stripplot`). A sturdier Q5 would ask when an ECDF is the better choice, rather than what
  the function is called.
- **L17. The tick on a completed lesson is 4.46:1 while its sidebar item is hovered.** That
  is `--good` (`#1a7f37`) on `--surface-2`, in the light theme only, and it is the one place
  where that pair meets. `#197d36` would be 4.57:1.
- **L18. Both heatmaps leave the rotation of their tick labels to seaborn**, which turns the
  labels of whichever axis would otherwise overlap. In the built figures (Arial, on the
  machine that builds `docs/`) the row labels of `04-heatmap` and `sol-4.1` run vertically.
  In the browser (DejaVu Sans) `sol-4.1` comes out the other way round, with level row labels
  and vertical column labels. Both are legible, but level row labels read more easily, and
  `ax.tick_params(axis="y", rotation=0)` would keep them level in both places.
- **L19. Lesson 6's layout advice is not what the course does.** Of `layout="constrained"`
  the lesson says "Use it for every multi-panel figure", but its own two earlier figures
  (`06-styles`, `06-palettes`) call `fig.tight_layout()`, and `02-kde-bw` and `03-three-ways`
  use neither. All four render well; it is the advice and the examples that disagree.
- **L20. `06-styles` does not name its y-axis.** All four panels set `ylabel=""`, so the
  counts are numbers without a name. The panels show the same data on the same scale, so a
  label on the first one would do.
- **L21. `02-kde-bw` shares its y-axis but not its x-axis.** The over-smoothed panel runs
  from 0 to 9,000 g and the under-smoothed one from 2,300 to 6,700 g, so the same 1,000 g is
  drawn at two widths, and the right-hand curve looks no wider than the left-hand one when it
  is twice as wide. With `sharex=True` the figure would also show what the callout under it
  says, a density curve reaching far beyond any real penguin (the heaviest weighs 6,300 g,
  and the curve ends near 8,500 g).

## What checked out

Technical accuracy of every example against seaborn 0.13.2 and matplotlib 3.10.6: all
arguments exist and mean what the text says (`errorbar=`, `linestyle="none"` and `legend=`
in categorical plots, `fliersize`, `common_norm`, `bw_adjust`, `cut`, `corner=True`,
`facet_kws`, `g.figure`, `move_legend`, `loc="outside lower center"` with constrained
layout, callable tick formatters). The follow-up pass found one nuance: `binwidth=` is
honoured only approximately (L13). The browser runs matplotlib 3.8.4 under Pyodide 0.27.2;
every API the course uses exists there too.

Numbers quoted in the text, recomputed from the bundled CSV:

| Claim | Computed |
|---|---|
| 342 penguins with flipper and mass; 11 missing sex; 68 Chinstraps | 342; 11; 68 |
| 95% / 97% of Adelies / Chinstraps at or below 4,500 g; 14% of Gentoos; "1 in 7" | 95.4% / 97.1%; 13.8%; 1 in 7.2 |
| 91% of Chinstraps have bills over 45 mm | 91.2% |
| Tallest bar: 14 penguins in 50 g bins, 153 in 1,000 g bins | 14; 153 |
| Each extra mm of flipper adds about 50 g | 49.7 g |
| r(flipper, mass) = 0.87; r(bill depth, mass) = -0.47 | 0.871; -0.472 |
| Truncated bar chart makes Gentoo "nearly eight times" Adelie | 7.9x |
| Gentoos "about 1.4 times" heavier | 1.37x |
| Gentoos "more than 1.3 kg" heavier on average | 1,343 g (vs Chinstrap); 1,375 g (vs Adelie) |
| Heaviest bird a 6.3 kg Gentoo | 6,300 g, Gentoo |
| Male-female gaps about 800 / 670 / 410 g, CIs do not overlap | 805 / 675 / 412 g; no overlap |
| Bill-ratio classifier: 97/96/95% per species, 96.2% overall, 13 of 342 wrong | identical |
| Species palette: minimum pairwise OKLab dE about 16 under CVD | 16.3 (protanopia), 17.6, 17.7 |
| Exam answer balance A 6, B 6, C 7, D 6 | identical |

Pedagogy and pacing: the arc (grammar, distributions, categories, relationships, facets,
polish, capstone) is sound and each lesson fits 45-75 minutes. Lesson 4 is the densest
(the heatmap's slice-and-mask idiom is the hardest code in the course) and Lesson 6 the
richest; the instructor guide's pacing notes already flag `pairplot`. Exercises ramp well
from fill-in-the-blank to a free build, and every checker gives an actionable hint. The one
gap is that no exercise asks learners to critique a chart in words before the assignments;
the quizzes carry that load. The instructor guide is unusually concrete (live-coding order,
misconceptions, troubleshooting table) and needed only the corrections above.
