"""A chat service over the made-up help pages, with a stand-in model."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from help_assistant.assistant import Assistant
from help_assistant.clock import FixedClock
from help_assistant.model.request import ModelRequest
from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Searcher
from help_assistant.service import ChatService
from help_assistant.store.db import open_db
from help_assistant.store.passages import all_passages, save_pages
from tests.fixtures.answerers import FakeAnswerer, answer


def otp_or_unsure(request: ModelRequest) -> str:
    """Answers OTP questions from the OTP page; is unsure about anything else."""
    question = request.messages[-1][1].lower()
    if "otp" in question:
        return answer("Wait 2 minutes, then tap Resend.", ["login-and-otp#if-the-otp-doesn-t-arrive"])
    return answer("Not sure.", [], confidence=0.2)


def chat(
    model: Callable[[ModelRequest], str] = otp_or_unsure,
) -> tuple[ChatService, FixedClock, FakeAnswerer]:
    db = open_db(":memory:")
    save_pages(db, read_pages(Path("help_pages")))
    clock = FixedClock(datetime(2026, 11, 7, 2, 0, tzinfo=UTC))
    fake = FakeAnswerer(model)
    assistant = Assistant(Searcher(all_passages(db), embedder=None), fake, mode="keyword")
    return ChatService(db, clock, assistant), clock, fake
