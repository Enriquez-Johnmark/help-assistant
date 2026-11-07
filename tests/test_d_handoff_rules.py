import re

import pytest

from help_assistant.core.checks import check_rules
from help_assistant.core.handoff import handoff_reason
from help_assistant.core.messages import HANDOFF, I_DONT_KNOW, SECRET_WARNING


@pytest.mark.parametrize(
    "message",
    [
        "Can I talk to a person please?",
        "I want to speak with a real agent",
        "connect me to a human",
        "Pwede po bang makausap ang tao?",
        "gusto ko ng agent, hindi bot",
        "may tao ba dyan?",
        "Gusto ko pong makausap ang isang tao",
        "Pakikausap po ako ng isang tao",
        "Puwede ko bang kausapin ang isang agent?",
    ],
)
def test_d1_asking_for_a_person_hands_off(message: str) -> None:
    assert handoff_reason(message) == "asked_for_person"


@pytest.mark.parametrize(
    "message",
    [
        "Where is my transfer? Reference HM4K2P9Q7X",
        "Can you check the status of my padala from yesterday?",
        "Why was I charged ₱80 on my wallet?",
        "Nabawasan ang balance ko pero hindi pumasok sa biller",
        "Hindi pa natatanggap ng kapatid ko yung padala ko kahapon",
        "Na-hold ang account ko, bakit?",
        "Nasaan na yung pera na pinadala ko noong Lunes?",
    ],
)
def test_d2_a_question_about_the_customers_own_account_or_transaction_hands_off(message: str) -> None:
    assert handoff_reason(message) in ("own_account", "lost_money")


@pytest.mark.parametrize(
    "message",
    [
        "Someone stole money from my wallet!!!",
        "NAWALA ANG PERA KO SA WALLET, SCAM KAYO",
        "Na-scam ako, nawala yung 5,000 ko",
        "My money is gone and nobody answers, this is a scam",
    ],
)
def test_d4_a_customer_upset_about_lost_money_hands_off(message: str) -> None:
    assert handoff_reason(message) == "lost_money"


@pytest.mark.parametrize(
    "message",
    [
        "How do I verify my account?",
        "Magkano ang fee pag nagpadala ng 3,000?",
        "What should I do if my OTP doesn't arrive?",
        "How do I contact customer service?",
        "Paano i-cancel ang padala na hindi pa nakukuha?",
        "What happens if I lose my pawn ticket?",
        "Is it safe to share my PIN with someone who says they're from you?",
        "I lost my pawn ticket for my 5000 loan, what do I do?",
        "What should I do if my wallet is locked?",
        "Paano kung na-hold ang account ko?",
        "May nagtext na nanalo daw ako, scam ba ito?",
    ],
)
def test_d_ordinary_questions_are_answered_not_handed_off(message: str) -> None:
    assert handoff_reason(message) is None


@pytest.mark.parametrize("language", ["english", "tagalog", "taglish"])
def test_d5_the_hand_off_message_never_promises_a_time(language: str) -> None:
    message = HANDOFF[language]  # type: ignore[index]
    assert not re.search(
        r"\d|minute|hour|day|today|tomorrow|soon|right away|agad|bukas|mamaya|oras|minuto|araw", message, re.I
    )
    assert check_rules(message) == []


def test_the_fixed_messages_exist_in_each_language_and_promise_nothing() -> None:
    for messages in (HANDOFF, I_DONT_KNOW, SECRET_WARNING):
        assert set(messages) == {"english", "tagalog", "taglish"}
        for text in messages.values():
            assert check_rules(text) == []


@pytest.mark.parametrize("language", ["english", "tagalog", "taglish"])
def test_c2_the_warning_names_a_card_number_too(language: str) -> None:
    assert "card" in SECRET_WARNING[language]  # type: ignore[index]
