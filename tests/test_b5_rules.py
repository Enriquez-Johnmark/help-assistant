import pytest

from help_assistant.core.checks import check_rules


def rules(reply: str) -> list[str]:
    return [broken.rule for broken in check_rules(reply)]


@pytest.mark.parametrize(
    "reply",
    [
        "Don't worry, we will refund your money today.",
        "You will get your money back by tomorrow.",
        "Your transfer will be reversed within the day, I promise.",
        "Your money will be returned to your wallet today.",
        "Your refund will arrive tomorrow.",
        "I guarantee your item won't go to auction.",
        "Ibabalik po namin ang pera ninyo bukas.",
        "Sigurado po na maibabalik ang pera ninyo.",
        "Ire-refund po namin agad yung fee.",
        "Makakaasa po kayo na aayusin namin ito ngayon.",
    ],
)
def test_b5_promises_of_refunds_outcomes_or_dates_are_caught(reply: str) -> None:
    assert "promise" in rules(reply)


@pytest.mark.parametrize(
    "reply",
    [
        "Please send me your PIN so I can check.",
        "Reply with your OTP and I will look into it.",
        "Pakibigay po ang inyong account number at password.",
        "Paki-send po ng OTP para ma-check namin.",
        "Don't worry, just share your card number with me.",
    ],
)
def test_b5_asking_for_a_secret_is_caught(reply: str) -> None:
    assert "asks_for_secret" in rules(reply)


@pytest.mark.parametrize(
    "reply",
    [
        # Policies quoted from the help pages are not promises.
        "If you cancel on the same day, the amount is returned in full and the fee too.",
        "Most transfers finish within 15 minutes. If it is still Pending after 2 hours, contact support.",
        "Bank cash-ins arrive within 30 minutes on banking days.",
        # Warnings to keep secrets safe are not requests.
        "Never share your PIN or OTP with anyone, even someone who says they are from us.",
        "Huwag po ninyong ibigay ang inyong PIN o OTP kahit kanino.",
        "A person in support will look into your transfer; have the reference number ready.",
        "Pwede po kayong mag-renew ng sangla sa app gamit ang ticket number.",
        "Tell support if your OTP still doesn't arrive after 2 minutes.",
        "Your transfer will be checked by a person in support.",
        "Your concern will be looked into; please have the reference number ready.",
        "Open the app and confirm with your 6-digit PIN.",
        "Send the reference number to the receiver; they don't need your PIN.",
    ],
)
def test_b5_quoting_policy_and_warning_about_secrets_pass(reply: str) -> None:
    assert rules(reply) == []
