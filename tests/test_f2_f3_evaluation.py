import json
from pathlib import Path

import pytest

from help_assistant.evaluation.grader import Grader
from help_assistant.evaluation.run import report, run, score
from help_assistant.evaluation.testset import load_questions
from help_assistant.model.client import HAIKU, SONNET, RecordedAnswerer, load_recordings
from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Searcher
from help_assistant.search.embeddings import FastEmbedder
from tests.fixtures.answerers import FakeAnswerer

QUESTIONS = load_questions(Path("evalset/questions.jsonl"))
PASSAGES = [p for page in read_pages(Path("help_pages")) for p in page.passages]
ANSWERS = Path("evalset/recorded/answers.json")
GRADES = Path("evalset/recorded/grades.json")


def first_passage_answer(request: object) -> str:
    """A stand-in model: cites the first passage found and quotes its first line."""
    from help_assistant.model.request import ModelRequest

    assert isinstance(request, ModelRequest)
    if not request.passage_ids:
        return json.dumps({"reply": "I don't know.", "cited": [], "confidence": 0.1, "handoff": "none"})
    return json.dumps(
        {"reply": "See this page.", "cited": [request.passage_ids[0]], "confidence": 0.9, "handoff": "none"}
    )


def test_c3_no_secret_in_any_test_question_reaches_a_model_request() -> None:
    results = run(
        QUESTIONS,
        Searcher(PASSAGES, None),
        FakeAnswerer(first_passage_answer),
        Grader(FakeAnswerer(lambda _: "")),
        "keyword",
    )
    assert [r.id for r in results if r.secret_reached_model] == []
    assert score(results).secrets_kept == 1.0


def test_f2_every_own_account_question_is_handed_off_by_the_rules_or_the_model() -> None:
    # With a stand-in that never hands off, what the rules alone catch is shown;
    # the rest rely on the model's hand-off, checked with recorded answers below.
    results = run(
        QUESTIONS,
        Searcher(PASSAGES, None),
        FakeAnswerer(first_passage_answer),
        Grader(FakeAnswerer(lambda _: "")),
        "keyword",
    )
    by_rules = [r for r in results if r.group == "own_account" and r.kind == "handoff"]
    assert len(by_rules) >= 10


def test_f3_the_report_has_a_row_for_each_model_and_search_mode() -> None:
    results = run(
        QUESTIONS[:5],
        Searcher(PASSAGES, None),
        FakeAnswerer(first_passage_answer),
        Grader(FakeAnswerer(lambda _: "")),
        "keyword",
    )
    rows = [
        (model, mode, score(results)) for model in ("haiku", "sonnet") for mode in ("keyword", "combined")
    ]
    table = report(rows)  # type: ignore[arg-type]
    assert table.count("\n| haiku |") + table.count("\n| sonnet |") == 4
    assert "Right answers" in table


@pytest.mark.skipif(
    not (ANSWERS.exists() and GRADES.exists()),
    reason="no recorded answers yet: run `help-assistant eval --record`",
)
def test_f2_the_recorded_answers_meet_the_targets() -> None:
    recordings = load_recordings(ANSWERS)
    grader = Grader(RecordedAnswerer(load_recordings(GRADES), SONNET))
    results = run(
        QUESTIONS, Searcher(PASSAGES, FastEmbedder()), RecordedAnswerer(recordings, HAIKU), grader, "combined"
    )
    scores = score(results)
    assert scores.meets_targets(), scores
