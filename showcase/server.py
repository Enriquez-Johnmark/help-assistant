"""The web app for screenshots and the walkthrough video.

By default its model refuses to be called: every conversation is one the rules
in code hand to a person before any model is asked, so nothing shown is a
model's answer. Run: uv run python showcase/server.py

With `--claude`, Claude Haiku answers with keyword search, as in `serve`. With
the owner's key each new answer is asked live and saved to CLAUDE_ANSWERS;
without one, the saved answers are replayed, so the screenshots and video can
be made again without a key. Run: uv run python showcase/server.py --claude
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import uvicorn

from help_assistant.assistant import Assistant
from help_assistant.env import load_env
from help_assistant.model.client import (
    HAIKU,
    Answerer,
    ClaudeAnswerer,
    RecordedAnswerer,
    RecordingAnswerer,
    load_recordings,
)
from help_assistant.model.request import ModelRequest
from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Searcher
from help_assistant.service import ChatService
from help_assistant.store.db import open_db
from help_assistant.store.passages import all_passages, save_pages
from help_assistant.web.app import create_app

CLAUDE_ANSWERS = Path("docs/showcase/claude-answers.json")


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


def claude() -> Answerer:
    load_env()
    if os.environ.get("ANTHROPIC_API_KEY"):
        return RecordingAnswerer(ClaudeAnswerer(HAIKU), CLAUDE_ANSWERS)
    return RecordedAnswerer(load_recordings(CLAUDE_ANSWERS), HAIKU)


def main() -> None:
    db = open_db(":memory:")
    save_pages(db, read_pages(Path("help_pages")))
    if "--claude" in sys.argv[1:]:
        assistant = Assistant(Searcher(all_passages(db), embedder=None), claude())
    else:
        assistant = Assistant(Searcher(all_passages(db), embedder=None), NoModel())
    app = create_app(ChatService(db, Ticking(), assistant))
    uvicorn.run(app, host="127.0.0.1", port=8013, log_level="warning")


if __name__ == "__main__":
    main()
