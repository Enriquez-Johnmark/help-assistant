"""Hiding secrets and personal details in what a customer types, before
anything is stored or sent to the model (C1, C2). The only way to make a
`Redacted` text is `redact`, so the store and the model client, which take only
`Redacted`, can't be handed a customer's words that skipped it (C3)."""

import re
from dataclasses import dataclass
from typing import Literal, NewType

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

Redacted = NewType("Redacted", str)


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
_CODE = r"\d{3}[ -]?\d{1,3}|\d{4,8}"
_CODE_AFTER_WORD = re.compile(rf"(?i)\b{_CODE_WORDS}\b[^\d.!?]{{0,40}}?(?<!\d)({_CODE})(?!\d)")
_CODE_BEFORE_WORD = re.compile(rf"(?i)(?<!\d)({_CODE})(?!\d)[^\d.!?]{{0,20}}?\b{_CODE_WORDS}\b")
_ONLY_A_CODE = re.compile(r"^\s*(\d{4,8}|\d{3} \d{3})\s*$")
_PASSWORD = re.compile(r"(?i)\b(?:password|passwd|pw)\b(?:\s+ko)?(?:\s+po)?\s*(?:is|ay|:|=)\s*(\S+)")
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
        # named as a card; any other long number is taken as an account number.
        if (
            13 <= len(digits) <= 19
            and _luhn(digits)
            and (len(digits) == 16 or grouped or _CARD_WORDS.search(text))
        ):
            return hide("card_number")
        if not grouped and 10 <= len(digits) <= 16:
            return hide("account_number")
        return match.group()

    text = _DIGIT_RUN.sub(digit_run, text)
    if _ONLY_A_CODE.match(text):
        return Redaction(Redacted(hide("pin_or_otp")), found)
    for pattern in (_CODE_AFTER_WORD, _CODE_BEFORE_WORD):
        text = pattern.sub(lambda m: m.group().replace(m.group(1), hide("pin_or_otp")), text)
    text = _PASSWORD.sub(lambda m: m.group().replace(m.group(1), hide("password")), text)
    return Redaction(Redacted(text), found)
