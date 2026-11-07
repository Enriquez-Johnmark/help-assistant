"""Checks on a model's answer, in code, before a customer sees it. Any broken
check turns the answer into "I don't know" (architecture.md)."""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from help_assistant.pages.reader import Passage


@dataclass(frozen=True)
class Broken:
    rule: str
    detail: str


def check_citations(cited: Sequence[str], retrieved: Sequence[str]) -> list[Broken]:
    """An answer must cite at least one passage, and only passages that search
    returned for this question (B1)."""
    if not cited:
        return [Broken("no_citation", "the answer cites no help page")]
    unknown = [pid for pid in cited if pid not in retrieved]
    if unknown:
        return [Broken("unknown_citation", f"cites passages search didn't return: {', '.join(unknown)}")]
    return []


# Number words. In a reply "one" and "isa" are not counted: "one of the ways"
# and "isa sa mga" aren't figures. In a passage they are, which only allows more:
# a page's "one break" lets a reply say "1 break".
_ONE = {"one": 1, "isa": 1}
_WORDS = {
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "dalawa": 2, "tatlo": 3, "apat": 4, "lima": 5, "anim": 6, "pito": 7,
    "walo": 8, "siyam": 9, "sampu": 10,
}  # fmt: skip
_WORD = re.compile(rf"(?i)\b({'|'.join(_WORDS)})(?:ng|na)?\b")
_WORD_OR_ONE = re.compile(rf"(?i)\b({'|'.join(_WORDS | _ONE)})(?:ng|na)?\b")
_TIME = re.compile(r"\b\d{1,2}:\d{2}\b")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_in(text: str, *, count_one: bool = False) -> set[str]:
    """The figures in `text`, written one way: "₱1,000", "1000" and "P1,000.00"
    are all "1000"; times stay as "8:00"; number words become digits ("one" and
    "isa" only with `count_one`)."""
    found = set(_TIME.findall(text))
    rest = _TIME.sub(" ", text)
    for raw in _NUMBER.findall(rest):
        value = raw.replace(",", "")
        if "." in value:
            value = value.rstrip("0").rstrip(".")
        found.add(value)
    pattern, values = (_WORD_OR_ONE, _WORDS | _ONE) if count_one else (_WORD, _WORDS)
    found.update(str(values[word.lower()]) for word in pattern.findall(rest))
    return found


def check_numbers(reply: str, cited: Iterable[Passage]) -> list[Broken]:
    """Every figure in the reply (a fee, amount, limit, time or number of days)
    must appear in a passage it cites (B2), so no figure is made up."""
    allowed: set[str] = set()
    for passage in cited:
        allowed |= numbers_in(passage.text, count_one=True)
    unsupported = sorted(numbers_in(reply) - allowed)
    if unsupported:
        return [Broken("unsupported_number", f"figures not in the cited pages: {', '.join(unsupported)}")]
    return []


# Promises about the customer's own case. Policies quoted from the pages ("the
# amount is returned in full", "most transfers finish within 15 minutes") are
# not promises; a promise is someone saying it *will* happen for this customer.
_PROMISES: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"\b(?:we|i)(?:'ll| will| shall)\s+(?:\w+\s+){0,2}?"
        r"(?:refund|reimburse|return|reverse|credit|restore|fix|resolve|send back|make sure)",
        r"\byou(?:'ll| will)\s+(?:\w+\s+){0,2}?(?:get|receive|have)\s+"
        r"(?:\w+\s+){0,3}?(?:refund|money|cash|funds)\b",
        r"\byour\s+(?:money|refund|transfer|item|fee|cash|balance)\s+will\s+(?:be|arrive|come)\b",
        r"\b(?:i|we)\s+(?:promise|guarantee|assure)\b|\bguaranteed?\b",
        r"\b(?:ibabalik|ire-?refund|aayusin)\s+(?:po\s+)?namin\b",
        r"\b(?:sigurado\w*|pangako|ipinapangako|makakaasa|garantisado)\b",
    )
)

_SECRET = re.compile(
    r"\b(?:account (?:number|no)|card (?:number|no)|m?pin|otp|one[- ]time (?:pin|password|code)"
    r"|password|passcode|cvv)\b"
)
# Asking for something to be given to us, not telling the customer to use their
# own PIN in the app ("confirm with your PIN" is how the app works).
_REQUEST = re.compile(
    r"\b(?:send|give|share|provide|tell|reply with|dm|forward|message us|ibigay|bigay|ipadala|i-?send"
    r"|i-?share|sabihin|paki-?\w*)\b"
)
_NEGATION = {"never", "don't", "dont", "not", "huwag", "wag", "hindi", "kailanman"}
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
_CLAUSE = re.compile(r"[,;:]")


def _asks_for_secret(sentence: str) -> bool:
    """A sentence names a secret and has a request that isn't negated just
    before it, within its own clause ("never share your PIN" passes)."""
    if not _SECRET.search(sentence):
        return False
    for request in _REQUEST.finditer(sentence):
        clause = _CLAUSE.split(sentence[: request.start()])[-1]
        if not set(re.findall(r"[a-z']+", clause)[-3:]) & _NEGATION:
            return True
    return False


def check_rules(reply: str) -> list[Broken]:
    """A reply promises no refund, outcome or date, and asks for no secret, in
    English, Tagalog or Taglish (B5)."""
    lowered = reply.lower()
    broken: list[Broken] = []
    if any(pattern.search(lowered) for pattern in _PROMISES):
        broken.append(Broken("promise", "promises a refund, an outcome or a date"))
    if any(_asks_for_secret(sentence) for sentence in _SENTENCE.split(lowered)):
        broken.append(Broken("asks_for_secret", "asks for a PIN, OTP, password, card or account number"))
    return broken
