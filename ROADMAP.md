# Roadmap

Where the Help Assistant stands and what comes next, in one page. The milestones come from `docs/architecture.md`; decisions, dated, from `docs/decisions.md`. Updated 2026-11-07.

## Where we are

**M1 and M2 done; M3 next.** The brief, the spec (27 acceptance criteria) and the architecture are approved.

| Milestone | Delivers | Criteria | Status |
| --- | --- | --- | --- |
| M1 | Setup, the made-up help pages, reading them into passages, keyword and embedding search | A1–A3 | Done (2026-11-07), code-reviewed |
| M2 | Hiding secrets and the answer checks | B1, B2, B5, C1–C3 | Done (2026-11-07), code-reviewed |
| M3 | Answering with Claude, the language check, hand-off | B3, B4, B6, D1–D5 | **Next** |
| M4 | The test set, the evaluation, Claude's grading, the report | F1–F4 | |
| M5 | The chat page, the agent's and the owner's views, the audit log | E1–E4, G1, G2 | |
| M6 | Live scores, README, screenshots, walkthrough video | — | |

Each milestone ends with a code review, with its findings fixed.

## What needs the owner

- **M6:** run the evaluation once with the Anthropic API key in `.env` (`help-assistant eval --record`), so CI can check the scores without a key.

## Limits that never move

No real company, figure or customer data; answers only from the help pages; secrets hidden before anything is stored or sent; a person takes over whenever the assistant isn't sure.
