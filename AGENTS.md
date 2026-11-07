# AGENTS.md

**Help Assistant** is an AI assistant that answers customers' questions about a money-services company's services from that company's own help pages, in Taglish, Tagalog or English, and hands off to a person when it isn't sure. It works for any such company; the demo uses a **made-up company, Halimbawa Money**, and the repository names no real company. Working name; it may be renamed.

## Phases

Each gate needs the owner's explicit "yes"; an approval for one phase never carries into the next.

| Phase | Status |
| --- | --- |
| 1. Brief | done, approved 2026-11-07 (`docs/product/brief.md`) |
| 2. Spec & acceptance criteria | done, approved 2026-11-07 (`docs/product/spec.md`, 27 criteria) |
| 3. Architecture | done, approved 2026-11-07 (`docs/architecture.md`) |
| 4. Build | **in progress**: M1 (help pages, search), M2 (secrets, answer checks), M3 (answering, hand-off) and M4 (test set, evaluation) done; M5 (chat page, staff views) next (`docs/architecture.md`) |

Code follows the build order in `docs/architecture.md`, one milestone at a time; each ends with a code review.

## Owner decisions

Every decision needing the owner's judgement is put as numbered rounds of questions, each with a recommended answer, worded so "yes" accepts it. Record every approved decision, dated, in `docs/decisions.md`.

## Rules

- **No real company.** No real company's name, branding, figures or help content anywhere in the repository; the help pages, fees and test questions are made up, and each says so (A3).
- **Answers come only from the help pages.** Every citation and every number in an answer is checked in code; a failed check gives "I don't know", never a guess.
- **Secrets never travel.** PINs, OTPs, passwords, card and account numbers are hidden before anything is stored or sent to the model.
- **Model output is untrusted.** Every answer is parsed into strict types and checked by rules before a customer sees it.
- **API key only.** The Claude API through the owner's key, never a Claude subscription; no data to free model tiers that train on inputs.
- **Time** is read only through the injected `Clock`; ruff bans direct system-clock calls.
- **Tests:** every acceptance criterion has a test whose name starts with its ID, e.g. `test_c3_no_secret_reaches_the_model_or_the_logs`.
- **Before every commit:** `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright` and `uv run pytest` pass.
- **Report test results only from commands actually run.**
- **Small commits** on `main`, each one behaviour or one doc change; messages imperative; no AI attribution trailers (owner's choice). Commits are signed, so GitHub shows them as verified.
