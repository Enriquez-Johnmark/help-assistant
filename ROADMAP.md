# Roadmap

Where the Help Assistant stands and what comes next, in one page. The milestones come from `docs/architecture.md`; decisions, dated, from `docs/decisions.md`. Updated 2026-11-07.

## Where we are

**M1 to M4 done; M5 next.** The brief, the spec (27 acceptance criteria) and the architecture are approved.

| Milestone | Delivers | Criteria | Status |
| --- | --- | --- | --- |
| M1 | Setup, the made-up help pages, reading them into passages, keyword and embedding search | A1–A3 | Done (2026-11-07), code-reviewed |
| M2 | Hiding secrets and the answer checks | B1, B2, B5, C1–C3 | Done (2026-11-07), code-reviewed |
| M3 | Answering with Claude, the language check, hand-off | B3, B4, B6, D1–D5 | Done (2026-11-07), code-reviewed |
| M4 | The test set, the evaluation, Claude's grading, the report | F1–F4 | Done (2026-11-07), code-reviewed; scores wait for the owner's key |
| M5 | The chat page, the agent's and the owner's views, the audit log | E1–E4, G1, G2 | **Next** |
| M6 | Live scores, README, screenshots, walkthrough video | — | |

Each milestone ends with a code review, with its findings fixed.

## What needs the owner

- **Any time:** try it live with your key in `.env`: `uv run help-assistant ask "Magkano ang fee pag nagpadala ng 3,000?"`.
- **Now possible:** run the evaluation with the Anthropic API key in `.env`: `uv run help-assistant eval --record`. It asks Claude Haiku and Sonnet every test question with both searches, has Claude grade the answers and the 20 grading cases, prints the report, and saves everything to `evalset/recorded/`. Commit that folder: CI then checks the targets (F2) and the grader (F4) without a key. Re-recording later asks only what changed.

## Limits that never move

No real company, figure or customer data; answers only from the help pages; secrets hidden before anything is stored or sent; a person takes over whenever the assistant isn't sure.
