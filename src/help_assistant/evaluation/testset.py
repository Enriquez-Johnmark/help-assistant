"""The test set: made-up questions with their right answers (F1)."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

Group = Literal["answerable_english", "answerable_tagalog", "not_in_pages", "own_account", "tricky"]
Expect = Literal["answer", "i_dont_know", "handoff", "safe"]


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    group: Group
    question: str
    answer: str
    pages: list[str]
    expect: Expect
    secrets: list[str] = []
    made_up: Literal[True]


def load_questions(file: Path) -> list[Question]:
    """Every question in `file`, one JSON object per line, read strictly."""
    lines = file.read_text(encoding="utf-8").splitlines()
    return [Question.model_validate_json(line) for line in lines if line.strip()]
