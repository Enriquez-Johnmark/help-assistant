from pathlib import Path

import pytest

from help_assistant.evaluation.testset import load_questions
from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Mode, Searcher
from help_assistant.search.embeddings import FastEmbedder
from tests.fixtures.tagalog_questions import QUESTIONS

TAGALOG = [q for q in load_questions(Path("evalset/questions.jsonl")) if q.group == "answerable_tagalog"]


@pytest.fixture(scope="module")
def searcher() -> Searcher:
    passages = [p for page in read_pages(Path("help_pages")) for p in page.passages]
    return Searcher(passages, embedder=FastEmbedder())


def share_found(searcher: Searcher, questions: list[tuple[str, list[str]]], mode: Mode) -> float:
    found = [
        bool({h.passage.page for h in searcher.search(q, 5, mode=mode)} & set(pages))
        for q, pages in questions
    ]
    return sum(found) / len(found)


def test_a2_a_tagalog_or_taglish_question_finds_its_english_page_in_the_top_5(searcher: Searcher) -> None:
    # The test set's Tagalog and Taglish questions, which search wasn't tuned on.
    assert share_found(searcher, [(q.question, q.pages) for q in TAGALOG], "combined") >= 0.9


def test_a2_the_search_questions_it_was_tuned_on_still_pass(searcher: Searcher) -> None:
    assert share_found(searcher, [(q, [page]) for q, page in QUESTIONS], "combined") >= 0.9


def test_search_is_by_keyword_unless_asked_so_it_needs_no_embedding_model() -> None:
    searcher = Searcher([p for page in read_pages(Path("help_pages")) for p in page.passages], embedder=None)
    hits = searcher.search("How much is the fee to send money?", 5)
    assert hits[0].passage.id.startswith("send-money-fees")
