# Seaborn with Penguins: notes for Claude Code

Read `HANDOFF.md` before anything else. It holds the rules of work, the setup of a new machine,
the things that have bitten before, the open decisions and the prompt for the next session.

Then read `README.md` (what the repository is and how it builds), `REVIEW.md` (every finding
and every question for the instructor, each with its status) and `PLAN.md` (what is built and
what is not).

The rules that matter most, all from `HANDOFF.md`:

- Work on a feature branch off `develop`, and open the pull request into `develop`.
- Do not merge to `main` or publish without asking. Each go-ahead covers one publish.
- Never edit by hand: `docs/`, the `.docx` files, the `.xlsx` workbook. Edit the sources, then
  run `python tools/build_site.py`, `python tools/build_materials.py` and the full suite.
- No mastery-check question or answer key goes into this repository. It is public.
- Do not start a step of `PLAN.md` until told to.
- Keep `HANDOFF.md` current at the end of a session: the state, the open decisions and the next
  prompt.
