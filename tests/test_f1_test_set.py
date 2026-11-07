from collections import Counter
from pathlib import Path

from help_assistant.evaluation.testset import load_questions
from help_assistant.pages.reader import read_pages


def test_f1_the_test_set_has_about_150_made_up_questions_in_the_five_groups() -> None:
    questions = load_questions(Path("evalset/questions.jsonl"))
    groups = Counter(q.group for q in questions)

    assert 140 <= len(questions) <= 160
    assert groups == {
        "answerable_english": 60,
        "answerable_tagalog": 40,
        "not_in_pages": 20,
        "own_account": 15,
        "tricky": 15,
    }
    assert len({q.id for q in questions}) == len(questions)


def test_f1_every_answerable_question_has_its_right_answer_and_real_source_pages() -> None:
    pages = {page.slug for page in read_pages(Path("help_pages"))}
    for question in load_questions(Path("evalset/questions.jsonl")):
        if question.group.startswith("answerable"):
            assert question.answer, question.id
            assert question.pages, question.id
            assert set(question.pages) <= pages, question.id
