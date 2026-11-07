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
