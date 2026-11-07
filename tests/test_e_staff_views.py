from datetime import timedelta

import pytest

from tests.fixtures.service import chat


def test_e1_the_agents_list_shows_waiting_conversations_money_first_with_what_was_said() -> None:
    service, clock, _ = chat()
    person = service.start()
    service.customer_message(person, "Can I talk to a real person?")
    clock.advance(timedelta(minutes=1))
    money = service.start()
    service.customer_message(money, "Nawala ang pera sa wallet ko!")
    answered = service.start()
    service.customer_message(answered, "My OTP didn't arrive")

    waiting = service.waiting()

    assert [w.id for w in waiting] == [money, person]
    assert waiting[0].money_involved
    first = waiting[1].messages[0]
    assert (first.sender, first.text) == ("customer", "Can I talk to a real person?")


def test_e2_an_agents_reply_appears_in_the_customers_chat_and_they_can_hand_back_or_close() -> None:
    service, _, fake = chat()
    conversation = service.start()
    service.customer_message(conversation, "I want to speak with a real agent")

    service.agent_reply(conversation, "Ana", "Hi, I'm Ana from support. How can I help?")
    assert service.messages(conversation)[-1].sender == "agent"
    assert service.messages(conversation)[-1].text == "Hi, I'm Ana from support. How can I help?"

    service.hand_back(conversation, "Ana")
    reply = service.customer_message(conversation, "My OTP didn't arrive")
    assert reply.kind == "answer"
    assert fake.seen

    service.close(conversation, "Ana")
    assert service.status(conversation) == "closed"
    with pytest.raises(ValueError, match="closed"):
        service.customer_message(conversation, "hello?")


def test_e3_every_hand_off_reply_hand_back_and_close_is_logged_with_who_and_when() -> None:
    service, clock, _ = chat()
    conversation = service.start()
    service.customer_message(conversation, "I want to speak with a real agent")
    clock.advance(timedelta(minutes=5))
    service.agent_reply(conversation, "Ana", "Hello!")
    service.hand_back(conversation, "Ana")
    service.close(conversation, "Ben")

    log = [(e.actor, e.action, e.at[11:16]) for e in service.audit_log()]
    assert log == [
        ("assistant", "handoff", "02:00"),
        ("Ana", "reply", "02:05"),
        ("Ana", "hand_back", "02:05"),
        ("Ben", "close", "02:05"),
    ]


def test_e3_the_log_cant_be_changed() -> None:
    service, _, _ = chat()
    conversation = service.start()
    service.customer_message(conversation, "I want to speak with a real agent")
    with pytest.raises(Exception, match="append-only"):
        service.db.execute("update audit_log set actor = 'someone'")
    with pytest.raises(Exception, match="append-only"):
        service.db.execute("delete from audit_log")


def test_e4_the_owners_view_counts_unanswered_questions_by_topic_and_hand_offs_by_reason() -> None:
    service, _, _ = chat()
    for question in ("Do you offer travel insurance?", "How do I pawn a car?", "Can I pawn a phone?"):
        service.customer_message(service.start(), question)
    service.customer_message(service.start(), "I want to speak with a real agent")
    service.customer_message(service.start(), "Nawala ang pera sa wallet ko!")

    view = service.owner_view()

    stored_unanswered = service.db.execute("select count(*) from unanswered").fetchone()[0]
    assert sum(view.unanswered_by_topic.values()) == stored_unanswered == 3
    assert view.unanswered_by_topic.get("pawning", 0) >= 1
    assert view.handoffs_by_reason == {"asked_for_person": 1, "lost_money": 1}


def test_e_only_a_person_by_name_acts_on_a_conversation() -> None:
    service, _, _ = chat()
    conversation = service.start()
    service.customer_message(conversation, "I want to speak with a real agent")
    with pytest.raises(ValueError, match="name"):
        service.agent_reply(conversation, " ", "Hello")


def test_c3_no_secret_reaches_the_database() -> None:
    service, _, _ = chat()
    conversation = service.start()
    service.customer_message(conversation, "My OTP 482913 didn't arrive")
    service.customer_message(conversation, "I want to talk to a person, my account is 0012345678901")
    service.agent_reply(conversation, "Ana", "Thanks, I can see account 0012345678901")

    dump = "\n".join(service.db.iterdump())
    for secret in ("482913", "0012345678901"):
        assert secret not in dump
