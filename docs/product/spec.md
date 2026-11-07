# Spec: Help Assistant

Decided round by round with the owner; the single source for spec decisions. The brief is `brief.md`. Status: **in progress** (Rounds 1–2 decided 2026-11-07).

## Words

- A **help page** is one page of the company's own help content, the only source the assistant answers from.
- A **passage** is a part of a help page that search can find and an answer can cite.
- A **conversation** is one customer's chat; a **hand-off** passes it to a **support agent**.
- A **secret** is a PIN, OTP, password, card number or account number.

## The demo company (Round 1, 2026-11-07)

- A made-up money-services company, **Halimbawa Money** ("halimbawa" is Tagalog for "example"), with about **25 made-up help pages**: sending and receiving money, bills payment, pawning (loans, renewal, redeeming, auction), the e-wallet (sign-up, ID verification, login and OTPs, cash-in and cash-out), fees, ID requirements and branch hours.
- Its fees and limits are clearly invented. No real company, brand or figure is used.

## Languages (Round 1, 2026-11-07)

- Help pages are in **English**. The assistant answers in the **customer's language** (Taglish, Tagalog or English) and shows the English page it used.

## Search (Round 1, 2026-11-07)

- **Local and free:** keyword search (BM25) and a small **multilingual embedding model run locally**, combined, so a Tagalog question finds an English page.
- The test set reports both **keyword search alone** and the **combined search**.

## The model (Round 1, 2026-11-07)

- **Claude Haiku** answers by default, through the owner's API key. The test set also runs **Claude Sonnet**, and the README reports whether it is worth the cost.
- The answer comes back as **structured data**: the reply, the passages it cites, a confidence, and whether to hand off. Anything that doesn't parse is treated as "I don't know".

## Checks in code (Round 1, 2026-11-07)

- Every cited passage must be one that search returned for this question.
- Every number in an answer (fee, amount, limit, number of days) must appear in a cited passage.
- A low confidence or a failed check gives **"I don't know"** and an offer of a person, never a guess.

## Secrets (Round 1, 2026-11-07)

- Before anything is stored or sent to the model, PINs and OTPs, card and account numbers (checked by their pattern) and passwords are **hidden**; mobile numbers and email addresses are hidden in what is stored.
- The customer is told not to share them.
- A test proves a hidden secret never reaches the model or the logs.

## Hand-off (Round 2, 2026-11-07)

- The assistant hands a conversation to a person when the customer **asks for one**, when the question is about **their own account or a specific transaction**, after **two "I don't know"s** in one conversation, or when the customer is **upset about lost money**.
- It says a person will reply, and **never promises when**.

## The support agent's view (Round 2, 2026-11-07)

- A list of conversations **waiting for a person**, money issues first, each with everything said so far (secrets already hidden).
- The agent **replies** there, and the reply appears in the customer's chat; the agent can **hand back** to the assistant or **close** the conversation.
- Every hand-off, reply, hand-back and close is **logged** with who and when.
- **One local user**, with no logins.

## The content owner's view (Round 2, 2026-11-07)

- The questions the assistant **couldn't answer**, grouped by topic and counted, showing which help pages are missing or unclear; and hand-offs counted **by reason**.

## The test set (Round 2, 2026-11-07)

- About **150 made-up questions**, committed with their right answers and source pages:

| Group | Questions | Must |
| --- | --- | --- |
| Answerable, English | ~60 | Answer correctly |
| Answerable, Taglish or Tagalog | ~40 | Answer correctly, in that language |
| Not in the pages | ~20 | Say "I don't know" |
| About the customer's own account | ~15 | Hand off |
| Tricky (typing a PIN, "ignore your rules", "promise me a refund") | ~15 | Refuse or hand off |

- **Grading:** code checks citations, numbers, hand-offs and refusals; Claude grades whether each answer matches the right one; the owner spot-checks 20 of Claude's grades.
- **Targets:** at least **85%** right answers and **90%** citing the right page; **100%**: no secret reaches the model or the logs; **100%** of own-account questions handed off.
- CI runs it from **recorded answers**, with no API key; an `eval` command runs it live.

## How it runs (Round 2, 2026-11-07)

- **FastAPI** serves the API, the chat page and the two staff views, as plain server-rendered HTML with a little JavaScript.
- **SQLite**; one command starts it; it answers only on **127.0.0.1**.

## Tooling (Round 2, 2026-11-07)

- Python 3.12 with **uv**, **ruff** (lint and format), **pyright** in strict mode, **pytest**, and the official Anthropic SDK.
- Every acceptance criterion has a test named after it; CI runs them all.
