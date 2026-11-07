# Spec: Help Assistant

Decided round by round with the owner; the single source for spec decisions. The brief is `brief.md`. Status: **in progress** (Round 1 decided 2026-11-07).

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
