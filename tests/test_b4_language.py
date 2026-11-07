import pytest

from help_assistant.core.language import check_language, language_of


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("How much is the fee to send money?", "english"),
        ("Magkano po ang bayad sa pagpapadala ng pera?", "tagalog"),
        ("Paano mag-sangla ng alahas?", "tagalog"),
        ("Sorry po, how do I cash out sa branch?", "taglish"),
        ("ok", None),
    ],
)
def test_b4_the_customers_language_is_told_apart(text: str, language: str | None) -> None:
    assert language_of(text) == language


@pytest.mark.parametrize(
    "text",
    [
        "Bakit Pending pa rin ang transfer ko?",
        "Hindi dumating ang OTP ko, ano gagawin ko?",
        "Pwede ba mag cash out?",
    ],
)
def test_b4_tagalog_with_english_nouns_reads_as_tagalog_or_taglish(text: str) -> None:
    # Taglish mostly borrows English nouns ("transfer", "OTP"), which the common
    # words can't see; either reading accepts the same replies.
    assert language_of(text) in ("tagalog", "taglish")


def test_b4_a_reply_in_the_customers_language_passes() -> None:
    assert check_language("Sending up to ₱1,000 costs ₱15.", "english") == []
    assert (
        check_language("Pasensya na po. Ang bayad sa pagpapadala ng hanggang ₱1,000 ay ₱15.", "tagalog") == []
    )
    assert check_language("Sorry po! Ang fee sa padala na hanggang ₱1,000 ay ₱15 lang.", "taglish") == []
    # Taglish and Tagalog customers both read either.
    assert check_language("Ang bayad sa pagpapadala ng hanggang ₱1,000 ay ₱15.", "taglish") == []


def test_b4_a_reply_in_another_language_is_refused() -> None:
    assert [b.rule for b in check_language("Sending up to ₱1,000 costs ₱15.", "tagalog")] == [
        "wrong_language"
    ]
    assert check_language("Ang bayad ay ₱15 po para sa hanggang ₱1,000.", "english") != []


def test_b4_when_the_customers_language_isnt_clear_any_reply_passes() -> None:
    assert check_language("Sending up to ₱1,000 costs ₱15.", None) == []
