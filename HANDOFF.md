# Handoff: picking the work up on another machine

Written on 2026-11-15, at the end of the session that built steps C and D of `PLAN.md`, and
brought up to date on 2026-11-16 by the first session on the second machine, which set that machine
up and rechecked steps C and D cold (`REVIEW.md`, L31-L33, all left alone). Read `README.md`,
`REVIEW.md` and `PLAN.md` as well: this file adds what those three do not say.

## Where things stand

- `main` and `develop` hold the same files, and GitHub Pages serves `main:docs/`.
- Steps A, B, C and D of `PLAN.md` are built. Step E, the mastery checks, is not started.
- Steps C and D were rechecked cold on 2026-11-16: 86 attempts at exercise 7.2 and 44 at 7.3
  beyond their tests, the runner's temporary folder under CPython and in the browser, both Word
  editions, the Timing sheet against the guide, and the browser run and widths. Nothing needed a
  fix. Three Low findings were written down and left alone (`REVIEW.md`, L31-L33).
- Both machines are set up. The second has no Anaconda: its `.venv` is Python 3.14 with the pinned
  packages, and the suite, the builds and the browser check all pass from it.
- All fourteen static objectives are Covered. The objectives map is version 1.6.
- 17 exercises, 56 figures, 28 quiz questions, 25 exam questions, 32 lesson goals, 3 assignments
  and a short task with 23 rubric rows.
- The full suite has 124 tests.

## Setting up the other machine

1. Clone and take the working branch:

   ```bash
   git clone https://github.com/acatlin/seaborn-penguins.git
   cd seaborn-penguins
   git checkout develop
   ```

2. Python 3.13 with the pinned packages. The pins matter: the tests compare the built site with
   the committed one.

   ```bash
   python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install websocket-client                          # only for tools/browser_check.py
   ```

   On the first machine this was Anaconda's Python, whose packages matched the pins. Any Python
   with the pinned packages does: the second machine runs them on Python 3.14.4 from
   `C:\Python314`, in the repository's `.venv`, and all 124 tests pass. On Windows, use
   `.venv\Scripts\python.exe` in place of `python` throughout, and paste the two lines above one
   at a time: pasted together into PowerShell, they once created two empty venvs named `#` and
   `Python` in the repository root (git ignored them, because `venv` writes its own `.gitignore`).

3. The GitHub CLI, signed in as the owner of the repository (`gh auth login`). Pull requests,
   their checks and the merges all go through `gh`.

4. Chrome, for the browser check. No extension is needed: `tools/browser_check.py` starts a
   headless Chrome of its own.

5. Confirm the state before any edit. All four should hold:

   ```bash
   git status --short                      # prints nothing
   git diff origin/develop origin/main --stat   # prints nothing
   python -m pytest -q                     # 124 passed, in about 3 minutes
   python tools/build_site.py && git status --short docs/   # prints nothing: see "Figures" below
   ```

Word and Excel are not needed to build anything: the `.docx` files and the workbook are written
by python-docx and openpyxl. They were used on the first machine only to look at the output as
Word and Excel draw it.

## What does not travel with the repository

- **The notes Claude Code kept on the first machine.** They held the rules of work and a few
  hard-won facts. Both are written out below, so nothing is lost.
- **The scratch scripts of earlier sessions.** The one worth keeping is in the repository now:
  `tools/browser_check.py`.
- **A private companion repository for the mastery checks** (`PLAN.md`, question 1). It does not
  exist yet. It is made with step E.

## Rules of work

- Feature branches go off `develop`, and each pull request goes into `develop`. `main` is
  protected: the `test` check must pass.
- **Do not merge to `main` or publish without asking.** Each go-ahead so far covered one publish.
- To publish, once told to: merge the feature pull request into `develop`, open one from
  `develop` into `main`, wait for `test`, merge with a merge commit. Pages rebuilds in about half
  a minute. Then compare every file under `https://acatlin.github.io/seaborn-penguins/` with
  `origin/main:docs/`.
- Never edit by hand: `docs/`, the `.docx` files, the `.xlsx` workbook. Edit the sources and
  rebuild.
- After any edit: `python tools/build_site.py`, `python tools/build_materials.py`, then the full
  suite.
- After a change to a lesson, an exercise or the stylesheet: `python tools/browser_check.py run`,
  then `widths`, and for a change of layout a `snapshot` before and after and a `compare`.
- A change to a lesson, an exercise, a question or a rubric row changes the map
  (`instructor/mastery_objectives.yaml`), the instructor guide, `README.md`, `REVIEW.md` and
  `PLAN.md` in the same pull request. The tests fail until the numbers agree, which is the point.
- Plain slips are fixed and reported. A judgment call is not changed: it is listed, with a
  recommendation.
- An exercise's number is never reused or moved. Neither is an objective's code.
- The objectives and the guide name Dash at most once, as the alternative. A test holds this.
- No mastery-check question or answer key goes into this repository. It is public.
- `REVIEW.md` lists findings by id (H, M, L) and questions for the instructor (O), each with a
  status. A finding outside the task at hand is written there as "left alone", not fixed in
  passing.

## Things that have bitten before

- **Figures.** A PNG's bytes depend on the machine that drew it, so the tests check only that
  each figure exists. If `build_site.py` on the new machine marks every file in `docs/img/` as
  changed although no lesson was touched, the machine draws them differently (other fonts, for
  one). Then commit only the figures whose code changed, and restore the rest with
  `git checkout -- docs/img/NAME.png`. The first machine draws in Arial, and the browser in
  DejaVu Sans. On the second machine this happened as predicted: a build marks all 56 figures and
  nothing else, so after a build there, `git checkout -- docs/img` before reading `git status`.
- **An old prompt.** The prompt at the end of this file is replaced each session. The one from
  two sessions back was pasted once by mistake; its state lines failed at once (other commit ids,
  119 tests, "steps A and B are built"), which is what they are for. Stop when they fail.
- **Word files.** `build_materials.py` rewrites all three `.docx` with new timestamps even when
  nothing changed. Before a commit, restore the ones whose parts are unchanged
  (`git checkout -- instructor/NAME.docx`). To tell: unzip the old and the new file and compare
  the parts. The workbook has no such problem: its build is reproducible.
- **Line endings.** The first machine is Windows with `core.autocrlf=true`, and the tests fold
  line endings before they compare. A tool that rewrites a file with other endings leaves no
  diff in git, but `sed -i` once rewrote a whole file that way. Check before a scripted edit.
- **Two runtimes.** The suite runs CPython with matplotlib 3.10. The browser runs Pyodide with
  Python 3.12 and matplotlib 3.8.4. A check that passes in the suite is not yet known to pass
  in the browser: `tools/browser_check.py run` is the test of that.
- **A new number is written down in several places.** `PLAN.md` lists them under "Places that
  hold a number".

## Open decisions

Each is written where its question is, with what was recommended.

| Where | Question | State |
|---|---|---|
| `PLAN.md`, question 3 | How a learner takes a mastery check | Answered on 2026-11-15: an honor system for now, web pages with a database later. Two things are open under it: where a learner gets a check and its key, and who scores it |
| `REVIEW.md`, O12 | A notebook has no automatic check: leave rule 1 as it is, or record passes in the browser | Not decided |
| `PLAN.md`, step B | Fold the page's own list of faults away under exercise 6.4, or leave it in plain view | Not decided. It is in plain view |
| `REVIEW.md`, L27 | "afterwards" (Lesson 6, and D05 in the map) and "backwards": leave, or change to -ward | Not decided. They are left |
| `REVIEW.md`, L29 and L30 | Exercise 6.4 turns away an honest sentence of under 20 characters, and recognizes faults from letters inside other words | Left alone. Recommended: count words, and match whole words |
| `REVIEW.md`, L31 | Exercise 7.2 misreads four honest forms the lessons do not teach (frequency polygon, hexbin, markers-only `plot`, a colorbar as a fourth panel) | Left alone. Recommended: leave; if any, read a markers-only line as a scatter |
| `REVIEW.md`, L32 | Exercise 7.3 names a folder as a file, passes another letter case on Windows only, and gives the generic line for a file that is not an image | Left alone. Recommended: quote the names, list files only, catch the Pillow error |
| `REVIEW.md`, L33 | Exercise 7.3 turns away an honest alt text of 11 words and a caption of 7 | Left alone. Recommended: leave the floors (12 and 8) |
| `PLAN.md`, step C | The short task's fourth rubric row is mapped to S09 and S02, where the plan said S09 alone | Done that way. Say so if S09 alone is wanted |
| `PLAN.md`, step D | The guide now says to plan the capstone as two sessions, since 45 added minutes fall in Lesson 7 | Added by the builder, not asked for |

## Before step E

Step E writes about 90 questions and 10 tasks, which is most of the hours in the plan. It needs
these from the instructor first:

1. **The two things question 3 left open.** Under an honor system, does a learner get the key
   and score the check, or hand the answers in? And where do the check and the key come from,
   since neither may be in this repository?
2. **The private companion repository** (question 1): its name, and a go-ahead to create it.
3. **The format of the bank.** Recommended: questions and tasks as YAML, like the exam and the
   assignments, in the private repository. Word sheets are built from it now, and the web pages
   with a database can be fed from the same files later.
4. **The second form** (question 9): penguins again, or a second dataset. Only the first form
   was decided.
5. **Where to start and how to review.** Recommended: the tasks for S09, S11, S12 and S14 first
   (the exam has no question on them), then S02, and a first batch for one objective to read
   and correct before the other 80 questions are written.

## The prompt for the next session

Paste this into a new Claude Code session, started in the repository's folder. Fill in the
decisions. Keep the lines short: a long line was once cut off when pasted.

```text
Read README.md, REVIEW.md, PLAN.md and HANDOFF.md
before anything else. PLAN.md is the plan.
Steps A to D are built and rechecked. Step E
is not started.

STATE TO CONFIRM FIRST. Stop and tell me if a
line fails.
- Clean tree on develop. No open PR.
- develop and main hold the same files:
  git diff origin/develop origin/main --stat
  prints nothing.
- Full suite: 124 passed. On this machine run
  Python as .venv\Scripts\python.exe.
- Every file under origin/main:docs/ is
  identical to the live site.
- mastery_objectives.yaml: version 1.6.
- 17 exercises, 56 figures.
- REVIEW.md ends its Low findings at L33.

TASK 1. MY DECISIONS. Blank = not decided.
  Q3a  who scores a check ........ [ ]
       (learner with the key / instructor)
  Q3b  where check and key live .. [ ]
  repo private repo: name ........ [ ]
       may you create it? ........ [ ]
  bank YAML in the private repo .. [ ]
  Q9   second form's dataset ..... [ ]
  O12  notebook, no auto check ... [ ]
  6.4  fold the list of faults ... [ ]
  sp   -wards spellings .......... [ ]
  L29  6.4: count words .......... [ ]
  L30  6.4: whole words .......... [ ]
  L31  7.2: markers-only scatter . [ ]
  L32  7.3: names, case, Pillow .. [ ]
  L33  7.3: word floors .......... [ ]
Record each where its question is written,
with the date. A decided fix is a small PR of
its own, with a near-miss test, before step E.

TASK 2. STEP E, FIRST STAGE ONLY.
- The tooling in this repository: builder,
  format tests, a manifest of counts.
- The first batch in the private repository:
  [say which objective].
- Stop there and show me the batch.

RULES
- HANDOFF.md, "Rules of work".
- Do not merge to main or publish without
  asking.
- No mastery-check question or answer key in
  the public repository.
- If a line of this prompt looks cut off,
  work from its sense and tell me how you
  read it.

FINISH WITH: what changed for each decision;
what was built and how it was verified; the
judgment calls for me; what is left.
```
