# Glossary

The Help Assistant answers a money-services company's customers from that company's help pages. Use these words in code, docs and messages.

## People

**Company**:
The money-services business whose help pages the assistant answers from. In the demo, Halimbawa Money, which is made up.
_Avoid_: Client, tenant, brand

**Customer**:
A person asking a question in the chat.
_Avoid_: User, client

**Agent**:
A person on the company's support team who takes over a conversation, always by name.
_Avoid_: Operator, rep, admin

**Owner**:
The person responsible for the help pages, who sees what the assistant couldn't answer.
_Avoid_: Admin, editor

## Help content

**Help page**:
One Markdown page in `help_pages/`, marked `made_up: true`, with a title, a topic and sections.
_Avoid_: Article, document, FAQ

**Passage**:
One section of a help page (`page#section`): what search finds and an answer cites.
_Avoid_: Chunk, snippet

**Topic**:
The subject a help page belongs to (sending money, pawning…), used to group unanswered questions.

## Answering

**Conversation**:
One customer's chat, answered by the assistant, waiting for an agent, with an agent, or closed.
_Avoid_: Session, ticket, thread

**Answer**:
A reply from the help pages that passed every check, with the passages it cites.

**Citation**:
A passage an answer names as its source. Only a passage search returned may be cited.
_Avoid_: Reference, source (in code)

**Check**:
A rule in code that an answer must pass: its citations, its figures, no promise, no request for a secret, the customer's language. Any failed check gives "I don't know".
_Avoid_: Guardrail, filter

**"I don't know"**:
The reply when the pages don't say, or an answer failed a check; it offers a person. Two in one conversation hand off.
_Avoid_: Fallback, error

**Hand-off**:
Passing a conversation to an agent, with a reason: the customer asked for a person, their own account, lost money, or the assistant wasn't sure.
_Avoid_: Escalation, transfer

## Safety

**Secret**:
A PIN, OTP, password, card number or account number. Never asked for, never stored, never sent to the model.
_Avoid_: Sensitive data, PII (too broad)

**Redacted**:
Text with its secrets hidden. A type only `redact` can create; the store and the model client accept nothing else.
_Avoid_: Masked, sanitised

**Audit log**:
Every hand-off, reply, hand-back and close: when, who and what. Append-only, enforced by the database.

## Measuring

**Test set**:
The 150 made-up questions in `evalset/questions.jsonl`, in five groups, with their right answers and pages.
_Avoid_: Benchmark, dataset

**Recorded answer**:
A model answer saved by `eval --record`, keyed by a hash of the exact request, so tests and CI replay it without a key.
_Avoid_: Cache, fixture, mock
