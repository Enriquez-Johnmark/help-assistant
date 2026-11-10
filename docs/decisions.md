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
- **B2 clarified:** an answer may repeat the customer's own figures from their question ("sending ₱3,000 costs ₱35"); any other figure must be on a cited page.

## 2026-11-08

- **Keyword search by default:** the recorded run on the 150 test questions met the targets (F2) with keyword search alone (Haiku 88% right answers, 92% right page; Sonnet 86%, 91%) and missed them with keyword and embeddings combined (Haiku 83%, 89%; Sonnet 84%, 89%), losing mostly on Tagalog questions. `serve`, `ask`, `search` and CI's F2 check now use keyword search; combined search stays an option (`--mode combined`) and stays in the report (F3). Not tuned further on the test set, so it stays an honest measure.

## 2026-11-10

- **UI polish with `ui-taste`:** Uizze's `ui-taste` skill (v0.3.0, Apache-2.0) is added, pinned and recorded, without the paid Uizze MCP. Every product gets an audit (look only, with real desktop and phone screenshots), then a polish pass that keeps its current look, one product at a time: Lab Report Assistant, Kompleto, Balanse, Review Triage Agent, Help Assistant, then the portfolio; each product's screenshots, video and portfolio page are remade before the next starts. Every rule that protects an acceptance criterion stays in code, and every test must still pass (owner: "yes to all").
