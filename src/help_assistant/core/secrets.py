"""Hiding secrets and personal details in what a customer types, before
anything is stored or sent to the model (C1, C2). The only way to make a
`Redacted` text is `redact`, so the store and the model client, which accept
only `Redacted`, can't be handed a customer's words that skipped it (C3)."""

import re
from dataclasses import dataclass
from typing import Literal

Kind = Literal["pin_or_otp", "card_number", "account_number", "password", "mobile_number", "email"]

# The customer is warned about these (C2); mobile numbers and emails are hidden
# without a warning, since sharing them is no risk to their money.
SECRET_KINDS: tuple[Kind, ...] = ("pin_or_otp", "card_number", "account_number", "password")

LABELS: dict[Kind, str] = {
    "pin_or_otp": "[PIN or OTP hidden]",
    "card_number": "[card number hidden]",
    "account_number": "[account number hidden]",
    "password": "[password hidden]",
    "mobile_number": "[mobile number hidden]",
    "email": "[email hidden]",
}

_TOKEN = object()


class Redacted(str):
    """Text that has been through `redact`. Made only there: the store and the
    model client check for it, so a customer's raw words can't reach them (C3)."""

    __slots__ = ()

    def __new__(cls, value: str, *, _token: object = None) -> "Redacted":
        if _token is not _TOKEN:
            raise TypeError("Redacted text comes only from redact()")
        return super().__new__(cls, value)


@dataclass(frozen=True)
class Redaction:
    text: Redacted
    found: list[Kind]

    @property
    def warn(self) -> bool:
        """Whether the customer typed a secret and should be told not to (C2)."""
        return any(kind in SECRET_KINDS for kind in self.found)


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_MOBILE = re.compile(r"(?<![\d+])(?:\+?63[\s-]?|0)9\d{2}[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
_DIGIT_RUN = re.compile(r"(?<!\d)\d(?:[ -]?\d){9,18}(?!\d)")
_CODE_WORDS = r"(?:m?pin|otp|one[- ]?time[- ]?(?:pin|password|code)|passcode|verification code|code)"
# A code as typed: "482913", "774 210", or one digit at a time ("4 8 2 9", "5-5-2-1").
_CODE = r"\d(?:[ -]\d){3,7}|\d{3}[ -]?\d{1,3}|\d{4,8}"
_CODE_AFTER_WORD = re.compile(rf"(?i)\b{_CODE_WORDS}\b[^\d.!?]{{0,40}}?(?<!\d)({_CODE})(?!\d)")
_CODE_BEFORE_WORD = re.compile(rf"(?i)(?<!\d)({_CODE})(?!\d)[^\d.!?]{{0,20}}?\b{_CODE_WORDS}\b")
_ONLY_A_CODE = re.compile(r"^\s*(\d{4,8}|\d{3} \d{3})\s*$")
_PASSWORD = re.compile(r"(?i)\b(?:password|passwd|pw)\b(?:\s+ko)?(?:\s+po)?\s*(?:is|ay|:|=)\s*(\S+)")
# Without "is", "ay" or ":", the next word is a password only if it looks like
# one, so "my password reset doesn't work" keeps its words.
_PASSWORD_BARE = re.compile(r"(?i)\b(?:password|passwd|pw)\b(?:\s+ko)?(?:\s+po)?\s+(\S+)")


def _looks_like_a_password(word: str) -> bool:
    word = word.strip(".,!?'\"")
    return (
        any(c.isdigit() for c in word)
        or any(not c.isalnum() and c != "'" for c in word)
        or (any(c.isupper() for c in word[1:]))
    )


_CARD_WORDS = re.compile(r"(?i)\b(?:card|credit|debit|visa|mastercard)\b")


def _luhn(digits: str) -> bool:
    total = 0
    for index, digit in enumerate(reversed(digits)):
        value = int(digit) * (2 if index % 2 else 1)
        total += value - 9 if value > 9 else value
    return total % 10 == 0


def redact(text: str) -> Redaction:
    """`text` with secrets and personal details replaced by a label saying what
    was hidden, and the kinds found. Ordinary numbers (amounts, times, days) and
    reference numbers are kept."""
    found: list[Kind] = []

    def hide(kind: Kind) -> str:
        found.append(kind)
        return LABELS[kind]

    text = _EMAIL.sub(lambda _: hide("email"), text)
    text = _MOBILE.sub(lambda _: hide("mobile_number"), text)

    def digit_run(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group())
        grouped = match.group() != digits
        # A card number passes the Luhn check and is 16 digits, grouped, or
        # named as a card.
        if (
            13 <= len(digits) <= 19
            and _luhn(digits)
            and (len(digits) == 16 or grouped or _CARD_WORDS.search(text))
        ):
            return hide("card_number")
        # Ten digits or more, together or in groups, is an account number: an
        # amount is written with commas, and a date or a time is shorter.
        return hide("account_number")

    text = _DIGIT_RUN.sub(digit_run, text)
    if _ONLY_A_CODE.match(text):
        return Redaction(Redacted(hide("pin_or_otp"), _token=_TOKEN), found)
    for pattern in (_CODE_AFTER_WORD, _CODE_BEFORE_WORD):
        text = pattern.sub(lambda m: m.group().replace(m.group(1), hide("pin_or_otp")), text)
    text = _PASSWORD.sub(lambda m: m.group().replace(m.group(1), hide("password")), text)
    text = _PASSWORD_BARE.sub(
        lambda m: (
            m.group().replace(m.group(1), hide("password"))
            if _looks_like_a_password(m.group(1)) and "hidden]" not in m.group(1)
            else m.group()
        ),
        text,
    )
    return Redaction(Redacted(text, _token=_TOKEN), found)
