# UI audit and polish, 2026-11-10

An audit of the chat page and the staff views with the `ui-taste` skill (`reference/audit.md`), then a polish pass (`reference/polish.md`) that kept the existing look. Owner's decision: `docs/decisions.md`, 2026-11-10.

## What was inspected

- **Build:** `main` at `a9e553b`, served by `showcase/server.py --claude` (Claude's recorded answers).
- **Browser:** Chromium (Playwright) at 1280×900 and 390×844 (phone, touch emulated).
- **Pages:**
  - the chat: an answer with its sources, then a hand-off for lost money;
  - the staff views: the agents' list, one conversation and the owner's view;
  - a help page, and the help content list.
- **Checks:** a script measured horizontal overflow on every page at both sizes; keyboard focus on the header's links.
- **Not checked:** a screen reader, zoom above 100% and real phones.

## Findings and what was done

| # | Priority | Finding | Done |
|---|---|---|---|
| 1 | P2 | The agents' list and a conversation's page named each chat by its full 32-character ID, which wrapped over two lines on a phone | "Chat bd9bfcf2": the short ID the audit log already uses (`344167b`) |
| 2 | P2 | The audit log showed stored codes ("handoff", "hand_back") | Each step in words ("Handed to a person"), with the speaker capitalised (`344167b`, `9f54b0f`) |
| 3 | P3 | The staff views wrote who spoke in lowercase ("customer:"), unlike the chat ("You", "Assistant") | "Customer", "Assistant", "Agent" (`344167b`) |
| 4 | P3 | Unanswered topics showed as slugs ("bills-payment") | "Bills payment" (`344167b`) |
| 5 | P3 | A help page's section headings were as large as its title, so the page had no clear top | Headings are a step below the title (`9f54b0f`) |
| 6 | P3 | Links on the page were the browser's default blue, while "Start a new chat" was the brand's green | Links in the page are the brand's colour (`9f54b0f`) |

**Checked and fine:**

- Every page fits a phone with no horizontal overflow.
- The header's links show a visible focus outline.
- The warning not to type a PIN or OTP is above the chat.
- The demo note is on every page.

## Checks after the fixes

- `ruff format --check`, `ruff check`, `pyright` and `pytest` (211 tests) passed before each commit.
- The staff views and a help page were captured again on a phone and inspected.
- The screenshots and the video were remade.
