"""The model clients: live Claude through the owner's API key, and recorded
answers for tests and CI, which need no key."""

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from anthropic.types import MessageParam
from pydantic import ValidationError

from help_assistant.model.answer import ModelAnswer
from help_assistant.model.request import ModelRequest

if TYPE_CHECKING:
    import anthropic

HAIKU = "claude-haiku-5-5"
SONNET = "claude-sonnet-5-5"


class Answerer(Protocol):
    @property
    def model(self) -> str: ...

    def answer(self, request: ModelRequest) -> str:
        """The model's raw answer: checked by `parse_answer` before anything trusts it."""
        ...


def recording_key(request: ModelRequest) -> str:
    """A hash of the exact request, so a changed prompt or model can't reuse an old answer."""
    return hashlib.sha256(request.to_json().encode()).hexdigest()


class ClaudeAnswerer:
    """Claude through the owner's API key (`ANTHROPIC_API_KEY`), never a subscription."""

    def __init__(self, model: str = HAIKU, client: "anthropic.Anthropic | None" = None) -> None:
        import anthropic  # loaded only when Claude is used live

        self.model = model
        self._client = client or anthropic.Anthropic()

    def answer(self, request: ModelRequest) -> str:
        messages: list[MessageParam] = [
            {"role": "user", "content": text} if role == "user" else {"role": "assistant", "content": text}
            for role, text in request.messages
        ]
        try:
            response = self._client.messages.parse(
                model=request.model,
                max_tokens=4096,
                system=request.system,
                messages=messages,
                output_format=ModelAnswer,
            )
        except ValidationError:
            # The SDK checks the answer against the type itself: an answer that
            # doesn't fit is "I don't know", not a crash (B3).
            return ""
        # A refusal or a cut-off answer has nothing usable: "I don't know".
        if response.stop_reason != "end_turn" or response.parsed_output is None:
            return ""
        return response.parsed_output.model_dump_json()


class NotRecordedError(KeyError):
    """No recorded answer for this exact request: record again with the API key."""


class RecordedAnswerer:
    """Replays recorded answers, keyed by the exact request."""

    def __init__(self, recordings: dict[str, str], model: str) -> None:
        self._recordings = recordings
        self.model = model

    def answer(self, request: ModelRequest) -> str:
        try:
            return self._recordings[recording_key(request)]
        except KeyError:
            raise NotRecordedError(recording_key(request)) from None


class RecordingAnswerer:
    """Asks the live model and saves each answer to `file` as it comes."""

    def __init__(self, live: Answerer, file: Path) -> None:
        self._live = live
        self._file = file
        self._recordings = load_recordings(file)
        self.model = live.model

    def answer(self, request: ModelRequest) -> str:
        raw = self._live.answer(request)
        self._recordings[recording_key(request)] = raw
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(self._recordings, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return raw


def load_recordings(file: Path) -> dict[str, str]:
    if not file.exists():
        return {}
    data: dict[str, str] = json.loads(file.read_text(encoding="utf-8"))
    return data
