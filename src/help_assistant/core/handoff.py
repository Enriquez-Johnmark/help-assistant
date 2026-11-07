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

# D4: lost money, with anger or a loss.
_MONEY = _any(
    r"\b(?:money|pera|balance|funds|cash|ipon|savings)\b", r"₱\s?\d", r"\b\d{1,3}(?:,\d{3})+\b", r"\b\d{4,}\b"
)
_LOSS = _any(
    r"\b(?:stole|stolen|steal|lost|missing|gone|scam\w*|hack\w*)\b",
    r"\b(?:nawala|nawawala|ninakaw|nanakaw|naloko|na-?scam|na-?hack)\b",
)

# D2: the customer's own account or transaction, with something only a person
# can look up: a reference, a date, a status, a charge, a hold.
_OWN = _any(
    r"\bmy\s+(?:transfer|transaction|padala|payment|wallet|account|balance|money|remittance|cash-?in|cash-?out)\b",
    r"\b(?:transfer|transaction|padala|bayad|wallet|account|balance|pera|remittance)\s+ko\b",
    r"\b(?:pinadala|ipinadala|binayad|sinend|na-?send)\s+ko\b",
    r"\bwas\s+i\s+charged\b",
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
    if _MONEY.search(message) and _LOSS.search(message):
        return "lost_money"
    if _OWN.search(message) and _CASE.search(message):
        return "own_account"
    return None
