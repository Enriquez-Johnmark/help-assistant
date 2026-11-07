"""The model's answer, exactly as it must arrive. Anything else is refused."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ModelAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: str
    cited: list[str]
    confidence: float = Field(ge=0, le=1)
    handoff: Literal["none", "own_account", "asked_for_person", "lost_money"]


def parse_answer(raw: str) -> ModelAnswer | None:
    """The answer in `raw`, or `None` if it isn't exactly the agreed shape (B3)."""
    try:
        return ModelAnswer.model_validate_json(raw)
    except ValidationError:
        return None
