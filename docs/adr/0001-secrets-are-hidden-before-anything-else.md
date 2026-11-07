# Secrets are hidden before anything else, and only hidden text can be stored or sent

A customer may type a PIN, an OTP, a card or account number or a password into the chat, however often they are told not to. The first step for every message is `redact`, which hides them; it returns `Redacted`, a text type that only `redact` can create. The store's insert and the model request builder accept nothing else, and check it at run time too, so the customer's raw words can't reach the database, the model or the logs (C1, C3).

The deciding reason is that "remember to redact" is a rule a later change can forget, and one forgotten call would send a customer's PIN to a third party. A type makes forgetting a pyright error and a failing test, not a silent leak.

## Considered options

- **Ask the model not to repeat secrets.** The secret would already have reached the model, and a prompt is not a guarantee. Rejected.
- **Redact in each caller (the web app, the commands, the evaluation).** Simple, but three ways in means three places to forget. Rejected.
- **Redact on the way out (before logging or storing).** Leaves the raw text in memory through every step, including the model request. Rejected.

## Consequences

- Hiding errs on the strict side: a long reference number may be hidden as an account number. A customer can rephrase; a leaked secret can't be taken back.
- Earlier turns, the assistant's and an agent's replies included, are redacted again before they go to the model.
- The tests check the whole path: the model requests, the evaluation run and a dump of the database hold no secret from the tricky test questions.
