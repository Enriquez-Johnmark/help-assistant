from pathlib import Path

import pytest

from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Searcher
from help_assistant.search.embeddings import FastEmbedder
from tests.fixtures.tagalog_questions import QUESTIONS


@pytest.fixture(scope="module")
def searcher() -> Searcher:
    passages = [p for page in read_pages(Path("help_pages")) for p in page.passages]
    return Searcher(passages, embedder=FastEmbedder())


def top_pages(searcher: Searcher, question: str, mode: str) -> list[str]:
    return [hit.passage.page for hit in searcher.search(question, 5, mode=mode)]  # type: ignore[arg-type]


def test_a2_a_tagalog_or_taglish_question_finds_its_english_page_in_the_top_5(searcher: Searcher) -> None:
    found = [page in top_pages(searcher, question, "combined") for question, page in QUESTIONS]
    missed = [question for (question, _), ok in zip(QUESTIONS, found, strict=True) if not ok]
    assert sum(found) / len(found) >= 0.9, f"missed: {missed}"
