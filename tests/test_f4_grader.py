from pathlib import Path

import pytest

from help_assistant.evaluation.grader import Grader, grade_request, load_grading_cases
from help_assistant.model.client import SONNET, RecordedAnswerer, load_recordings
from tests.fixtures.answerers import FakeAnswerer

CASES = load_grading_cases(Path("evalset/grading_cases.jsonl"))
GRADES = Path("evalset/recorded/grades.json")


def test_f4_the_grader_reads_a_grade_and_counts_an_unreadable_one_as_none() -> None:
    right = Grader(FakeAnswerer(lambda _: '{"correct": true, "reason": "same fee"}'))
    garbled = Grader(FakeAnswerer(lambda _: "yes I think so"))
    grade = right.grade("Fee?", "₱15.", "It costs ₱15.")
    assert grade is not None
    assert grade.correct
    assert garbled.grade("Fee?", "₱15.", "It costs ₱15.") is None


def test_f4_the_grader_is_sent_the_three_texts_redacted() -> None:
    request = grade_request(SONNET, "My PIN is 482913, why?", "Never share it.", "Ok")
    assert "482913" not in request.to_json()


def test_f4_the_grading_cases_have_right_and_wrong_replies() -> None:
    assert len(CASES) == 20
    assert {case.correct for case in CASES} == {True, False}


@pytest.mark.skipif(
    not GRADES.exists(), reason="Claude's grades aren't recorded yet: run `help-assistant eval --record`"
)
def test_f4_claude_grades_made_up_right_and_wrong_replies_as_they_should_be() -> None:
    grader = Grader(RecordedAnswerer(load_recordings(GRADES), SONNET))
    wrong: list[str] = []
    for case in CASES:
        grade = grader.grade(case.question, case.answer, case.reply)
        if grade is None or grade.correct != case.correct:
            wrong.append(case.id)
    assert wrong == []
