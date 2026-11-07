"""Stand-ins for Claude, for tests: made-up answers, no API key."""

import json
from collections.abc import Callable

from help_assistant.model.request import ModelRequest


class FakeAnswerer:
    """Answers each request with `answer(request)`, keeping every request seen."""

    model = "fake-model"

    def __init__(self, answer: Callable[[ModelRequest], str]) -> None:
        self._answer = answer
        self.seen: list[ModelRequest] = []

    def answer(self, request: ModelRequest) -> str:
        self.seen.append(request)
        return self._answer(request)


def answer(reply: str, cited: list[str], confidence: float = 0.9, handoff: str = "none") -> str:
    """A well-formed model answer."""
    return json.dumps({"reply": reply, "cited": cited, "confidence": confidence, "handoff": handoff})
