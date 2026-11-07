import pytest

from help_assistant.core.secrets import SECRET_KINDS, redact

# Made-up customer messages, with what must be hidden in each. Every number here
# is invented; the card numbers are standard test numbers, not real cards.
CASES: list[tuple[str, str, list[str]]] = [
    ("My PIN is 482913, why can't I log in?", "482913", ["pin_or_otp"]),
    ("otp ko po 5521 pero ayaw pa rin", "5521", ["pin_or_otp"]),
    ("Ito po yung code na dumating: 774 210", "774 210", ["pin_or_otp"]),
    ("Pin ko ay 1234", "1234", ["pin_or_otp"]),
    ("Here is my one-time pin 908172", "908172", ["pin_or_otp"]),
    ("482913", "482913", ["pin_or_otp"]),
    ("PIN ko 4 8 2 9", "4 8 2 9", ["pin_or_otp"]),
    ("the otp is 5-5-2-1", "5-5-2-1", ["pin_or_otp"]),
    ("Card ko 4111 1111 1111 1111 na-charge twice", "4111 1111 1111 1111", ["card_number"]),
    ("my card 5500-0000-0000-0004 was declined", "5500-0000-0000-0004", ["card_number"]),
    ("Account number ko 0012345678901 sa bank", "0012345678901", ["account_number"]),
    ("acct no. 12345678901234 please check", "12345678901234", ["account_number"]),
    ("My password is Juan@2026 and it doesn't work", "Juan@2026", ["password"]),
    ("password ko ay mahalpusa99", "mahalpusa99", ["password"]),
    ("password ko mahalpusa99 pero ayaw", "mahalpusa99", ["password"]),
    ("my password Juan@2026 won't work", "Juan@2026", ["password"]),
    ("Text me at 09171234567", "09171234567", ["mobile_number"]),
    ("number ko +63 917 123 4567 po", "+63 917 123 4567", ["mobile_number"]),
    ("email ko ana.cruz@example.test", "ana.cruz@example.test", ["email"]),
]

# Ordinary questions with numbers that are not secrets: nothing may be hidden.
KEPT = [
    "How much is the fee to send ₱5,000?",
    "Nagpadala ako ng 50000 kahapon, bakit pending?",
    "Is the branch open at 8:00 on Saturday?",
    "Pwede ba mag-cash in ng 10,000 sa branch?",
    "My reference number is HM4K2P9Q7X",
    "I sent it 3 days ago at 2 pm",
    "My password reset doesn't work",
    "Paano palitan ang password ko?",
]


@pytest.mark.parametrize(("message", "secret", "kinds"), CASES)
def test_c1_secrets_are_hidden_in_english_tagalog_and_taglish(
    message: str, secret: str, kinds: list[str]
) -> None:
    redaction = redact(message)
    assert secret not in redaction.text
    assert [kind for kind in redaction.found] == kinds


@pytest.mark.parametrize("message", KEPT)
def test_c1_ordinary_numbers_and_reference_numbers_are_kept(message: str) -> None:
    redaction = redact(message)
    assert redaction.text == message
    assert redaction.found == []


def test_c1_a_number_that_fails_the_card_check_is_not_called_a_card() -> None:
    assert redact("card 4111 1111 1111 1112").found != ["card_number"]


def test_c1_the_hidden_text_says_what_was_hidden() -> None:
    assert redact("My PIN is 482913").text == "My PIN is [PIN or OTP hidden]"


def test_c2_the_customer_is_warned_when_they_type_a_secret() -> None:
    assert redact("otp ko 5521").warn
    assert not redact("Text me at 09171234567").warn
    assert set(SECRET_KINDS) == {"pin_or_otp", "card_number", "account_number", "password"}
