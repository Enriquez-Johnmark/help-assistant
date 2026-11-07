"""Reading help pages (Markdown with a short front matter) into passages."""

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class NotMadeUpError(ValueError):
    """A help page that doesn't say it is made up: refused (A3)."""


class Passage(BaseModel):
    """One section of a help page: what search finds and an answer cites."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    page: str
    heading: str
    text: str
    position: int


class HelpPage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str
    title: str
    topic: str
    passages: tuple[Passage, ...]


class FrontMatter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    topic: str = Field(pattern=r"^[a-z][a-z-]*$")
    made_up: bool


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _front_matter(text: str, name: str) -> tuple[dict[str, str | bool], str]:
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not match:
        raise NotMadeUpError(f"{name} has no front matter saying it is made up")
    fields: dict[str, str | bool] = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        fields[key.strip()] = value == "true" if value in ("true", "false") else value
    return fields, match.group(2)


def read_page(file: Path) -> HelpPage:
    """One help page. A page whose front matter doesn't say `made_up: true` is
    refused, so no real company's page can slip in (A3)."""
    fields, body = _front_matter(file.read_text(encoding="utf-8"), file.name)
    if fields.get("made_up") is not True:
        raise NotMadeUpError(f"{file.name} doesn't say it is made up (made_up: true)")
    try:
        front = FrontMatter.model_validate(fields)
    except ValidationError as error:
        raise ValueError(f"{file.name}: {error}") from error
    slug = file.stem
    intro, *sections = re.split(r"^## ", body, flags=re.M)
    # Before the first section only the title and the made-up note may stand:
    # anything else would never be found, so it is refused rather than dropped.
    stray = [line for line in intro.splitlines() if line.strip() and not line.startswith(("# ", "> "))]
    if stray:
        raise ValueError(f"{file.name} has text outside a section: {stray[0][:60]!r}")
    if not sections:
        raise ValueError(f"{file.name} has no sections (## headings), so nothing in it could be found")
    passages: list[Passage] = []
    seen: set[str] = set()
    for position, section in enumerate(sections):
        heading, _, content = section.partition("\n")
        heading = heading.strip()
        if _slug(heading) in seen:
            raise ValueError(f"{file.name} has two sections headed {heading!r}")
        seen.add(_slug(heading))
        passages.append(
            Passage(
                id=f"{slug}#{_slug(heading)}",
                page=slug,
                heading=heading,
                text=f"{heading}\n{content.strip()}",
                position=position,
            )
        )
    return HelpPage(slug=slug, title=front.title, topic=front.topic, passages=tuple(passages))


def read_pages(folder: Path) -> list[HelpPage]:
    """Every help page in `folder`, in name order."""
    return [read_page(file) for file in sorted(folder.glob("*.md"))]
