# Tests and CI replay recorded answers, keyed by the exact request

The evaluation needs Claude's answers to 150 questions, with two models and two kinds of search, and Claude's grades of them. Asking live on every test run would need the owner's API key in CI and cost money each push. Instead, `eval --record` asks once, with the owner's key on their machine, and saves each answer under a SHA-256 of the exact request: the model, the system prompt and the messages, which include the passages found. CI replays them without a key (F2).

The deciding reason is that a recording must never pass for an answer to a different question. Keyed by the whole request, a changed prompt, model, help page or search result finds no recording, and the replay fails with a message saying to record again, rather than scoring stale answers.

## Considered options

- **Call Claude live in CI** with the key as a secret. Real scores every run, but a cost on every push and a key in a third place. Rejected.
- **Key recordings by question ID.** Simple, but a prompt change would silently reuse old answers and report scores the code no longer earns. Rejected.
- **Hand-written fake answers only.** Fine for unit tests (they still use them), but they measure nothing about the model. Kept for unit tests only.

## Consequences

- Recording again reuses the answers whose requests didn't change, so a small change costs only what it touches.
- Until the owner records, the two F2 replay tests are skipped and say why; the scores in the README come only from recorded runs.
- The recordings are committed (`evalset/recorded/`); they hold only made-up questions and redacted text.
