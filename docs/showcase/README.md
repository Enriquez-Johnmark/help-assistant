# Showcase

Screenshots of the chat and the staff views, on the made-up company Halimbawa Money. **No model was used.** Every conversation shown is one the rules in code hand to a person before any model is asked: a customer asking for a person, asking about their own account or transaction, or saying money is lost. The server used for them (`showcase/server.py`) has a model that refuses to be called, so none of the words below are a model's. Screenshots of Claude answering from the help pages follow once the live scores are recorded.

| File | Shows |
| --- | --- |
| `desktop-1-chat.png` | A customer in Tagalog says money is lost and types an OTP by mistake: the OTP is hidden, they are warned, handed to a person, and an agent replies |
| `desktop-2-agents.png` | The agents' list: money issues first, then the longest waiting; secrets already hidden, a card number included |
| `desktop-3-conversation.png` | One conversation, where an agent, by name, replies, hands back to the assistant or closes |
| `desktop-4-owner.png` | The owner's view: hand-offs by reason and the append-only audit log (unanswered questions need the model, so none yet) |
| `desktop-5-help-page.png` | A help page, where every answer's citation links |
| `phone-1-chat.png` | The same chat on a phone |

Times are a made-up morning, Manila time.

## Making them again

```sh
uv run python showcase/server.py &                   # on 127.0.0.1:8013, no key needed
NODE_PATH="$(npm root -g)" node showcase/shots.cjs   # needs Playwright
```
