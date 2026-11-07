# Architecture

Status: **approved by the owner** (2026-11-07). The spec is `product/spec.md`; this says how it is built.

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

## Search, as measured

On 25 made-up Taglish and Tagalog questions (one per help page), the right page was in the top 5:

| Setting | Right page in the top 5 |
| --- | --- |
| Keyword search alone, plain | 17 of 25 |
| Keyword and the local model, combined (lists 20 deep) | 19 of 25 |
| The same with a model four times larger | 20 of 25 |
| Adding a Tagalog glossary to keyword search | 22 of 25 |
| The glossary, light English stemming, and lists 5 deep before combining | **24 of 25** |

- **The Tagalog glossary** (`search/glossary.py`) adds the English for common Tagalog money words (padala, sangla, tubos, alahas, kuryente…) to a question's keyword search: small embedding models know few of them. It is one list for every question, matched at the start of a word or after a Tagalog prefix.
- **Light stemming** lets "fees", "cancelling" and "arriving" match "fee", "cancel" and "arrive".
- **Shallow lists:** combining only each search's top 5 worked better than 10 or 20, where weak matches crowded out strong ones.

These were chosen on the same 25 questions, so the test set (M4), written separately, is the real measure; its report gives keyword and combined search side by side (F3).

## Secrets and the answer checks, as built

- **Hiding secrets** (`core/secrets.py`) runs in order: emails, mobile numbers, long numbers (a card if it passes the Luhn check and is 16 digits, grouped or called a card; otherwise an account number), PINs and OTPs near a word like "PIN", "OTP" or "code" (or a message that is only a code), then passwords after "password". Amounts, times, dates and reference numbers are kept.
- **`Redacted`** is a text type only `redact` can create; the store and the model client accept nothing else, so a customer's raw words can't reach them (C3).
- **Figures** in an answer must be on a cited page or in the customer's own question ("sending ₱3,000 costs ₱35"); "₱1,000", "1000" and "P1,000.00" count as the same figure, and number words in English and Tagalog are read as digits.
- **Promises** are about the customer's own case ("we will refund you", "ibabalik po namin"); policies quoted from a page ("the amount is returned in full") are not. **Asking for a secret** means a request whose object is the secret ("send me your PIN"); "never share your PIN" and "confirm with your PIN" pass.

## Answering and hand-off, as built

- **Hand-off rules** (`core/handoff.py`) run before the model: asking for a person; money lost or stolen (a loss word within three words of a money word, so "I lost my pawn ticket for my 5000 loan" is answered); or the customer's own account or transaction with something only a person can look up (a reference number, a date, a status, a charge, a hold). General "what do I do if…" questions are answered.
- **The model** can also hand off, by its `handoff` field; an answer that doesn't parse, even one the SDK rejects, is "I don't know".
- **Only the last six turns** go to the model with each question, all redacted, the assistant's and an agent's replies included.
- **Language:** English is told from Tagalog and Taglish by common words. Taglish that borrows only English nouns may read as Tagalog; a Tagalog or Taglish customer accepts a reply in either.

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

## The evaluation, as built

- **Search on the test set** (without a key): combined search finds the right page in the top 5 for 37 of the 40 Tagalog and Taglish questions (92%) and 59 of the 60 English ones; keyword search alone, 39 of 40 and 59 of 60. A2 is checked on these questions, which search wasn't tuned on.
- **Recordings:** `evalset/recorded/answers.json` (both models, both searches, keyed by the exact request) and `grades.json` (Claude Sonnet's grades, the 20 grading cases included). Recording again reuses what is there. A replay fails, with a message saying to re-record, if the prompt, the questions, the pages or the passages found changed.

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
