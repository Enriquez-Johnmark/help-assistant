"""Telling English, Tagalog and Taglish apart by their common words, for the
check that a reply is in the customer's language (B4)."""

import re
from typing import Literal

from help_assistant.core.checks import Broken

Language = Literal["english", "tagalog", "taglish"]

_TAGALOG = frozenset(
    [
        "ang",
        "ng",
        "mga",
        "po",
        "pong",
        "opo",
        "na",
        "sa",
        "namin",
        "natin",
        "kami",
        "kayo",
        "ninyo",
        "ninyong",
        "nyo",
        "niyo",
        "inyong",
        "inyo",
        "aming",
        "ating",
        "ito",
        "iyan",
        "para",
        "lang",
        "ay",
        "nang",
        "dahil",
        "kung",
        "hindi",
        "huwag",
        "wag",
        "pero",
        "ba",
        "din",
        "rin",
        "naman",
        "agad",
        "pasensya",
        "paumanhin",
        "salamat",
        "ko",
        "mo",
        "ako",
        "akin",
        "yung",
        "paano",
        "bakit",
        "ano",
        "saan",
        "kailan",
        "magkano",
        "pwede",
        "puwede",
        "wala",
        "may",
        "kasi",
        "nga",
        "ba",
        "eh",
        "siya",
        "sila",
        "tayo",
        "gagawin",
        "dumating",
    ]
)
_ENGLISH = frozenset(
    [
        "the",
        "we",
        "you",
        "your",
        "our",
        "is",
        "are",
        "to",
        "for",
        "and",
        "this",
        "that",
        "with",
        "of",
        "in",
        "it",
        "will",
        "can",
        "be",
        "please",
        "sorry",
        "thank",
        "thanks",
        "about",
        "into",
        "how",
        "what",
        "why",
        "when",
        "where",
        "much",
        "does",
        "do",
        "my",
        "i",
        "me",
        "if",
        "not",
    ]
)
_WORD = re.compile(r"[a-zñ']+")


def _counts(text: str) -> tuple[int, int]:
    words = _WORD.findall(text.lower())
    return sum(w in _TAGALOG for w in words), sum(w in _ENGLISH for w in words)


def language_of(text: str) -> Language | None:
    """The language of `text`, or `None` when it has too few common words to tell.
    Taglish that borrows only English nouns ("transfer", "OTP") may read as
    Tagalog; a Tagalog or Taglish customer accepts the same replies."""
    tagalog, english = _counts(text)
    if tagalog + english < 2:
        return None
    share = tagalog / (tagalog + english)
    if share >= 0.8:
        return "tagalog"
    if share <= 0.2:
        return "english"
    return "taglish"


def check_language(reply: str, customer: Language | None) -> list[Broken]:
    """The reply must be in the customer's language (B4). A Tagalog or Taglish
    customer reads either; an English one needs English. When the customer's
    language isn't clear, any reply passes."""
    if customer is None:
        return []
    tagalog, english = _counts(reply)
    fits = tagalog < 2 or tagalog * 3 <= english if customer == "english" else tagalog >= 2
    return [] if fits else [Broken("wrong_language", f"the customer wrote in {customer}")]
