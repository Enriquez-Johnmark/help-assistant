import random

import pytest

from help_assistant.core.secrets import Redacted, redact

# Ways customers write their secrets, in English, Tagalog and Taglish. {code}
# is a made-up PIN or OTP, {account} a made-up account number.
TEMPLATES = [
    "My PIN is {code}",
    "otp ko po {code}",
    "eto po yung code: {code}",
    "{code} yung otp ko",
    "pin ko ay {code} tapos ayaw pa rin",
    "The one-time pin I got is {code}, please help",
    "{code}",
    "account number ko {account}",
    "my acct no is {account} pls check",
    "password ko ay Pusa{code}",
    "my password: Juan{code}!",
]


def test_c3_no_secret_survives_redaction_however_it_is_written() -> None:
    rng = random.Random(20261107)  # noqa: S311 - made-up test data, not security
    for _ in range(500):
        template = rng.choice(TEMPLATES)
        code = "".join(rng.choice("0123456789") for _ in range(rng.choice([4, 6])))
        account = "".join(rng.choice("0123456789") for _ in range(rng.randint(10, 14)))
        message = template.format(code=code, account=account)
        hidden = redact(message)
        assert code not in hidden.text or "{code}" not in template, message
        assert account not in hidden.text or "{account}" not in template, message
        assert hidden.warn, message


def test_c3_redacted_text_comes_only_from_redact() -> None:
    assert isinstance(redact("hello").text, Redacted)
    with pytest.raises(TypeError, match="only from redact"):
        Redacted("My PIN is 1234")
