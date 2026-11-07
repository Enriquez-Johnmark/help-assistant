# Help Assistant

**An AI assistant that answers customers' questions from a company's own help pages, in Taglish, Tagalog or English, and hands off to a person when it isn't sure.**

It is built for money-services companies (sending money, bills payment, pawning, e-wallets) and works for any of them, given their help pages. The demo uses a made-up company, Halimbawa Money, with made-up help pages; it is **not affiliated with any real company**.

Status: building. The [brief](docs/product/brief.md), [spec](docs/product/spec.md) (27 acceptance criteria) and [architecture](docs/architecture.md) are approved; the build follows the [roadmap](ROADMAP.md). M1 is done: 25 made-up help pages, read into passages, and a local search that finds the English page for 24 of 25 made-up Tagalog and Taglish questions. M2 is done: PINs, OTPs, card and account numbers, passwords, mobile numbers and emails are hidden however they are typed, and code refuses answers that cite pages search didn't find, state figures their pages don't, promise outcomes or ask for a secret. M3 is done: Claude answers from the passages found, in the customer's language, through the owner's API key (or recorded answers in tests); a person takes over when the customer asks, when it's about their own account or lost money, or after two "I don't know"s. M4 is done: a test set of 150 made-up questions in five groups (English, Tagalog and Taglish, not in the pages, own-account, tricky), graded in code and by Claude, with a report comparing Haiku and Sonnet and keyword and combined search; the scores are added once recorded with the owner's key.

```sh
uv sync
uv run help-assistant index                                   # the help pages into data/help.db
uv run help-assistant search "Paano mag-sangla ng alahas?"    # the passages a question finds
uv run help-assistant ask "Magkano ang fee pag nagpadala ng 3,000?"   # an answer (needs ANTHROPIC_API_KEY in .env)
uv run help-assistant eval --record                          # the test set with Claude (needs the key)
uv run pytest
```

The first search downloads a small multilingual model (about 240 MB) into `data/models`.

MIT ([LICENSE](LICENSE)).
