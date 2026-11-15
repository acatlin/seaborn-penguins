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
findings (L16-L21) without acting on them. A recheck of the mastery objectives added one more
(L22) and nine questions about the objectives map (O1-O9). Seven of them (O1-O7) were decided
as recommended on 2026-11-15 and applied, and a tenth (O10) came up while they were. O8, O9 and
O10 were decided later that day and applied as version 1.3 of the map. The same pass fixed L22
and the British spellings (L27), rechecked the first seven as applied, and wrote down four more
Low findings (L23-L26) and three more questions (O11-O13) without acting on them. All seven were
decided on 2026-11-15, as recommended, and applied in a fourth follow-up, with version 1.4 of the
map. What comes next is planned in `PLAN.md`. Steps A, B and C of that plan are built, and a
recheck of steps A and B added three more Low findings (L28-L30).

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
| L22 | Low | Found while rechecking the objectives: five of the nine pages scroll sideways at phone width | Fixed in a third follow-up |
| L23-L26 | Low | Found in the third follow-up: a gap inside some quiz options at desktop width, three exercise checks that pass what their brief rules out, a small table that breaks across two printed pages | Fixed in a fourth follow-up |
| L27 | Low | Found in the third follow-up: British spellings in a course written in American English | Fixed in the third follow-up |
| L28-L30 | Low | Found in a recheck of exercises 6.3 and 6.4: grams with a thousands comma passed as kilograms, an honest sentence of under 20 characters is turned away, kinds of fault are recognized from letters inside other words | L28 fixed; L29 and L30 left alone, see below |
| O1-O7 | Decision | Questions about the mastery objectives map: a rule that cannot be followed as written, evidence that is tested but not listed, two page roles, overlapping criteria | Decided on 2026-11-15 as recommended, and applied |
| O8-O10 | Decision | More questions about the map: two objectives that each hold several performances, section 2's library, an objective first taught before one of its prerequisites | Decided on 2026-11-15 (split, Plotly, as recommended) and applied in version 1.3 of the map |
| O11-O13 | Decision | Questions from the second recheck: an exercise whose check cannot fail on an objective it is listed for, and two parts of the mastery rule that cannot be followed with today's materials | Decided on 2026-11-15 as recommended, and applied in version 1.4 of the map |

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
the "after" chart, the centerpiece of the lesson, rendered with a gray grid background
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
- **L9. Exercise 4.1's solution heatmap** showed raw column names and an unlabeled
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

Fixed in a third follow-up pass:

- **L22. Five of the nine pages scrolled sideways on a phone.** In a window 390 px wide the page
  was wider than the screen on Start here (647 px), on Lessons 1, 5 and 6 (419, 517 and 471) and
  on the instructor guide (398). Start here did the same in any window narrower than about
  940 px. There were three causes, and the finding as first written had the third one wrong:
  - On Start here, the `pip install` line. A code block that is not Python is a plain `pre`, and
    only the highlighted blocks scrolled inside their own box.
  - On the guide, the workbook's path in the "Mastery objectives" section: inline code that could
    not break.
  - In Lessons 1, 5 and 6, six quiz options that hold inline code, and not "a long call in a quiz
    question". An option is a flex row, so each piece of inline code and each run of words
    between two pieces is a flex item of its own, and a row of items cannot wrap the way a
    sentence does. The quiz and its option list are grids, and their one column grew to fit the
    widest row.

  Fix, in `site_src/style.css`: inline code may break inside a long name (`overflow-wrap:
  break-word`), a plain `pre` scrolls inside its own box, and the two quiz grids let their column
  shrink (`minmax(0, 1fr)`). `tools/build_site.py` now wraps the text of an option in a span.
  Below 860 px, where the sidebar folds away, the span is one flex item, so the option wraps like
  a sentence beside its letter. Above 860 px the span is `display: contents`, which leaves the
  pieces laid out exactly as they were (see L23).

  Measured in Chrome with each of the nine pages in frames 320, 360, 390, 414, 600, 768 and
  860 px wide: no page is wider than its frame. With the stylesheet and the span changed and
  nothing else, the position and size of all 8,472 elements of the nine pages at 1600 px are what
  they were, to a hundredth of a pixel. At 900 px the same holds for eight pages, and Start here
  differs as intended: its `pip install` block has a scrollbar of its own, and the page no longer
  scrolls. At 280 px, narrower than any phone in use, the guide is still 19 px too wide, because
  of a URL used as link text. That is not code, and it was left alone.
- **L27. British spellings in a course written in American English.** "recognise" in the guide's
  learning outcome 2, and "labelled" in its accessibility notes and in the README; "modelling",
  "neighbouring" and "organisation's" in three quiz items (Lessons 2, 3 and 7); "centred" in exam
  Q11; "neighbours" and "labelled" in the assignments; six in this file and three in code
  comments. All are American now. The answer statistics given under M4 and M5 are unchanged.

Fixed in a fourth follow-up pass, after each was decided on 2026-11-15 ("as recommended", which
for these four is the cure the finding itself names):

- **L23. At desktop width, a quiz option that held inline code was laid out in pieces.** This is
  the layout that L22 describes, and above 860 px it was still there: each piece of code and each
  run of words was a flex item, and the row's 8 px gap stood between them where a space would. In
  3 of the 18 options that hold code, a punctuation mark followed a piece of code and stood apart
  from it: a comma in two ("`sns.relplot` , the figure-level function", Lesson 6, Q3) and a
  closing parenthesis in one. The finding as first written counted three commas. Fix, in
  `site_src/style.css`: the option's span is no longer `display: contents` and has
  `min-width: 0` at every width, so an option is one flex item beside its letter and wraps like a
  sentence. Measured in Chrome at 1600 px against the pages as they were: the code inside those
  options sits 3 to 10 px further left, an option that holds code is 1.5 px less tall, and what
  follows it on the page moves up by as much (15 px at most, at the foot of Lesson 5). Nothing
  outside a quiz changed its size or its horizontal position. No page is wider than its window
  at 320 to 860 px.
- **L24. Exercise 2.2's check did not test that the chart is an ECDF.** It looked for the three
  species in the legend, the Chinstrap purple, a vertical line at 45 and the range of the x-axis.
  A histogram of bill length (bars or step outlines) or a density curve passed, and was told to
  "read it off the plot: the purple line crosses 45 mm near 0.09". It is the gap that L11 closed
  in exercise 2.1. Fix: the check requires three lines that each climb from 0 to 1, with a hint
  that names `sns.ecdfplot`. A cumulative histogram scaled to 1 still passes: it is a binned
  ECDF.
- **L25. Two more checks passed what their brief rules out.** Exercise 6.1's brief says to drop
  `style=` and `size=`, and the check tested the sizes only, so a chart that kept a marker shape
  for each island passed. Exercise 7.1's brief asks for `layout="constrained"`, and its hint says
  "keep one legend"; the check tested neither, so a figure with three legends passed. Fix: 6.1
  requires one marker shape, and 7.1 requires the constrained layout and exactly one legend,
  wherever it is. A new test puts six such changes into the three solutions (L24's three among
  them) and requires a hint for each.
- **L26. On the Timing sheet of the workbook, the last small table broke across two printed
  pages.** "Check: every lesson's minutes add up to the midpoint" had its heading and one row on
  the first page and six rows on the second. Fix: the builder puts a page break before the
  heading. Excel honors it although the sheet is fitted to one page wide: its second page now
  starts at the heading. (Since step A of `PLAN.md` the break stands one table higher, before
  "Additions built on top of the lessons", so the second page holds both small tables whole.)

Found in a recheck of steps A and B of `PLAN.md`, on 2026-11-15. Each solution was changed in
ways its test does not try (eight for exercise 6.3, ten for 6.4), and the check was run on each:

- **L28. Exercise 6.3 passed grams as kilograms (fixed).** A formatter that writes the grams with
  a thousands comma ("3,000") under an axis label that says "Body mass (kg)" passed, because the
  check looked for four digits in a row. Fix: the check folds commas and spaces out of a tick
  label first. The attempt is the tenth in the exercise's test.
- **L29. Exercise 6.4 turns away an honest sentence of fewer than 20 characters (left alone).**
  "There is no title." has 18 characters and "Too many encodings." has 19, and each is told to
  "say more". The 20 characters are the plan's, and the message is a friendly one. Counting
  words (three or more) would let both through and still stop "bad colors".
- **L30. Exercise 6.4 recognizes kinds of fault from letters inside other words (left alone).**
  "emphasize" holds "size" and "community" holds "unit", so a learner who wrote neither about
  encodings nor about labels is told "You wrote about the encodings, the labels". And one
  sentence written three times with different punctuation counts as three. Both touch the
  message only, and the check says of itself that it counts and cannot judge. Matching whole
  words, and comparing statements without their punctuation, would close both.

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
honored only approximately (L13). The browser runs matplotlib 3.8.4 under Pyodide 0.27.2;
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
the quizzes carry that load. (Since 2026-11-15 one does: exercise 6.4, `PLAN.md`, step B. Its
check counts the statements and cannot judge them.) The instructor guide is unusually concrete (live-coding order,
misconceptions, troubleshooting table) and needed only the corrections above.

A later pass mapped the course onto twelve mastery objectives, fourteen since version 1.3 of the
map (instructor guide, "Mastery
objectives", and `instructor/Seaborn_Mastery_Objectives.xlsx`). It found two more gaps of
the same kind, both left alone. Nothing assesses the choice of chart form: every assignment
names its chart types, and no exam question or exercise check asks for the choice. And
saving a figure is shown in Lesson 6 as code that is not run, with no exercise to practice
it. The guide lists both, and what to add, under "Next steps". (Since 2026-11-15 the first gap is
closed: exercise 7.2 and the short task "Questions only" name no chart, `PLAN.md`, step C.)

## Recheck of the mastery objectives

A second look at the objectives work (the map in `instructor/mastery_objectives.yaml`, the
workbook, its builder and tests, and the guide's "Mastery objectives" section), made before
anything was built on it. The same pass changed section 3 from Dash to Streamlit.

**Checked, and sound.** Every objective listed for an exercise is tested by an assert in that
exercise's check block (13 exercises). Each of the 28 quiz and 25 exam questions fits the one
objective it is mapped to. Three are close calls and stay as they are: quiz L3 Q3 as S09 rather
than S04, quiz L6 Q1 as S11 rather than S08, and exam Q19 as S10 rather than S06. The 18 rubric
rows fit their "full credit" text, apart from O4 below. Every count, status and hour in the
guide's section agrees with the workbook and the course. Excel, driven through COM, recalculated
all 703 formula cells to the results stored in the file, before the changes and after them, and
all six sheets were looked at as Excel draws them. The guide page was looked at in Chrome: its
lists and three tables render as intended (L22 is what a narrow window showed). The builder and
its tests were read for bugs and none was found in the logic.

**Fixed.**

- **Key tools for I01-I12, written from memory.** Checked against Plotly 7.1.0 and Altair 6.3.0,
  installed and inspected, and against their documentation. Every function and argument exists.
  Three entries were stale or misleading. I08 named `alt.condition`, to which Altair's
  documentation now prefers `alt.when`, and left out `add_params`, without which a selection
  does nothing; it also needed the note that `go.FigureWidget` requires anywidget. I11 listed
  `config={"responsive": True}`, which is already the default in Plotly's HTML output, and said
  only "needs Kaleido" where static export needs Kaleido 1.0 or later and Chrome. "Linked
  brushing in `px.scatter_matrix`" was tried in a browser and holds.
- **Gaps the "Gap today" column did not admit**, found by checking each criterion of S01-S12
  against the pages. No page says how `color=` differs from `hue=` (S01): Lesson 1 uses
  `color="gray"` once without comment, and exam Q1 asks for the difference. No page mentions
  restarting a notebook and running it top to bottom (S12), which the assignments require.
  `ax.axhline` is named in Lesson 6's takeaways and never shown (S08). And S02's gap said the
  checks measure "only a title's length", where exercise 6.2 looks for a word.
- **The note on rubric row A2 R5** described the row as noting "what was left out". The row asks
  for a verdict that "notes uncertainty".
- **Exam Q6 on the Evidence sheet** read "What is the main problem with this chart..." with no
  chart. The builder now adds the code a question refers to, and a test checks it.
- **The assumption about tools** claimed that another library would change only the "Key tools"
  column. I04 and I07 name Plotly's own functions in their criteria, and the assumption now says
  so.

**Section 3 is written for Streamlit.** D02-D09, D11 and D12 are reworded in Streamlit's terms
(the top-to-bottom rerun, session state, caching, fragments, `AppTest`, Community Cloud), and
D04, D05 and D06 are renamed to match. Every name was checked against Streamlit 1.67.0, installed
and inspected, and its documentation; the behavior the criteria describe (a widget's key cannot
be assigned after the widget is drawn, a reset through a button callback, a cache surviving
reruns, a message and `st.stop` for an empty selection) was run through `AppTest`. Five
objectives are 10 to 15 minutes shorter, which takes section 3's lessons from 12.5 to 11.4 hours.
The two sentences that said a dashboard needs a running server were wrong for Streamlit: stlite
runs it in the browser on Pyodide. A test page served as static files ran a select box, a cached
load, a Plotly selection and a fragment (stlite 1.12.2, which bundles Streamlit 1.65.0, about a
minute to load the first time). It is a second runtime beside the site's own, the exercise
checker cannot look inside it, and `streamlit.testing` is not in its build.

**Questions about the map.** O1-O7 were decided on 2026-11-15, as recommended, and applied in
version 1.2 of the map. Each of the seven ends with what was done. O8, O9 and O10 were decided
later the same day and applied in version 1.3: each ends with the decision.

- **O1. Mastery rule 1 cannot be followed as written.** "An objective is mastered when every
  exercise listed for it passes its automatic check." S02 is listed for nine exercises, the last
  of them in Lesson 6, and S02 is a prerequisite of S03, S04, S05, S06, S08 and S12. Exercise
  2.1, which S02 needs, is the exercise that practices S03, which needs S02 first. S07 and S08
  have the same shape. Recommendation: for rule 1, count only the exercises on the pages that
  teach the objective (marked T on the Page map). S02 then needs 1.1 and 1.2, S07 needs 1.1, 6.1
  and 6.2, and S08 needs 6.1 and 6.2. The later exercises stay on the sheets as reinforcement.
  Applied: rule 1 now reads "every exercise that checks it on the pages that teach it", and the
  Objectives sheet names those exercises first under "Practice today" ("Exercises for mastery"),
  with the others as "Further practice". S02 needs 1.1 and 1.2 and S08 needs 6.1 and 6.2, as
  above. S07 needs 1.1, 3.1, 3.2, 6.1 and 6.2: O5 makes Lesson 3 a page that teaches S07, so its
  two exercises count too. Two exercises still serve an objective and its prerequisites at once
  (1.2 for S05, S01 and S02, and 6.1 for S11, S07 and S08), but each sits at the end of a page
  that teaches all of them. A test now fails if an objective's mastery waits for an exercise on
  a page later than the first page teaching an objective that needs it.
- **O2. S01 is counted for one exercise, though seven more checks test it.** Exercises 1.2, 2.1,
  2.2, 4.2, 5.2, 6.1 and 7.1 assert which column sits on x, y or hue, and none lists S01. The
  stated rule ("only when its check tests that objective") is not broken, but the guide explains
  the high counts of S02 and S07 by that rule, and S01 would count higher still. Recommendation:
  add S01 to 1.2, which is in S01's own lesson and makes the learner add `hue=`, and say in the
  fifth assumption that later checks use the mapping to recognize the chart, not to test S01.
  Applied: S01 is listed for exercise 1.2, two exercises in all, and the fifth assumption states
  the convention.
- **O3. "No redundant legend" is a criterion of S08, and two checks test it without listing
  S08.** Exercises 3.2 and 5.1 assert that the legend is gone, with a hint that it would repeat
  the axis or the panel titles. Exercises 6.1 and 6.2 count the same assert for S08.
  Recommendation: add S08 to both (3 exercises become 5), and map Lesson 5's `catplot` section,
  where the idea is first explained, as an introduction to S08.
  Applied: S08 is listed for 3.2 and 5.1, five exercises in all, and Lesson 5's `catplot`
  section is mapped as introducing it. Lesson 3 passes `legend=False` in two examples without
  saying why, so a learner first meets the reason in the hint of exercise 3.2.
  Since the second recheck, Lesson 3 says why, and is mapped as the page that introduces the
  idea. That recheck also found exercise 3.2's check weaker than this item took it to be: O11.
- **O4. Two rubric rows are mapped more narrowly than their neighbors.** A3 R2 asks for "ECDF
  reference lines" and does not list S08, though exercise 2.2 counts a reference line for S08.
  A3 R4, the makeover, is mapped to S11 alone, while exercise 6.1, which is the same task, is
  S11, S02, S07 and S08, and A3 R3 is split in the same way. Recommendation: add S08 to A3 R2,
  and map A3 R4 to S11, S02, S07 and S08. The guide's table would change (S02 from 2 rubric rows
  to 3, S07 from 5 to 6, S08 from 1 to 3). No status would.
  Applied: A3 R2 lists S08, and A3 R4 lists S11, S02, S07 and S08. The guide's table changed as
  predicted.
- **O5. Two page roles.** "Three ways to follow along" on Start here is mapped as an
  introduction to S12. It is about running the course's code, and reads as orientation, like the
  two sections before it. And Lesson 3's point-plot section is mapped as reinforcing S07, but it
  is the only place that teaches "a second variable never borrows those colors" and that shape
  should carry the distinction too. By the sheet's own definition (the main instruction for one
  of the criteria) that is teaching. Recommendation: orientation for the first, and "teaches"
  for the second, which makes S07 "taught in Lessons 1, 3, 6".
  Applied: both roles changed, and the guide's table shows S07 as taught in Lessons 1, 3, 6.
- **O6. S02's fourth criterion reaches into S06.** Labeling "on a grid" with
  `g.set_axis_labels` and `g.legend.set_title` cannot be done in Lesson 1, where S02 is taught,
  and S06 has the same criterion. Recommendation: end S02's criterion at the Axes and take
  "seaborn grids" out of its key tools.
  Applied: the criterion ends "on an Axes", and S02's key tools name the Axes methods only.
- **O7. I05 and I07 share a criterion.** "Panels that are compared zoom together" (I05) is
  I07's "Zooming one panel zooms the panels it is compared with", and I05 comes before panels
  are taught. Recommendation: keep it in I07 and move `matches=` there.
  Applied: I05 keeps three criteria, and `matches=` is among I07's key tools.
- **O8. S05 and S12 each hold more than one performance.** S05 is a fitted trend, a line chart,
  a correlation heatmap, a pair plot and the check for hidden groups. Its own next step says to
  split it "if learners stall". S12 is two: saving files that can be reproduced, and writing
  what a figure shows, which the rubrics already score in separate rows. Recommendation: decide
  before the mastery checks are written, because a check is written per objective. Splitting
  either one ends "twelve per section".
  Decided on 2026-11-15: split. Applied in version 1.3 of the map, as set out under "Second
  recheck of the mastery objectives".
- **O9. Section 2's library is still a placeholder.** Two things learned in this pass bear on
  it. Altair links two views in a few lines, where Plotly needs a scatter matrix, a notebook
  widget or section 3. And Streamlit's documentation now recommends its Vega-based charts,
  `st.altair_chart` among them, for new 2-D charts, and `st.plotly_chart` for a Plotly figure
  you already have. Plotly still fits I03-I06 (tooltips, the figure object, navigation,
  controls), which are written around it.
  Decided on 2026-11-15: Plotly. Applied in version 1.3: section 2's tools are Plotly's, I08
  (linked views) lists the scatter matrix and the notebook widget and no longer Altair's
  functions, and the fourth assumption says what that costs: linking two separate charts is
  finished in section 3 (D07). Lesson 7's "Where to next?" still tells learners "Plotly or
  Altair". It was left as it is: advice to a learner about what exists, not the course's plan.
- **O10. S11 needs S09, but is first taught before it.** S11 (critique and redesign) lists S09
  (choose the chart form) as a prerequisite. S09 is taught in Lesson 7, Step 1, while S11 is
  first taught by the makeover in Lesson 6, where its one exercise, 6.1, sits too. It is the
  only objective first taught before one of its prerequisites. Nothing deadlocks: S09 needs
  nothing from S11, and a learner does exercise 6.1 in Lesson 6 in any case, for S07 and S08.
  But the Prerequisites column promises "objectives to master first", and that cannot hold for
  the Lesson 6 half of S11. Found while applying O1. Recommendation: leave the map as it is, and
  when the mastery checks are written, place S11's after Lesson 7, where the rest of S11 is
  taught.
  Decided on 2026-11-15, as recommended. The map is as it was. S11's "Next step" on the
  Objectives sheet and step 3 of the guide's "Next steps" now say that S11's mastery check
  belongs after Lesson 7. Since step C of `PLAN.md` S09 has an exercise in Lesson 7, and the
  rule-1 test names this pair as the one that was decided.

## Second recheck of the mastery objectives

A cold check of the first recheck's last step (O1-O7 as applied in version 1.2 of the map), made
on 2026-11-15 before anything is planned on top of it. The same pass applied the three decisions
that were still open.

**Checked, and sound.**

- Rule 1 reads the same in the YAML, on the Read me sheet and in the guide. Worked out by hand
  from the page map and the evidence map, the exercises it counts for S01-S12 are the ones the
  Objectives sheet names under "Practice today" and the ones `tests/test_objectives.py` pins.
- For O2 and O4-O7, the "Applied" note, the YAML, the workbook and the guide agree, and the lesson
  source, the check code or the rubric text bears each one out. O3 holds for exercise 5.1 and for
  Lesson 5's `catplot` section, and less well for exercise 3.2 (O11).
- Each exercise's solution was broken in one way for each objective the map lists for it, 62
  broken solutions in all, and the exercise's own check was run on each. Every listed objective
  has at least one that its check rejects. Thirteen pass: the three of L24 and the three of L25,
  the one of O11, three in which S02 is tested through the title and not through the axis labels
  (exercises 1.2, 3.1 and 6.2), and three that are no fault of the check.
- Excel, through COM, recalculated all 703 formula cells of version 1.2 to the stored results,
  and all 739 of version 1.3. All six sheets were looked at as Excel draws them, both times.
- The guide's "Mastery objectives" section was looked at in Chrome at 1600 px, and in the Word
  guide rendered to PDF. After its last two changes the first recheck had compared the built HTML
  only.
- Every name in the "Key tools" of D01-D12 exists in Streamlit 1.67.0, which is still the current
  release. What had only been read in the documentation was run as a two-page app in Chrome:
  pages made with `st.Page` and `st.navigation`, and a widget in the entry script that keeps its
  value on both; `bind="query-params"`, which put the choice into the URL, restored it on a reload
  and from a link to the other page, and dropped a value that is not among the options; and
  `persist_state="session"`, which kept a widget's value across a page switch while a widget
  without it went back to its default. The Plotly names of I01-I12 were checked again against
  Plotly 7.1.0, since section 2 now rests on them.

**Fixed.**

- **The note on exercise 3.2** said that the check "requires legend=False". It requires that no
  legend is drawn, which is not the same thing (O11). The note now says what the check does.
- **Lesson 3 now says why its examples pass `legend=False`**, in one sentence under the box,
  violin and strip plots. That section is mapped as introducing S08, and the note on Lesson 5's
  `catplot` section no longer calls itself the first.
- L22 and L27, above.

**O8 as applied.** Splitting took choices that the decision did not make. They are listed so that
any of them can be reversed.

- *Codes.* The half that keeps the old name's main idea keeps the code, and the halves split off
  are S13 and S14. A code is never reused, and the builder wants each section's codes in order,
  so they follow S12, although S13 is taught in Lesson 4.
- *S05, "Show a trend and check for hidden groups".* The fitted trend, the line chart and
  Simpson's paradox. Four criteria: three as they were, and "looks at the points before trusting
  a straight line", which Lesson 4's warning box teaches. It keeps exercises 1.2 and 4.2, quiz
  L1 Q4, L4 Q1 and L4 Q3, and exam Q13 and Q15. It has no rubric row any more: no assignment asks
  for a fitted trend or a line chart.
- *S13, "Show correlations among several variables".* The heatmap and the pair plot. Three
  criteria: the two that were S05's, and "checks whether a correlation holds within groups",
  which the last lines of the heatmap section and exercise 4.1 teach. It needs S01, S02 and S05.
  It takes exercise 4.1, quiz L4 Q4, exam Q14 and Q16, and rubric row A2 R3. Covered.
- *Lesson 4's 60 minutes* are 35 for S05 and 25 for S13.
- *S12, "Save a figure that can be reproduced".* The files and the notebook. Three criteria: the
  old first one is now two (the PNG, and the choice of format for the destination), and the
  restart. Rubric rows A1 R6 and A3 R6. Still Partial.
- *S14, "Describe what a figure shows".* The words. Three criteria: the two that were S12's, and
  "each claim points at something the reader can check", which is what Assignment 2's rubric
  means by "cites evidence". Rubric rows A1 R5 and A2 R5. Its status is Planned, not Partial: by
  the sheet's own definition, no page teaches it. Lesson 4's line-chart section, which asks for
  "a caveat in the caption", is mapped as introducing it.
- *The 25 minutes to write* that were S12's are 10 for S12 and 15 for S14, so no total of hours
  changed.
- *What follows.* 38 objectives, 14 of them static: 11 Covered, 2 Partial (S09 and S12) and 1
  Planned (S14). The exam has questions on ten of the fourteen. Section 1 averages 30 minutes
  per objective, not 35. The assumption that spoke of "three sections of twelve" now says
  fourteen, twelve and twelve.

**Questions for a decision.** All three were decided on 2026-11-15, as recommended, and applied
in version 1.4 of the map. Each ends with what was done.

- **O11. Exercise 3.2 is listed for S08, but its check cannot fail on what S08 asks.** The check
  asserts that the chart has no legend. Seaborn 0.13 leaves a legend out by itself when every
  value of the `hue` column is the value on the categorical axis, so the solution passes with
  `legend=False` deleted. The assert fails only if the learner asks for a legend or colors by
  another column. In exercise 5.1 the same assert is a real test, because `displot` draws the
  legend unless told not to. Lesson 5's `catplot` example needs its `legend=False` too: eleven
  penguins have no `sex`, and one missing value is enough for seaborn to bring the legend back.
  Recommendation: take S08 off exercise 3.2 (S08 would count 4 exercises, not 5; no status
  changes, and rule 1 does not count 3.2 for S08 in any case). And say in the guide's Lesson 3
  notes that deleting `legend=False` there changes nothing, so that an instructor who tries it
  in front of a class is not caught out.
  Decided on 2026-11-15, as recommended. Applied: exercise 3.2 is listed for S04, S02 and S07,
  with a note that says why S08 is not among them. S08 counted 4 exercises, and counts 5 again since exercise 6.3 was added (`PLAN.md`, step A).
  The guide's Lesson 3 notes say what happens when
  `legend=False` is deleted, and when the argument is needed. Run again for this: exercise 3.2
  and both of Lesson 3's examples that pass it draw no legend without it.
- **O12. An instructor cannot see whether part 1 of rule 1 is met.** "Every exercise that checks
  it ... passes its automatic check": the workbook names the exercises, but a pass is a line of
  text under the learner's editor. The site keeps the editor's text and nothing else, nothing
  reaches the instructor, and every exercise offers its solution one click away, on purpose (the
  guide says the exercises "are for practice, not grading"). So the instructor watches, or takes
  the learner's word. Recommendation: say which in the rule, for example "shown to the
  instructor, or handed in as the lesson's notebook with its outputs", or word part 1 as what a
  learner does before asking for the mastery check, which is how the exercises are meant.
  Recording a pass in the browser, as the quiz records a finished lesson, would give the learner
  something to show. It is a small change to `live.js`, but a solution that was loaded and run
  would earn the tick too.
  Decided on 2026-11-15: the first wording. Applied: part 1 of rule 1 now ends "passes its
  automatic check, shown to the instructor or handed in as the lesson's notebook with its
  outputs", in the YAML, on the Read me sheet and in the guide. One thing the wording leaves to
  the instructor: a notebook has no automatic check, so a notebook that is handed in shows the
  charts, and the instructor compares them with the solutions notebook. How a learner takes a
  mastery check (`PLAN.md`, question 3) was answered later on 2026-11-15: an honor system for
  now, and web pages with a database later. Whether part 1 of rule 1 is then taken on the
  learner's word as well was not said, so its wording stands. Recording a pass in the browser,
  the other way out that this item names, is not decided either.
- **O13. With today's materials, part 2 of rule 1 comes too late.** Part 2 needs a mastery check,
  and none exists yet. Rule 5 says to use "the exercises and rubric rows" meanwhile. The rubric
  rows come with the assignments, after Lessons 3, 5 and 7, which is later than the objectives
  that need them. S01's only row is in Assignment 1, while S02, S03 and S04 all need S01 first.
  S08's three rows are all in Assignment 3, while S10 and S11 need S08. S05 has no row at all
  since the split. It is the deadlock that O1 took out of part 1, in part 2, and rule 5 does not
  say whether the exercises alone let a learner move on. Recommendation: say so. Until the
  mastery checks are written, a learner moves on when the exercises of rule 1 pass, and the
  rubric rows of the next assignment confirm the objective or send the learner back. The mastery
  checks of step 3 remove the problem, since a check can be taken at any time.
  Decided on 2026-11-15, as recommended. Applied: rule 5 now says that no mastery check is
  written yet, that until one is a learner moves on when the exercises of rule 1 pass, and that
  the rubric rows of the next assignment confirm the objective or send the learner back. The
  exam's questions are for finding what to rework, as before. Rule 5 is rewritten again when the
  checks exist (`PLAN.md`, step E).

**What comes next.** Steps 2 to 4 of the guide's "Next steps" are planned in `PLAN.md`: two
exercises, a task, a new section in Lesson 7 and the mastery checks, with ten questions to answer
first. Nine of the ten were answered on 2026-11-15, as recommended, and the answers are written
under each question there. Question 3 (how a learner takes a check) was answered later that day:
an honor system for now. Steps A and B
of the plan are built: exercise 6.3 for S08, and exercise 6.4 for S11. So is step C: exercise 7.2
and the short task "Questions only" for S09, which is Covered now. One of the ten follows from
O10. An exercise for S09 in Lesson 7 makes the rule-1 test fail as it was written, because S11
needs S09 and is first taught one lesson earlier. Since step C the test names that pair.
