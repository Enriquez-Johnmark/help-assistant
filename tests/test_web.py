import logging
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from help_assistant.model.request import ModelRequest
from help_assistant.web.app import DEMO_NOTE, create_app
from tests.fixtures.service import chat

LOCAL = {"host": "127.0.0.1:8000"}


def client(model: Callable[[ModelRequest], str] | None = None) -> TestClient:
    service, _, _ = chat(model) if model else chat()
    return TestClient(create_app(service), headers=LOCAL)


def test_the_customer_chats_and_sees_an_agents_reply() -> None:
    web = client()
    conversation = web.post("/api/conversations").json()["id"]
    reply = web.post(
        f"/api/conversations/{conversation}/messages", json={"text": "My OTP didn't arrive"}
    ).json()
    assert reply["kind"] == "answer"
    handoff = web.post(
        f"/api/conversations/{conversation}/messages", json={"text": "Can I talk to a real person?"}
    )
    assert handoff.json()["kind"] == "handoff"

    assert (
        web.post(f"/api/agent/{conversation}/reply", json={"by": "Ana", "text": "Hi, Ana here."}).status_code
        == 200
    )
    messages = web.get(f"/api/conversations/{conversation}/messages").json()["messages"]
    assert [m["sender"] for m in messages][-1] == "agent"
    assert messages[-1]["text"] == "Hi, Ana here."


def test_e1_the_agents_page_lists_waiting_conversations_with_what_was_said() -> None:
    web = client()
    conversation = web.post("/api/conversations").json()["id"]
    web.post(f"/api/conversations/{conversation}/messages", json={"text": "Nawala ang pera sa wallet ko!"})
    page = web.get("/agent").text
    assert "Nawala ang pera sa wallet ko!" in page
    assert "Money" in page
    assert conversation in page


def test_e4_the_owners_page_shows_unanswered_topics_and_hand_off_reasons() -> None:
    web = client()
    for question in ("Do you offer travel insurance?", "I want to speak with a real agent"):
        conversation = web.post("/api/conversations").json()["id"]
        web.post(f"/api/conversations/{conversation}/messages", json={"text": question})
    page = web.get("/owner").text
    assert "asked_for_person" in page or "Asked for a person" in page


@pytest.mark.parametrize("path", ["/", "/agent", "/owner", "/pages/login-and-otp"])
def test_g2_every_page_says_it_is_a_demo_for_a_made_up_company(path: str) -> None:
    page = client().get(path)
    assert page.status_code == 200
    assert DEMO_NOTE in page.text
    assert DEMO_NOTE == "A demo for Halimbawa Money, a made-up company. Not affiliated with any real company."


def test_g1_it_answers_only_requests_addressed_to_this_computer() -> None:
    service, _, _ = chat()
    rebound = TestClient(create_app(service), headers={"host": "evil.example.test:8000"})
    assert rebound.get("/").status_code == 403
    assert TestClient(create_app(service), headers={"host": "localhost:8000"}).get("/").status_code == 200


def test_changes_from_another_site_are_refused() -> None:
    web = client()
    refused = web.post("/api/conversations", headers={"origin": "https://evil.example.test"})
    assert refused.status_code == 403


def test_g1_the_api_key_never_appears_in_an_answer_or_a_log(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import httpx2 as httpx  # what the Anthropic SDK is built on
    from anthropic import AuthenticationError

    key = "sk-ant-api03-MADE-UP-TEST-KEY-0000"
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)

    def leaky(_: object) -> str:
        response = httpx.Response(401, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
        raise AuthenticationError(f"invalid x-api-key: {key}", response=response, body=None)

    web = client(leaky)
    conversation = web.post("/api/conversations").json()["id"]
    with caplog.at_level(logging.DEBUG):
        answer = web.post(
            f"/api/conversations/{conversation}/messages", json={"text": "When do branches open?"}
        )
    assert answer.status_code == 502
    assert key not in answer.text
    assert key not in caplog.text
    for path in ("/", "/agent", "/owner", f"/api/conversations/{conversation}/messages"):
        assert key not in web.get(path).text


def test_bad_input_is_refused_plainly() -> None:
    web = client()
    conversation = web.post("/api/conversations").json()["id"]
    assert web.post(f"/api/conversations/{conversation}/messages", json={"text": ""}).status_code == 422
    assert (
        web.post(f"/api/conversations/{conversation}/messages", json={"text": "x", "extra": 1}).status_code
        == 422
    )
    assert web.post("/api/agent/nope/reply", json={"by": "Ana", "text": "hi"}).status_code == 400


def test_b1_an_answer_links_to_the_help_page_it_comes_from() -> None:
    web = client()
    conversation = web.post("/api/conversations").json()["id"]
    web.post(f"/api/conversations/{conversation}/messages", json={"text": "My OTP didn't arrive"})
    reply = web.get(f"/api/conversations/{conversation}/messages").json()["messages"][-1]
    [link] = reply["cited"]
    assert link["url"] == "/pages/login-and-otp#if-the-otp-doesn-t-arrive"
    page = web.get(link["url"]).text
    assert link["title"] in page
    assert 'id="if-the-otp-doesn-t-arrive"' in page


def test_what_a_customer_types_is_shown_as_text_not_run_as_html() -> None:
    web = client()
    conversation = web.post("/api/conversations").json()["id"]
    web.post(
        f"/api/conversations/{conversation}/messages",
        json={"text": "<script>alert(1)</script> Can I talk to a real person?"},
    )
    for path in ("/agent", f"/agent/{conversation}"):
        page = web.get(path).text
        assert "<script>alert(1)" not in page
        assert "&lt;script&gt;alert(1)" in page


def test_changes_from_another_program_on_this_computer_are_refused() -> None:
    web = client()
    other_port = web.post("/api/conversations", headers={"origin": "http://localhost:3000"})
    assert other_port.status_code == 403
    assert web.post("/api/conversations", headers={"origin": "http://127.0.0.1:8000"}).status_code == 200


def test_g2_a_missing_page_is_a_page_with_the_demo_note() -> None:
    web = client()
    for path in ("/agent/no-such-conversation", "/pages/no-such-page"):
        missing = web.get(path)
        assert missing.status_code == 404
        assert DEMO_NOTE in missing.text
    assert web.get("/api/conversations/nope/messages").json() == {"detail": "no such conversation"}


def test_times_are_shown_in_manila_time() -> None:
    web = client()
    conversation = web.post("/api/conversations").json()["id"]
    web.post(f"/api/conversations/{conversation}/messages", json={"text": "Can I talk to a real person?"})
    # The fixture's clock reads 02:00 UTC on 7 November 2026: 10:00 AM in Manila.
    for path in ("/agent", f"/agent/{conversation}", "/owner"):
        page = web.get(path).text
        assert "7 Nov 2026, 10:00 AM" in page
        assert "+00:00" not in page


def test_a_help_pages_table_is_shown_as_a_table() -> None:
    page = client().get("/pages/send-money-fees").text
    assert "<table" in page
    assert "<th>Amount sent</th>" in page
    assert "<td>Up to ₱1,000</td>" in page
    assert "| ---" not in page
