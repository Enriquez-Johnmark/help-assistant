"""Every help page and every test question must say it is made up (A3)."""

import json
from pathlib import Path

from help_assistant.pages.reader import NotMadeUpError, read_page


def not_made_up(root: Path) -> list[str]:
    """What in `root` isn't marked made up: help pages without `made_up: true`,
    and test questions (one JSON object per line) without `"made_up": true`."""
    problems: list[str] = []
    for file in sorted((root / "help_pages").glob("*.md")):
        try:
            read_page(file)
        except NotMadeUpError:
            problems.append(f"help_pages/{file.name}: doesn't say it is made up (made_up: true)")
    for file in sorted((root / "evalset").glob("*.jsonl")):
        for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            record: object = json.loads(line)
            if not (isinstance(record, dict) and record.get("made_up") is True):  # pyright: ignore[reportUnknownMemberType]
                problems.append(f"evalset/{file.name} line {number}: doesn't say it is made up")
    return problems


def main() -> int:
    problems = not_made_up(Path())
    for problem in problems:
        print(problem)
    print(f"{len(problems)} not marked made up" if problems else "Everything is marked made up.")
    return 1 if problems else 0
