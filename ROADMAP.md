# Roadmap

Where the Help Assistant stands and what comes next, in one page. The milestones come from `docs/architecture.md`; decisions, dated, from `docs/decisions.md`. Updated 2026-11-08.

## Where we are

**All six milestones done.** On the 150 test questions Claude Haiku with keyword search gives 88% right answers and 92% the right page, meeting the targets; the scores are in the README.

| Milestone | Delivers | Criteria | Status |
| --- | --- | --- | --- |
| M1 | Setup, the made-up help pages, reading them into passages, keyword and embedding search | A1–A3 | Done (2026-11-07), code-reviewed |
| M2 | Hiding secrets and the answer checks | B1, B2, B5, C1–C3 | Done (2026-11-07), code-reviewed |
| M3 | Answering with Claude, the language check, hand-off | B3, B4, B6, D1–D5 | Done (2026-11-07), code-reviewed |
| M4 | The test set, the evaluation, Claude's grading, the report | F1–F4 | Done (2026-11-07), code-reviewed; scores wait for the owner's key |
| M5 | The chat page, the agent's and the owner's views, the audit log | E1–E4, G1, G2 | Done (2026-11-07), code-reviewed |
| M6 | Live scores, README, screenshots, walkthrough video | — | Done (2026-11-08), code-reviewed; keyword search made the default (decisions, 2026-11-08) |

Each milestone ends with a code review, with its findings fixed.

## What needs the owner

- **Any time:** chat with it live: `uv run help-assistant serve`, then open http://127.0.0.1:8000 (the chat), `/agent` (support agents) and `/owner` (help content). Or try one question with your key in `.env`: `uv run help-assistant ask "Magkano ang fee pag nagpadala ng 3,000?"`.
- **After changing a prompt, a help page or the test set:** `uv run help-assistant eval --record` with the key asks Claude again for what changed only, and prints the report; commit `evalset/recorded/`, which CI checks without a key (F2, F4).
- **The walkthrough video** is `docs/showcase/walkthrough.mp4`; the portfolio page plays it.

## Limits that never move

No real company, figure or customer data; answers only from the help pages; secrets hidden before anything is stored or sent; a person takes over whenever the assistant isn't sure.
