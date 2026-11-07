# Help Assistant

**An AI assistant that answers customers' questions from a company's own help pages, in Taglish, Tagalog or English, and hands off to a person when it isn't sure.**

It is built for money-services companies (sending money, bills payment, pawning, e-wallets) and works for any of them, given their help pages. The demo uses a made-up company, Halimbawa Money, with made-up help pages; it is **not affiliated with any real company**.

Status: building. The [brief](docs/product/brief.md), [spec](docs/product/spec.md) (27 acceptance criteria) and [architecture](docs/architecture.md) are approved; the build follows the [roadmap](ROADMAP.md). M1 is done: 25 made-up help pages, read into passages, and a local search that finds the English page for 24 of 25 made-up Tagalog and Taglish questions.

```sh
uv sync
uv run help-assistant index                                   # the help pages into data/help.db
uv run help-assistant search "Paano mag-sangla ng alahas?"    # the passages a question finds
uv run pytest
```

The first search downloads a small multilingual model (about 240 MB) into `data/models`.

MIT ([LICENSE](LICENSE)).
