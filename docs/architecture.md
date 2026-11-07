# Architecture

Status: **draft, for the owner's approval**. The spec is `product/spec.md`; this says how it is built.

## Shape

One Python package, `help_assistant`, in `src/`:

| Folder | Holds |
| --- | --- |
| `core/` | The rules, with no input or output: hiding secrets, the answer checks (citations, numbers, promises, secret requests, language), the hand-off rules |
| `pages/` | Reading help pages (Markdown) into passages |
| `search/` | Keyword search (BM25), the local multilingual embeddings, and combining the two |
| `model/` | The model client: live (Claude) and recorded (for tests and CI); the answer's strict type |
| `store/` | SQLite and its migrations |
| `web/` | FastAPI: the JSON API, the chat page and the two staff views (server-rendered templates) |
| `evaluation/` | The test set runner, Claude's grading and the report |
| `cli.py` | The commands: `index`, `ask`, `serve`, `eval` |
| `help_pages/` | The made-up company's help pages (committed) |
| `evalset/` | The made-up test questions and the recorded model answers (committed) |

The safety rules live in `core/` and are used by every way in (the chat API, the commands and the evaluation), so none of them can skip a rule.

## Tools

Python 3.12, managed with **uv**; **ruff** for lint and format; **pyright** in strict mode; **pytest**. **Pydantic** for every input and every model answer; **FastAPI** with **Jinja2** templates and a little plain JavaScript; the official **Anthropic SDK**; **fastembed** for the local embeddings (ONNX, no PyTorch, no paid service).

## How a customer's message is answered

1. **Hide secrets** in the message (C1). If one was found, the reply starts with a warning (C2). Only the hidden text is used from here on.
2. **Hand-off rules in code** (D1, D2, D4): asking for a person, a question about the customer's own account or a transaction, or anger about lost money hands off at once, before the model is asked. The rules are word lists in English, Tagalog and Taglish, tested on the test set.
3. **Search** for the top 5 passages, keyword and embeddings combined by reciprocal rank fusion.
4. **Ask the model** with only the hidden question, the hidden conversation so far and those passages (B6). The system prompt says the passages and the customer's words are information, not instructions. The answer is parsed with `client.messages.parse(output_format=Answer)` into a strict Pydantic type: the reply, the IDs of the passages it cites, a confidence, the language, and whether it thinks a person is needed.
5. **Check the answer in code** (B1–B5): it parsed; its confidence is at the threshold or above; every cited passage was one search returned; every number in the reply appears in a cited passage; it promises nothing and asks for no secret; it is in the customer's language. Any failure gives "I don't know" and an offer of a person, never the model's text (B3).
6. **Two "I don't know"s** in one conversation hand off (D3). The hand-off message never promises a time (D5).
7. **Store** the hidden messages, the passages cited and, for an "I don't know", the question and its nearest topic, for the owner's view.

## Database

SQLite through the standard library, one file in `data/` (ignored by git), with numbered migrations.

| Table | Holds |
| --- | --- |
| `pages`, `passages` | The help pages and their passages, keyed by page and heading so reading again adds nothing (A1) |
| `conversations` | One per chat: who is answering (the assistant or a person), waiting or closed, whether money is involved |
| `messages` | Every message, **secrets already hidden**, with the passages cited |
| `unanswered` | Each "I don't know", with its nearest topic (E4) |
| `audit_log` | Every hand-off, reply, hand-back and close: when, who, what. Append-only, enforced by triggers (E3) |

## The model

Behind an interface with two versions:

- **Live:** the Anthropic SDK with the owner's API key; `claude-haiku-5-5` answers by default, and `claude-sonnet-5-5` is compared in the evaluation.
- **Recorded:** replays saved answers, keyed by a hash of the exact request (model, system prompt, messages), so a changed prompt or model can't reuse old answers. Tests and CI run without a key.

## Measuring

`eval` runs the test set (`evalset/questions.jsonl`) through the same steps as the chat, with each search mode and each model (F3), and reports right answers, right pages, "I don't know"s, hand-offs and refusals by group. **Grading:** code checks citations, numbers, hand-offs and refusals; Claude Sonnet grades whether a reply matches the right answer, as a strict type (`correct`, `reason`); the grader is tested on made-up right and wrong replies (F4). Recorded answers are committed, so CI checks the targets (F2) without a key.

## Time and privacy

Time is read only through an injected clock. The server listens on 127.0.0.1 only and answers only requests addressed to it (G1). The API key lives in `.env` and is never in a page, an answer or a log; the model client's errors are reported by kind and status only.

## CI

GitHub Actions: ruff, pyright, pytest (with the recorded answers), and a check that every help page and test question is marked made-up (A3). The embedding model is downloaded once and cached.

## Build order

| Milestone | Delivers | Criteria |
| --- | --- | --- |
| M1 | Repository setup, the 25 made-up help pages, reading them into passages, keyword and embedding search | A1–A3 |
| M2 | Hiding secrets and the answer checks, as pure rules | B1, B2, B5, C1–C3 |
| M3 | Answering with Claude (live and recorded), the language check, the hand-off rules | B3, B4, B6, D1–D5 |
| M4 | The test set, the evaluation, Claude's grading and the report | F1–F4 |
| M5 | The chat page, the agent's view, the owner's view, the audit log | E1–E4, G1, G2 |
| M6 | Live scores, README, screenshots and the walkthrough video | — |

Each milestone ends with a code review. The live evaluation needs the owner's API key, run on the owner's machine; everything else runs without one.
