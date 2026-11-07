from pathlib import Path

import pytest

from help_assistant.core.secrets import redact
from help_assistant.model.client import NotRecordedError, RecordedAnswerer, RecordingAnswerer, recording_key
from help_assistant.model.request import ModelRequest, build_request
from tests.fixtures.answerers import FakeAnswerer, answer


def request(question: str, model: str = "fake-model") -> ModelRequest:
    return build_request(model, [], redact(question).text, [], "english")


def test_recorded_answers_are_replayed_for_the_exact_request_only(tmp_path: Path) -> None:
    file = tmp_path / "recorded.json"
    live = FakeAnswerer(lambda _: answer("Branches open at 8:00.", ["branch-hours#opening-hours"]))
    recorder = RecordingAnswerer(live, file)
    recorder.answer(request("When do branches open?"))

    replay = RecordedAnswerer(
        {recording_key(request("When do branches open?")): live.answer(request("x"))}, "fake-model"
    )
    assert "8:00" in replay.answer(request("When do branches open?"))
    with pytest.raises(NotRecordedError):
        replay.answer(request("When do branches close?"))
    assert file.exists()


def test_a_changed_model_or_prompt_doesnt_reuse_an_old_answer() -> None:
    assert recording_key(request("When do branches open?")) != recording_key(
        request("When do branches open?", model="another-model")
    )
