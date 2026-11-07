# Brief: Help Assistant

Status: **approved by the owner** (2026-11-07). Once approved, the spec (`spec.md`) is decided round by round from it. "Help Assistant" is a working name.

## In one sentence

An AI assistant that answers customers' questions about a money-services company's services from that company's own help pages, in Taglish, Tagalog or English, shows where each answer comes from, never asks for a PIN or an OTP, and hands the customer to a person when it isn't sure.

## Why it exists

A portfolio project for AI engineering roles. It shows the parts of an AI assistant that matter once real customers use it: answering only from approved sources, measuring how often it is right, refusing what it must not do, and knowing when to hand over to a person.

It is a second project beside the Review Triage Agent, which finds what customers complain about in public reviews (sign-up, login and OTPs, failed transfers). This assistant answers those questions before they become one-star reviews.

It works for any company that sends money, pays bills, lends against pawned items or runs an e-wallet, given its help pages. The demo uses a **made-up company** with made-up help pages. It names no real company and uses no real company's branding.

## The problem

Customers of money services ask the same questions again and again: how to send money, what an ID needs to show, why an OTP hasn't arrived, when a pawned item must be redeemed, why a transfer is still pending. The answers are already on the help pages, but people don't find them, so they wait for an agent or leave a bad review. A chatbot that makes things up is worse than none: a wrong fee, a promised refund or a request for a PIN can cost a customer money and the company its trust.

## Who uses it

- **A customer** asks a question in a chat window, in their own words and language.
- **A support agent** takes over conversations the assistant hands off, with the conversation so far.
- **The help-content owner** sees the questions the assistant couldn't answer, which are the help pages that are missing or unclear.

(In the portfolio, all three are shown in a demo.)

## What it does (first version)

1. **Reads the help pages** given to it (web pages or Markdown) and keeps them ready to search.
2. **Answers from them only**, in the customer's language, and shows the page each answer comes from.
3. **Says "I don't know" when the pages don't say**, rather than guessing, and offers a person.
4. **Hands off to a person** when it isn't sure, when the customer asks for one, or when the question is about their own account or a specific transaction, which it can't see.
5. **Protects secrets:** it never asks for an account number, PIN, OTP, password or card number; if a customer types one, it is hidden before anything is stored or sent to the model, and the customer is warned.
6. **Never promises** refunds, outcomes or dates, and never gives fees or rates that the pages don't state.
7. **Lists unanswered questions** for the content owner.
8. **Measures itself** on a test set of questions with known answers: how often it is right, how often it shows the right page, and how often it hands off or refuses when it should.

## How it's used

- A small **chat page**, the kind a company would embed on its help site.
- A **hand-off view** for support agents.
- An **API**, so it can sit behind other channels later.

## What it must never do

- Ask for, keep or pass on an account number, PIN, OTP, password or card number.
- State a fee, rate, limit or date that isn't in the help pages.
- Promise a refund, an outcome or a date.
- Act on an account or look up a transaction.
- Present itself as a real company's official assistant, or use a real company's name or branding.
- Commit real customer data; the demo uses made-up help pages and made-up questions.

## How success is shown

- **Accuracy on the test set**, reported in the README: right answers, right source pages, and correct refusals and hand-offs.
- **Safety checks** that always pass: no secret ever reaches the model or the logs, and no answer states a fee or promise the pages don't support.
- A README with screenshots and a walkthrough video, like the owner's other projects.

## Technology (proposed)

**Python** (FastAPI), so the portfolio shows Python beside TypeScript and Rust; Claude through the owner's API key (never a Claude subscription); a local search index with no paid services; tests and CI. The details are decided in the spec.

## Not in the first version

Looking up accounts or transactions, Viber, Messenger or SMS, voice, several companies at once, user accounts.

## Licence

MIT, like the Review Triage Agent, so anyone can clone and run it.
