"""When a conversation goes to a person, decided in code before the model is
asked (D1, D2, D4). Word lists in English, Tagalog and Taglish."""

import re
from typing import Literal

Reason = Literal["asked_for_person", "own_account", "lost_money", "not_sure"]


def _any(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


# D1: the customer asks for a person.
_ASKS_FOR_PERSON = _any(
    r"\b(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+|someone|somebody)?"
    r"(?:real\s+|live\s+|human\s+)?(?:person|human|agent|someone|somebody|representative|staff)\b",
    r"\b(?:connect|transfer|pass)\s+me\s+to\s+(?:a\s+|an\s+)?(?:real\s+|live\s+)?(?:person|human|agent)\b",
    r"\b(?:real|live|human)\s+(?:person|agent)\b",
    r"\bmakausap\s+(?:po\s+)?(?:ang|ng|ko\s+ang)?\s*(?:tao|agent|staff|tauhan)\b",
    r"\bgusto\s+ko\s+(?:po\s+)?(?:ng\s+)?(?:tao|agent|kausap)\b",
    r"\bmay\s+tao\s+ba\b",
    r"\bpakausap\b",
)

# D4: money that is lost or stolen: a loss word close to a money word ("nawala
# ang pera", "stole money", "my money is gone"), so "I lost my pawn ticket for my
# 5000 loan" or "is this a scam?" are answered from the pages.
_MONEY_WORD = re.compile(
    r"^(?:money|pera|balance|funds|cash|ipon|savings|₱?\d{1,3}(?:,\d{3})+|₱?\d{4,}|₱\d+)$"
)
_LOSS_WORD = re.compile(
    r"^(?:stole|stolen|steal|lost|missing|gone|scam\w*|hack\w*|nawala|nawawala|ninakaw|nanakaw|naloko"
    r"|na-?scam|na-?hack)$"
)
_NEAR = 3


def _lost_money(message: str) -> bool:
    tokens = [t.strip(",") for t in re.findall(r"[\w₱,'-]+", message.lower())]
    money = [i for i, t in enumerate(tokens) if _MONEY_WORD.match(t)]
    loss = [i for i, t in enumerate(tokens) if _LOSS_WORD.match(t)]
    return any(abs(i - j) <= _NEAR for i in money for j in loss)


# D2: the customer's own account or transaction, with something only a person
# can look up: a reference, a date, a status, a charge, a hold.
_OWN = _any(
    r"\bmy\s+(?:transfer|transaction|padala|payment|wallet|account|balance|money|remittance|cash-?in|cash-?out)\b",
    r"\b(?:transfer|transaction|padala|bayad|wallet|account|balance|pera|remittance)\s+ko\b",
    r"\b(?:pinadala|ipinadala|binayad|sinend|na-?send)\s+ko\b",
    r"\bwas\s+i\s+charged\b",
)
# "What do I do if my wallet is locked?" asks how things work, not about one case.
_GENERAL = _any(
    r"^\s*(?:what|how)\b[^?]*\bif\b",
    r"\bwhat\s+happens\s+if\b",
    r"\bpaano\s+(?:po\s+)?kung\b",
    r"\bano\s+(?:po\s+)?(?:ang\s+)?(?:gagawin|mangyayari)\s+(?:ko\s+)?kung\b",
)
_CASE = _any(
    r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{10}\b",
    r"\b(?:where\s+is|status|check\s+(?:my|the)|charged|deducted|on\s+hold|held|locked|blocked|frozen)\b",
    r"\b(?:yesterday|last\s+(?:week|night|month)|this\s+morning|on\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
    r"\b(?:nasaan|nabawasan|na-?hold|naka-?hold|hindi\s+(?:pa\s+)?(?:natatanggap|pumasok|dumating|nakuha))\b",
    r"\b(?:kahapon|kanina|noong|lunes|martes|miyerkules|huwebes|biyernes|sabado|linggo)\b",
)


def handoff_reason(message: str) -> Reason | None:
    """Why `message` should go to a person at once, or `None` to answer it.
    Ordinary questions ("how do I verify my account?") are answered."""
    if _ASKS_FOR_PERSON.search(message):
        return "asked_for_person"
    if _lost_money(message):
        return "lost_money"
    if _OWN.search(message) and _CASE.search(message) and not _GENERAL.search(message):
        return "own_account"
    return None


_MONEY_MENTION = _any(
    r"\b(?:money|pera|balance|funds|cash|padala|transfer|remittance|refund|bayad|charged|deducted|nabawasan)\b",
    r"₱\s?\d",
)


def mentions_money(text: str) -> bool:
    """Whether a message is about money, so the agent's list puts it first (E1)."""
    return bool(_MONEY_MENTION.search(text))
