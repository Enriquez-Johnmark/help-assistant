# Answers are checked in code, and any failed check gives "I don't know"

The model writes each answer, but a customer sees it only after code checks it: it parsed into the strict `Answer` type; its confidence meets the threshold; every page it cites was one search returned; every figure in it is on a cited page or in the customer's own question; it promises no outcome for the customer's case and asks for no secret; it is in the customer's language. A failure gives "I don't know" and an offer of a person, never the model's text (B1–B5). Asking for a person, the customer's own account and lost money hand off in code before the model is asked (D1, D2, D4).

The deciding reason is that the harm of a wrong answer here is money: a wrong fee, a promised refund or a request for a PIN. The system prompt says the same rules, but a prompt can be ignored or overridden by what a customer types; a check in code can't.

## Considered options

- **Trust the system prompt.** Fewer refusals, but no guarantee, and nothing to test. Rejected.
- **A second model to judge each answer.** Catches more kinds of mistake, but doubles the cost and is itself unverifiable. Kept for grading the test set (F4), not for customers.
- **Fix a failing answer (drop the bad figure, strip the promise).** The rest of the answer may depend on what was removed. Rejected: "I don't know" is honest.

## Consequences

- Some right answers are refused, for example one that rounds a figure; the test set measures how many, so the checks can be tuned with numbers rather than guesses.
- The checks are plain rules (word lists in English, Tagalog and Taglish, figure matching), tested on their own in `tests/` and on the test set.
- Two "I don't know"s in one conversation hand off, so a customer is never stuck with a refusing bot.
