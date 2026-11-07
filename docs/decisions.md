# Decisions

Every decision the owner made, dated.

## 2026-11-07

- **Build it:** a second portfolio project for AI engineering roles, beside the Review Triage Agent: an AI assistant that answers customers' questions about a money-services company's services from its own help pages, in Taglish, Tagalog or English, and hands off to a person when unsure.
- **Generic:** the repository names no real company; the demo uses a made-up company with made-up help pages.
- **Working name:** Help Assistant (repository `help-assistant`).
- **Language:** Python, so the portfolio shows Python beside TypeScript and Rust.
- **Licence:** MIT.
- **Commits:** signed, so GitHub shows them as verified.
- **Brief:** approved (`docs/product/brief.md`).
- **Spec Round 1** (`docs/product/spec.md`): a made-up company, Halimbawa Money, with about 25 made-up help pages; English pages, answers in the customer's language; local keyword and multilingual search, both measured; Claude Haiku answers, Sonnet compared; citations and every number checked in code, else "I don't know"; secrets hidden before storing or sending.
- **Spec Round 2:** hand-off on request, own-account questions, two "I don't know"s or upset about lost money, never promising when; an agent's view with replies, hand-back and close, all logged; an owner's view of unanswered questions and hand-offs by reason; a test set of about 150 made-up questions in five groups with targets (85% right, 90% right page, 100% on secrets and own-account hand-offs), run in CI from recorded answers; FastAPI with server-rendered pages, SQLite, 127.0.0.1 only; Python 3.12, uv, ruff, pyright, pytest.
- **Spec Round 3:** 27 acceptance criteria (A1–G2); the spec is complete.
- **Architecture** (`docs/architecture.md`): one Python package with the rules in `core/`; local BM25 and fastembed search combined by reciprocal rank fusion; Claude answers parsed into a Pydantic type and checked in code; SQLite with an append-only audit log; recorded model answers for tests and CI; build order M1–M6.
