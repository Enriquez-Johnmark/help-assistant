"""The web app for screenshots, with a model that refuses to be called.

Every conversation the screenshots show is handed to a person by the rules in
code before any model is asked, so nothing in them is a model's answer. If a
message ever reached the model, the request would fail and the screenshot
script with it. Run: uv run python showcase/server.py
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import uvicorn

from help_assistant.assistant import Assistant
from help_assistant.model.request import ModelRequest
from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Searcher
from help_assistant.service import ChatService
from help_assistant.store.db import open_db
from help_assistant.store.passages import all_passages, save_pages
from help_assistant.web.app import create_app


class NoModel:
    model = "none"

    def answer(self, request: ModelRequest) -> str:
        raise RuntimeError("the showcase never asks the model")


class Ticking:
    """A made-up morning: 9:00 Manila time, a minute later each time it is read."""

    def __init__(self) -> None:
        self._at = datetime(2026, 11, 9, 1, 0, tzinfo=UTC)

    def now(self) -> datetime:
        self._at += timedelta(minutes=1)
        return self._at


def main() -> None:
    db = open_db(":memory:")
    save_pages(db, read_pages(Path("help_pages")))
    assistant = Assistant(Searcher(all_passages(db), embedder=None), NoModel(), mode="keyword")
    app = create_app(ChatService(db, Ticking(), assistant))
    uvicorn.run(app, host="127.0.0.1", port=8013, log_level="warning")


if __name__ == "__main__":
    main()
