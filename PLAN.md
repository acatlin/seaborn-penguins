# Plan: finishing section 1 for mastery

This is the plan for steps 2, 3 and 4 of "Next steps" in the instructor guide's "Mastery
objectives" section: the teaching, the exercises and the mastery checks that the fourteen
objectives of section 1 still lack. It was worked out on 2026-11-15 against version 1.3 of the
objectives map (`instructor/mastery_objectives.yaml`).

**Steps A, B and C are built** (2026-11-15). Steps D and E are not. Nine of the ten questions under "Decide first" were answered
on 2026-11-15, each as recommended, and so were O11, O12 and O13 in `REVIEW.md`. The answer is
written under each question. Question 3 was answered later the same day: an honor system for now.
Two things that answer leaves open are listed under it, and step E waits for them.

How to use it:

- Answer the questions, then build the steps in the order given, one pull request into
  `develop` for each.
- A step changes the lesson, the map, the guide and the tests together. The build and `pytest`
  fail until the map and the course agree, and several tests pin today's numbers on purpose
  (see "Places that hold a number").
- When a step is built, say so here in the same pull request, and take its minutes out of
  "Minutes: to write" in the map. Question 2 decides where they go.

## Where section 1 stands

Twelve of the fourteen static objectives are Covered, one is Partial (S12) and one is Planned
(S14). Five objectives had work waiting when this plan was written, and two still have:

| Objective | Status | What is missing | Minutes to write | Step |
|---|---|---|---|---|
| **S08** Polish a chart with matplotlib | Covered | Nothing since step A: exercise 6.3 checks `ax.annotate` and a tick formatter | built: 10 | A |
| **S11** Critique and redesign a chart | Covered | Nothing since step B: exercise 6.4 asks for a critique before the page gives one | built: 10 | B |
| **S09** Choose the chart form from the question | Covered | Nothing since step C: exercise 7.2 checks the form, and the short task "Questions only" scores the reasons | built: 20 | C |
| **S12** Save a figure that can be reproduced | Partial | Saving is shown as code that is not run, and no page explains rerunning a notebook | 10 | D |
| **S14** Describe what a figure shows | Planned | No page teaches it, though two rubric rows score it | 15 | D |

The 65 minutes are the 1.1 hours of additions in the guide's Timings table: 40 are built, and 25
are still to write. The other nine objectives need nothing here but their mastery checks
(step E). No mastery check exists yet for any objective.

Today's counts: 16 exercises, 54 figures, 28 quiz questions, 25 exam questions, 30 lesson goals,
and 22 rubric rows in 3 assignments and a short task.

The work is about 58 to 73 hours of building and checking in all, most of it in step E, or 59 to
75 with the hour or two that question 2 adds once. The hours given with each step are rough.

## Decide first

1. **Where do the mastery checks live?** This repository is public, and so are its answer
   keys. The guide says the checks are "kept out of the public repository".
   Recommendation: a private companion repository for the questions, the tasks and their keys.
   This repository keeps the builder, the tests of the format and a manifest that holds counts
   only, so that the workbook can say what exists without showing it. Needed for step E.
   Decided on 2026-11-15: as recommended. The private repository is not made yet: it is made with
   step E, and the guide now says that the checks live in a private companion to this one.
2. **How are the minutes of an addition counted?** The map holds every lesson at its 60-minute
   midpoint, and a test enforces the sum.
   Recommendation: leave each lesson at 60 and count the additions as a block of their own: 65
   minutes, about one more session. The alternative lets Lessons 6 and 7 grow to 80 and 105
   minutes, past the guide's 45-75. Either way, the map, the builder and the Timing sheet have
   no place yet for minutes that were added to a lesson. The first step that is built has to
   make one: about 1 to 2 hours, once, on top of that step's own. Needed for steps A to D.
   Decided on 2026-11-15: as recommended. Each lesson stays at 60 minutes, and the minutes of an
   addition that is built are counted in a block of their own. Step A made the place: the list
   `added_minutes` in the map, a column "Minutes: additions built" on the Objectives sheet, and a
   row and a small table on the Timing sheet. A test holds "additions built" and "to write"
   together at 65 minutes for section 1.
3. **How does a learner take a check?** On paper or in Word, or in a learning management
   system, and which one? No recommendation: it depends on where the course runs. The answer
   sets the format that the builder writes, and it may settle O12. Needed for step E.
   Decided on 2026-11-15, in the instructor's words: "For now, let's make the mastery check honor
   system; we'll later move this into web pages with a database back end." As read here: for now a
   learner takes a check unsupervised and reports the result, and nobody proctors it. The answer
   does not choose among the paths that were offered (Word or paper, a learning management
   system, or both), and it leaves two things open that step E needs: where a learner gets a
   check and its key, since question 1 keeps both out of this repository, and who scores it, the
   learner or the instructor. The later move to web pages with a database is not planned here.
4. **Is five the number of questions in a check, or the least? And do the five objectives that
   are shown by a task get questions as well?**
   Recommendation: five, in two forms, for the nine objectives that are shown by questions,
   which is 90 questions. The other five get tasks only. Questions for all fourteen would be
   140. Needed for step E.
   Decided on 2026-11-15: as recommended. Rule 2 and the third assumption now say "five questions", where
   they said "five or more", and step 3 of the guide's "Next steps" gives the 90 questions and
   the ten tasks.
5. **O11, O12 and O13 in `REVIEW.md`.** O11 changes how many exercises count for S08 (step A).
   O12 and O13 change the mastery rule, which the checks carry out (step E).
   Recommendation: as given there.
   Decided on 2026-11-15: all three as recommended, and applied in version 1.4 of the map. What was done
   is written under each of them in `REVIEW.md`.
6. **May exercises be renumbered to follow the page?** A new exercise does not always belong at
   the end of its lesson: step B's sits above exercise 6.1.
   Recommendation: no. A new exercise takes the next free number, even where that puts 6.4
   above 6.1 on the page. The site keeps a learner's code in the browser under the exercise's
   number, so after a renumbering a returning learner would find old code in the wrong editor.
   Needed for steps A to D.
   Decided on 2026-11-15: as recommended. Numbers are not reused or moved.
7. **Is the "questions only" task a task of its own, or a part of Assignment 3? And may the
   rubrics be re-weighted?** Every rubric totals 100, so a new row takes points from others.
   Recommendation: a short task of its own after Lesson 7, with its own 100-point rubric, and
   Assignment 3 left as it is. For alt text (step D), a row of 10 points in Assignment 3, with
   5 points taken from each of its two "Report figure" rows: it is the only assignment in which
   no row scores a description of a figure. Needed for steps C and D.
   Decided on 2026-11-15: as recommended, for the task and for the 10-point row.
8. **Does "Describe and deliver" go in Lesson 6 or in Lesson 7? And is it acceptable that two
   things are done in the notebook and not on the page: opening the saved file, and restarting
   and running all cells?**
   Recommendation: Lesson 7, as Step 5, where the finished report is the figure to hand over.
   And yes: the page can check a saved file and the words, and it has no kernel to restart.
   Needed for step D.
   Decided on 2026-11-15: as recommended: Lesson 7, Step 5, and yes. The map's next steps for S12 and S14
   and step 2 of the guide's "Next steps" now name Lesson 7.
9. **Do the questions of a check use the penguins only?**
   Recommendation: penguins for the first form of each check. A second dataset in the second
   form would show that the skill carries over, at the price of new figures for every question
   that shows a chart. Needed for step E.
   Decided on 2026-11-15: as recommended. Whether the second form uses a second dataset was not asked
   and is not decided: the recommendation covers the first form only.
10. **What gives way when S09 gets an exercise?** S11 lists S09 as a prerequisite and is first
    taught in Lesson 6, one lesson before S09 (O10, decided: leave the map as it is). Today
    that costs nothing, because S09 has no exercise. Once an exercise in Lesson 7 counts for
    S09, `test_rule_one_waits_only_for_exercises_on_the_pages_that_teach_the_objective` fails
    with "S11 needs S09 first". This was tried on a copy of the map. There are three ways out:
    - Keep the map, as O10 decided, and let the test name this one pair, with the reason.
    - Take S09 out of S11's prerequisites. Nothing fails, but the map stops saying that a full
      critique judges the chart's form.
    - Give S09 no exercise on the page. It then stays Partial, since Covered asks for one.

    Recommendation: the first. S11's mastery check already belongs after Lesson 7.
    Needed for step C.
    Decided on 2026-11-15: the first, as recommended. The test is changed with step C, when the
    exercise exists. Until then it passes as it stands.

## The steps

### Step A. Exercise 6.3: annotate a point and format the ticks (S08)

Step 4 of the guide. About 3 hours. Needs questions 2, 5 and 6.

**Built on 2026-11-15**, as planned, with these particulars:

- The starter draws the scatter with its colors, labels and title, so the learner adds two
  things only. The check therefore tests S08 alone, and the exercise is listed for S08 alone.
- The check asks for a little more than the plan said: the annotation needs words, the tick
  labels or the y-axis label must say "kg", and the data must stay in grams (a chart of
  `body_mass_g / 1000` is told that a formatter changes the labels, not the data).
- A test puts nine attempts through the check: seven that must each earn their own hint, and
  two other correct answers that must pass. (A tenth was added by a recheck later that day:
  grams written with a thousands comma, "3,000", under an axis label that says kg. The check had
  passed it, because it looked for four digits in a row.)
- Tried in Chrome, where matplotlib is 3.8.4: the solution, the starter and the nine attempts
  get the same verdict and the same message as in the build.
- O11 took exercise 3.2 off S08, so S08 counts five exercises, and rule 1 counts 6.1, 6.2 and 6.3.

What the plan said:

- **The learner** draws flipper length against body mass, points at the lightest penguin with
  `ax.annotate` and an arrow, and shows the mass axis in kilograms with a tick formatter. The
  lesson's own example annotates the heaviest bird, so its lines cannot be pasted in unchanged.
- **Where:** Lesson 6, "Your turn", after exercise 6.2.
- **The check** looks for an annotation with an arrow whose point is the lightest bird (a
  2,700 g Chinstrap), and reads the tick labels after a draw: none may still hold a four-digit
  number. Tried under matplotlib 3.10.6, it passes the solution and rejects a chart with no
  formatter, one that uses `ax.text` in place of `ax.annotate`, and one that points at the
  heaviest bird. It has not been tried in the browser, which runs matplotlib 3.8.4.
- **The map:** exercise 6.3 is listed for S08, and for S02 and S07 only if its check tests the
  labels and the colors. S08's 10 minutes to write become minutes that exist. Rule 1 then
  counts 6.1, 6.2 and 6.3 for S08, which has six exercises in all, or five if O11 takes
  exercise 3.2 off.
- **With it:** the guide's count of exercises and S08's row in its table; the README's 13
  exercises and 52 figures, which become 14 and 53; the list pinned in the rule-1 test;
  near-miss tests like those of exercise 2.1; and, if the exercise asks for plain labels or for
  `PENGUIN_COLORS`, the lists `RAW_LABELS` and `ASK_FOR_PENGUIN_COLORS` in `tests/test_site.py`.

### Step B. A written critique before the makeover (S11)

Step 4 of the guide. About 3 hours. Needs questions 2 and 6.

**Built on 2026-11-15**, as planned, with these particulars:

- It is exercise 6.4, between the "before" chart and the paragraph that names its faults. On
  the page it comes before 6.1, and its number is the highest (question 6).
- The check is the lenient one of the plan, with a sixth kind of fault, the background: the
  "before" chart is drawn in the busiest style on purpose. A statement that the check has no
  word for still passes, and the message says that the check counts and does not judge.
- The starter prints the three statements, so that the page shows output and does not ask
  "did you draw a chart?". The solution draws no figure, so the site still has 53.
- **Settled while building: the page's own list stays in plain view,** right below the
  exercise, as "Show a solution" is one click away. Nothing of the lesson's text was changed or
  moved. Folding the list away is a judgment call that is left to the instructor: the Markdown
  extension the build already loads can do it without a new fence, at the price of hiding one
  sentence of the lesson behind a click.
- The notebooks: the exercise is a cell in the middle of the lesson. Both notebooks still run
  top to bottom, and the test that executes the solutions notebooks passes.
- A test puts seven attempts through the check: five that must each earn their hint, and two
  that must pass. Tried in Chrome: the same verdicts and messages as in the build.

What the plan said:

- **The learner** looks at the "before" chart in "The makeover" and writes down three things
  that are wrong with it, as three strings in a list, before reading the page's own list.
- **Where:** Lesson 6, inside "The makeover", between the "before" chart and the paragraph that
  names its faults. It would be exercise 6.4 (question 6), and the first exercise outside a
  "Your turn" section.
- **The check** is lenient on purpose: three statements, all different, each of 20 characters
  or more. Its message says which kinds of fault it recognized (encodings, color, legend,
  labels, title) and which the learner might look at again. It cannot judge whether a critique
  is right. Rubric row A3 R5 does that, and so will S11's mastery check.
- **The map:** exercise 6.4 is listed for S11. S11's 10 minutes to write become minutes that
  exist. Rule 1 then counts 6.1 and 6.4 for S11.
- **With it:** the counts of exercises (the solution draws no figure, which the builder already
  allows, though every exercise today draws one); the guide's Lesson 6 notes, which do this
  aloud today; the pinned rule-1 list.
- **To settle while building:** the page's own list of faults stands right below the exercise,
  in plain view. Either accept that, as with "Show a solution", or fold the reveal away, for
  which the builder has no fence yet. And look at the notebooks: the exercise becomes a cell in
  the middle of the lesson, and the solutions notebook must still run top to bottom.

### Step C. "Questions only": choosing the form (S09)

Step 2 of the guide. About 7 to 8 hours. Needs questions 2, 6, 7 and 10.

**Built on 2026-11-15**, as planned, with these particulars:

- **On the page** it is exercise 7.2, in Step 1 of Lesson 7. It stands above 7.1 on the page
  (question 6). Its three questions: how flipper lengths are spread within each species, which
  species has the deepest bill on average, and whether penguins with longer flippers weigh more.
  Three sentences above it name the three forms that mislead, with the lesson that showed each.
- **The check judges the form and nothing else,** through a new helper for checks,
  `chart_forms(ax)` in `tools/runner.py`, which the browser shares. It reads the objects that a
  chart leaves on an Axes and names fourteen forms. For each question the check accepts every
  honest form and rejects bars of a mean, a line from one species to the next and a pie, each
  with a hint that says why. The fallback of the plan, naming the forms in a dictionary, was not
  needed.
- **What the helper cannot name:** a frequency polygon (`element="poly"`) reads as a line, so a
  learner who draws one for a question about spread is told "I can't tell which form this is",
  with the forms the check does know. Eight or more bars drawn by hand on a numeric axis read as
  a histogram. Neither is taught in the course.
- **Tests:** 29 attempts go through the check, of which 17 must each earn their hint and 12 are
  other honest forms that must pass. The helper has a test of its own, on 26 charts.
- **Tried in Chrome,** where matplotlib is 3.8.4: the solution, the starter and the 29 attempts
  get the same verdict and the same message as in the build. It was a headless Chrome driven
  over the DevTools protocol, because the Claude extension was not connected.
- **The task** is "Short task - Questions only" in the assessment pack, after Assignment 3 in the
  file and before it in time. It lives in a new list, `tasks`, in `instructor/assignments.yaml`,
  and its rubric rows are T1 R1 to T1 R4 on the Evidence sheet, so the rows of the three
  assignments keep their numbers. Three new questions, 100 points: the form fits the question
  (45), a reason is given (20), a form is ruled out with a reason (20), the question and the
  labels are on the chart (15). Its model answer is run by the build, like every other.
- **One departure from the plan:** the fourth rubric row is mapped to S09 and to S02, not to S09
  alone, because its full-credit text asks for plain labels with units as well.
- **The map:** S09 is Covered. Its 20 minutes moved from "to write" to "additions built".
  Section 1's project time is 7.0 hours with the half-hour task (it was 6.5), so the guide's
  totals are 17.0 hours for section 1 and 57.9 in all. The map is version 1.5.
- **The rule-1 test** names the pair S11 and S09 as the one that was decided (question 10), and
  fails on any other.
- **Left for step E:** the check questions of the "which chart answers this?" kind, and a second
  set of three questions for the task.

What the plan said:

There are two pieces, because S09 is shown by a rubric task, and a status of Covered also asks
for one checked exercise.

- **On the page** (Lesson 7, after Step 1): three questions about the penguins, none of them
  among the four in Step 1's table. For each, the learner draws one panel in a form that
  answers it. The check judges the form and nothing else. It accepts every honest form for the
  question (for a distribution: a histogram, a density curve, an ECDF, a box plot or a strip
  plot) and rejects the misleading ones that S09 names (a line across unordered categories,
  bars of a mean where zero means nothing, a pie). Telling a form from the objects on the Axes
  is the hard part, so this needs about a dozen near-miss tests. If the check proves too loose,
  the fallback is for the learner to name each form in a dictionary, which is easy to check
  and close to a quiz question.
- **As a task** (after Lesson 7, in the assessment pack): three new questions. The learner
  draws each chart, and writes one sentence for the choice and one for a form ruled out. Its
  rubric rows (the form fits the question, a reason is given, a misleading form is ruled out
  with a reason, the charts are labeled) map to S09. That gives S09 its rubric rows, and a
  second set of questions gives its mastery check (step E).
- **The map:** the exercise and the rubric rows are listed for S09, which becomes Covered.
  S09's 20 minutes to write become minutes that exist. "Every assignment names its chart types"
  stops being true, in S09's gap and in the guide.
- **With it:** `test_three_assignments_increasing_and_rubrics_total_100` asserts three
  assignments whose solutions grow in size, so it must learn about a short fourth task; the
  README's "3 assignments"; both editions of the assessment pack; the guide's "Assignments"
  section, the project hours (6.5, or 7.0 with a half-hour task) and every total that follows
  from them; the count of rubric rows; the pinned statuses and the rule-1 list in
  `tests/test_objectives.py`; the guide's paragraph on S09 under "Where the pages fit".
- **Check questions** of the "which chart answers this?" kind belong to step E, not to the
  page. Quiz L3 Q3 and L7 Q3 are the models.

### Step D. "Describe and deliver" (S12 and S14)

Step 2 of the guide. About 8 to 10 hours. Needs questions 2, 6, 7 and 8.

- **The section** (Lesson 7, Step 5, after the pre-flight checklist): save the report as a PNG
  at 200 dpi with nothing cut off, and as a vector file where it must stay sharp at any size;
  open the file and look at it; restart the notebook and run it top to bottom; then write the
  figure's alt text and a one-sentence caption, with any caveat that changes the reading. It
  shows two short examples of alt text: one that describes the chart, and one that only names
  it.
- **The exercise** saves the learner's figure and fills two variables, the alt text and the
  caption. The check opens the saved file and reads its resolution, and tests the shape of the
  words: long enough to say something, short enough to be read aloud, and not a repeat of the
  title. It cannot judge whether the words are true. The rubric rows do that.
- **The rubric:** an "Alt text and caption" row, mapped to S14 (question 7).
- **The builder must change first.** A cell that calls `fig.savefig("name.png")` writes into
  the folder the build runs in, which is the repository (tried: the file appeared there). So
  `runner.run_cell` has to run each cell and its check in a temporary folder, and come back
  afterwards, in the build and in the browser alike, since both use the same file. Two things
  to watch. In the browser the dataset is found by a relative path, which must be resolved
  before the folder changes. And a PNG saved at 200 dpi reports 199.9996 when it is read back,
  so the check has to round. `tests/test_runner.py` gets a test that a cell which saves a file
  leaves nothing behind.
- **The map:** the new section teaches S12 and S14, and the exercise is listed for both. Both
  become Covered, and with step C all fourteen are. Lesson 7 gains two goals, so the 30 lesson
  goals become 32. The 10 and 15 minutes to write become minutes that exist. "Saving your work"
  in Lesson 6 stays where it is.
- **With it:** the pinned statuses, and that test's sentence that no page teaches S14; the
  guide's table, its paragraphs on S12, on S14 and on "Planned", and step 2 of "Next steps";
  the count of rubric rows; Lesson 7's notes in the guide; the notebooks, where the saved file
  lands beside the notebook.

### Step E. The mastery checks

Step 3 of the guide. Tooling 4 to 6 hours, questions 25 to 35 hours, tasks about 8 hours. Needs
questions 1, 3, 4 and 9, and O12 and O13. It is built last, because a check is written for an
objective as its pages teach it, and steps A to D change what five objectives' pages teach.

- **Size.** Nine objectives are shown by questions (S01 to S08, and S13): two forms of five
  questions each is 90 questions. Five are shown by a task (S09, S10, S11, S12 and S14): two
  forms of each is ten tasks, each with rubric rows mapped to its objective alone.
- **Format.** A question is written like an exam question (stem, four options, answer and
  explanation), with its objective and its form. A task is written like an assignment, with a
  rubric and a model answer.
- **Here, in public:** the builder that turns a bank into a student sheet and an instructor
  sheet for one objective and one form; tests of the format (five or more questions for each
  objective and form, no question shared between two forms or with the public quizzes and
  exam, answers spread across A to D); and a manifest of counts, from which the workbook fills
  in what exists for each objective.
- **There, in private:** the questions, the tasks, their keys and their model answers.
- **Order of writing.** The objectives with no exam question first (S09, S11, S12 and S14, as
  tasks), then S02 (one exam question), then S01, S05, S08, S10 and S13 (two each), then the
  rest.
- **Timing.** A check is taken when the objective's exercises pass. S11's is taken after
  Lesson 7, where its prerequisite S09 is taught (O10).
- **With it:** rule 5 of the mastery rule ("With today's materials ...") is rewritten once
  checks exist. The YAML, the Read me sheet and the guide repeat the rule word for word, so all
  three change together. The exam stays as it is, as the check at the end of the section.

## Order

1. The decisions: questions 1 to 10, and O11 to O13. Done on 2026-11-15. Question 3's answer (an
   honor system for now) leaves two things open: see the question.
2. Step A, then step B. They are small, and they change Lesson 6 only. Both are built.
3. Step C, then step D. They change Lesson 7, the assessment pack and the runner. Step C is built.
4. Step E, in stages, starting where the exam is thinnest.

L24 and L25 in `REVIEW.md` (three exercise checks that passed what their brief rules out) were
not part of this plan. They were closed on 2026-11-15, with the decisions.

## Places that hold a number

A new exercise, rubric row or assignment changes numbers that are written down in several
places. The tests fail until they agree, which is the point:

- `README.md`: the figures, the exercises and the assignments under "What's inside".
- `content/instructor-guide.md`: "Where the pages fit" (the counts in its first paragraph, the
  table, the paragraphs on Partial and Planned), "Timings" (the table and its notes) and "Next
  steps".
- `instructor/mastery_objectives.yaml`: `lesson_minutes`, `added_minutes`, `lesson_goals`,
  `page_map` and `evidence`, and each objective's `to_write`, `gap` and `next_step`.
- `tests/test_objectives.py`: the statuses, the exercises that rule 1 counts, the exam's thin
  spots, and the 65 minutes of additions.
- `tests/test_materials.py`: three assignments and one short task, each with a rubric that totals
  100, and the count of model solutions and task lists in the Word pack.
- `tests/test_site.py`: the lists of exercises that must reject raw column names and seaborn's
  default colors.

## What was tried for this plan

On 2026-11-15, without changing the repository:

- Step A's check, on four charts, under matplotlib 3.10.6 (see step A).
- A cell that saves a file during a build: the file lands in the repository folder (step D).
- Exercise 7.1 listed for S09, on a copy of the map: the condition of the rule-1 test fails for
  S11 (question 10).

Nothing else here was run for the plan. Since then, the checks of the steps that are built
have been tried in the browser: see each step.
