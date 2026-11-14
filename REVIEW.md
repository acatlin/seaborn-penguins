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
in a follow-up pass, which also turned up the new Low findings at the end of that section.

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
| L4-L9, L12 | Low | Raw pair-plot labels, box frames, an exam distractor, hover contrast and more | Left alone, see below |
| L13, L14 | Low | Found in the follow-up: `binwidth=` is approximate; three unit checks pass on raw column names | Left alone, see below |

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

Left alone, with reasons:

- **L4. `pairplot` keeps raw axis labels.** The text frames it as an exploration tool, and
  since the L1 fix it says in so many words that this is why the names are raw.
- **L5. Lessons 1-5 keep the full box frame** (`despine` is taught in Lesson 6). A
  deliberate progression; Few would despine from the first chart.
- **L6. `02-binwidths`** has unshared y axes (correct, since bin width changes the counts)
  but only the first panel carries the y label.
- **L7. Exam Q5's distractor `sns.histplot(cumulative="ecdf")`** uses an invented value
  for a real keyword; harmless but a learner who knows `cumulative=True` may hesitate.
- **L8. `--ink-3` text on the hover surface** (`#6b7280` on `#f2f0ea`) is 4.2:1, just under
  AA for small text; on the page background it is 4.6:1.
- **L9. Exercise 4.1's solution heatmap** shows the full matrix with raw column names and
  an unlabeled colorbar. The exercise doesn't ask for the renaming and masking taught in
  the lesson, which keeps it short; the check accepts either.
- **L12. The exam's Q10 (sorting bars)** has the correct option as the longest because it
  is real code; a learner who knows `order=` is not helped by that.

Found during the follow-up pass, and left alone:

- **L13. `binwidth=` is approximate in seaborn 0.13.** `histplot` turns it into a whole
  number of bins across the data's range, so `binwidth=3` on flipper length draws 2.95 mm
  bins. In Lesson 2's `02-binwidths` figure the panel titled "binwidth = 250 g" has 257 g
  bins and the one titled "binwidth = 1000 g" has 900 g bins, and the alt text repeats the
  nominal widths. The lesson's point (too narrow, sensible, too wide) survives. Passing
  `binrange=(2500, 6500)` would make all three widths exact, at the cost of one more
  argument in an early example; a sentence saying that seaborn rounds would also do.
- **L14. Three more unit checks pass on raw column names.** Exercises 3.2, 5.1 and 6.1
  look for "mm" in an axis label, which `bill_depth_mm`, `flipper_length_mm` and
  `bill_length_mm` satisfy untouched, so their "label the axes" hints never fire. The
  briefs of 5.1 and 6.1 ask for plain-English labels; 3.2's does not, so there the
  assertion is dead rather than lax. The condition used in 1.1, 2.1 and 4.2
  (`"_" not in label`) would fix each.

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
