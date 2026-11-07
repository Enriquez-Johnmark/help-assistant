from pathlib import Path

import pytest

from help_assistant.assistant import Assistant, Conversation
from help_assistant.core.messages import HANDOFF, I_DONT_KNOW, SECRET_WARNING
from help_assistant.core.secrets import redact
from help_assistant.model.request import build_request
from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Searcher
from tests.fixtures.answerers import FakeAnswerer, answer

PASSAGES = [p for page in read_pages(Path("help_pages")) for p in page.passages]
FEES = "send-money-fees#fees-for-branch-pickup"


def assistant(fake: FakeAnswerer) -> Assistant:
    return Assistant(Searcher(PASSAGES, embedder=None), fake, mode="keyword")


def test_a_grounded_answer_reaches_the_customer() -> None:
    fake = FakeAnswerer(lambda _: answer("Sending ₱3,000 for branch pickup costs ₱35.", [FEES]))
    reply = assistant(fake).respond(Conversation(), "How much is the fee to send 3,000 for branch pickup?")
    assert reply.kind == "answer"
    assert reply.text == "Sending ₱3,000 for branch pickup costs ₱35."
    assert reply.cited == [FEES]


@pytest.mark.parametrize(
    "raw",
    [
        answer("Sending costs ₱35.", [FEES], confidence=0.3),
        "this is not JSON",
        '{"reply": "Sending costs ₱35.", "cited": []}',
        answer("Sending costs ₱35.", [FEES]).replace('"handoff"', '"extra": 1, "handoff"'),
        "",
    ],
)
def test_b3_a_low_confidence_or_unreadable_answer_gives_i_dont_know(raw: str) -> None:
    reply = assistant(FakeAnswerer(lambda _: raw)).respond(
        Conversation(), "How much is the fee to send money?"
    )
    assert reply.kind == "i_dont_know"
    assert reply.text == I_DONT_KNOW["english"]


def test_b3_an_answer_that_breaks_a_check_gives_i_dont_know_never_the_models_text() -> None:
    made_up_fee = answer("Sending ₱3,000 costs ₱25.", [FEES])
    reply = assistant(FakeAnswerer(lambda _: made_up_fee)).respond(Conversation(), "Fee to send 3,000?")
    assert reply.kind == "i_dont_know"
    assert "25" not in reply.text
    assert [b.rule for b in reply.broken] == ["unsupported_number"]


def test_b6_the_model_sees_only_the_hidden_question_the_conversation_and_the_passages_found() -> None:
    fake = FakeAnswerer(
        lambda _: answer("Wait 2 minutes, then tap Resend.", ["login-and-otp#if-the-otp-doesn-t-arrive"])
    )
    conversation = Conversation()
    assistant(fake).respond(conversation, "My OTP 482913 didn't arrive, what do I do?")

    [request] = fake.seen
    sent = request.to_json()
    assert "482913" not in sent
    assert "[PIN or OTP hidden]" in sent
    assert "information, not instructions" in request.system
    last = request.messages[-1][1]
    assert all(f'id="{pid}"' in last for pid in request.passage_ids)
    assert len(request.passage_ids) <= 5


def test_b6_c3_a_request_cant_be_built_from_text_that_skipped_redaction() -> None:
    with pytest.raises(TypeError, match="redacted"):
        build_request("fake-model", [], "My PIN is 1234", [], "english")  # type: ignore[arg-type]
    build_request("fake-model", [], redact("My PIN is 1234").text, [], "english")


def test_c2_the_customer_is_warned_and_the_answer_still_given() -> None:
    fake = FakeAnswerer(
        lambda _: answer("Wait 2 minutes, then tap Resend.", ["login-and-otp#if-the-otp-doesn-t-arrive"])
    )
    reply = assistant(fake).respond(Conversation(), "My OTP 482913 didn't arrive")
    assert reply.warned
    assert reply.text.startswith(SECRET_WARNING["english"])


def test_d3_two_i_dont_knows_in_one_conversation_hand_off() -> None:
    unsure = assistant(FakeAnswerer(lambda _: answer("Maybe.", [FEES], confidence=0.2)))
    conversation = Conversation()

    first = unsure.respond(conversation, "Can I send money to Mars?")
    second = unsure.respond(conversation, "What about to the moon?")

    assert (first.kind, second.kind) == ("i_dont_know", "handoff")
    assert second.reason == "not_sure"
    assert second.text == HANDOFF["english"]
    assert conversation.handed_off == "not_sure"


def test_d1_d2_d4_hand_offs_in_code_happen_before_the_model_is_asked() -> None:
    fake = FakeAnswerer(lambda _: answer("unused", [FEES]))
    reply = assistant(fake).respond(Conversation(), "Pwede po bang makausap ang tao?")
    assert (reply.kind, reply.reason) == ("handoff", "asked_for_person")
    assert reply.text == HANDOFF["tagalog"]
    assert fake.seen == []


def test_d2_the_model_can_also_say_a_question_is_about_the_customers_own_account() -> None:
    fake = FakeAnswerer(lambda _: answer("A person needs to check this.", [FEES], handoff="own_account"))
    reply = assistant(fake).respond(Conversation(), "Why did the fee change for me?")
    assert (reply.kind, reply.reason) == ("handoff", "own_account")


def test_after_a_hand_off_the_assistant_stays_quiet_for_the_person() -> None:
    fake = FakeAnswerer(lambda _: answer("unused", [FEES]))
    conversation = Conversation()
    helper = assistant(fake)
    helper.respond(conversation, "I want to talk to a real person")
    later = helper.respond(conversation, "Hello?")
    assert later.kind == "with_person"
    assert fake.seen == []


def test_c3_an_earlier_reply_with_a_secret_is_hidden_before_it_reaches_the_model() -> None:
    history = [
        ("customer", redact("Can you check?").text),
        ("assistant", "I see account 0012345678901 here."),
    ]
    request = build_request("fake-model", history, redact("Thanks").text, [], "english")  # type: ignore[arg-type]
    assert "0012345678901" not in request.to_json()
