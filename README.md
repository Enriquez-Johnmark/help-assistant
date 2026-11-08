# Help Assistant

**An AI assistant that answers customers' questions from a company's own help pages, in Taglish, Tagalog or English, and hands off to a person when it isn't sure.**

It is built for money-services companies (sending money, bills payment, pawning, e-wallets) and works for any of them, given their help pages. The demo uses a made-up company, Halimbawa Money, with made-up help pages; it is **not affiliated with any real company**.

Status: building. The [brief](docs/product/brief.md), [spec](docs/product/spec.md) (27 acceptance criteria) and [architecture](docs/architecture.md) are approved; the build follows the [roadmap](ROADMAP.md). Milestones M1 to M5 are done and code-reviewed; M6 adds the live scores once they are recorded with the owner's API key.

![A customer types an OTP by mistake: it is hidden, they are warned and handed to a person, and an agent replies](docs/showcase/desktop-1-chat.png)

## What it does

- **Answers only from the help pages**, in English, Tagalog or Taglish, and links each answer to the page section it comes from.
- **Says "I don't know"** when the pages don't say, and offers a person; two "I don't know"s in one conversation hand off.
- **Hands off to a person at once**, in code before any model is asked, when a customer asks for one, asks about their own account or a transaction, or says money is lost.
- **Hides secrets**: a PIN, OTP, password, card or account number is hidden before anything is stored or sent to the model, and the customer is warned.
- **Never promises** a refund, an outcome or a date, and never states a fee the pages don't.
- **Shows staff what matters**: agents see waiting conversations with money issues first; the owner sees unanswered topics, hand-off reasons and an audit log that can't be changed.

| | |
| --- | --- |
| ![The agents' list, money issues first](docs/showcase/desktop-2-agents.png) | ![The owner's view: hand-offs by reason and the audit log](docs/showcase/desktop-4-owner.png) |

These screenshots use no model: each conversation is one the rules hand to a person before a model is asked ([how they were made](docs/showcase/README.md)).

## Why you can trust an answer

The model writes each answer; code decides whether a customer sees it. An answer is shown only if it parsed into a strict type, its confidence meets the threshold, every page it cites was one search found, every figure in it is on a cited page or in the customer's own question, it promises nothing and asks for no secret, and it is in the customer's language. Any failure gives "I don't know", never the model's text. The reasons are in the ADRs: [secrets are hidden first](docs/adr/0001-secrets-are-hidden-before-anything-else.md), [answers are checked in code](docs/adr/0002-answers-are-checked-in-code.md).

## How it is measured

- **A test set of 150 made-up questions** ([`evalset/questions.jsonl`](evalset/questions.jsonl)), written separately from the search tuning, each with its right answer and page: 60 English, 40 Tagalog and Taglish, 20 the pages don't answer, 15 about the customer's own account, and 15 tricky ones (secrets typed in, requests for a promise, instructions hidden in the question).
- **Targets** (F2): at least 85% of answers right, at least 90% citing the right page, and every own-account question handed off.
- **Grading:** code checks citations, figures, hand-offs and refusals; Claude Sonnet judges whether a reply says what the right answer says, as a strict type. The grader is itself tested on 20 made-up right and wrong replies (F4).
- **Compared** (F3): Claude Haiku and Claude Sonnet, each with keyword search alone and with keyword and embedding search combined.
- **Replayed in CI without a key:** the owner's run records every answer and grade, keyed by a hash of the exact request ([why](docs/adr/0003-recorded-answers-keyed-by-the-exact-request.md)); a changed prompt, page or search finds no recording and fails rather than reusing stale answers.

**Measured so far, without a key:** search finds the right page in its top 5 for 37 of the 40 Tagalog and Taglish questions (92%) and 59 of the 60 English ones with combined search, and 39 of 40 and 59 of 60 with keyword search alone. **The answer scores are not in yet:** they come from the owner's recorded run with Claude, and will be added here as measured, whatever they are.

## Running it

```sh
uv sync
uv run help-assistant index                                   # the help pages into data/help.db
uv run help-assistant search "Paano mag-sangla ng alahas?"    # the passages a question finds
uv run help-assistant ask "Magkano ang fee pag nagpadala ng 3,000?"   # an answer (needs ANTHROPIC_API_KEY in .env)
uv run help-assistant serve                                   # the chat at http://127.0.0.1:8000 (needs the key)
uv run help-assistant eval --record                          # the test set with Claude (needs the key)
uv run pytest
```

Everything except live answers works without a key: the tests use recorded and stand-in answers. In a Claude Code cloud session, set the key as the environment variable `OWNER_ANTHROPIC_API_KEY` instead, since Claude Code itself reads `ANTHROPIC_API_KEY`.

The first search downloads a small multilingual model (about 240 MB) into `data/models`.

MIT ([LICENSE](LICENSE)).
