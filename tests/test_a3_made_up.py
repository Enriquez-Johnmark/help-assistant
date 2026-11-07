import json
from pathlib import Path

from help_assistant.made_up import not_made_up

PAGE = "---\ntitle: Branch hours\ntopic: branches\nmade_up: true\n---\n\n## Opening hours\n8 to 6.\n"


def test_a3_the_repositorys_help_pages_and_questions_are_all_marked_made_up() -> None:
    assert not_made_up(Path()) == []


def test_a3_a_help_page_not_marked_made_up_is_found(tmp_path: Path) -> None:
    (tmp_path / "help_pages").mkdir()
    (tmp_path / "help_pages" / "ok.md").write_text(PAGE)
    (tmp_path / "help_pages" / "real.md").write_text(PAGE.replace("made_up: true", "made_up: false"))

    assert not_made_up(tmp_path) == ["help_pages/real.md: doesn't say it is made up (made_up: true)"]


def test_a3_a_test_question_not_marked_made_up_is_found(tmp_path: Path) -> None:
    (tmp_path / "evalset").mkdir()
    lines = [{"id": "q1", "made_up": True}, {"id": "q2"}, {"id": "q3", "made_up": "yes"}]
    (tmp_path / "evalset" / "questions.jsonl").write_text(
        "\n".join(json.dumps(line) for line in lines) + "\n"
    )

    assert not_made_up(tmp_path) == [
        "evalset/questions.jsonl line 2: doesn't say it is made up",
        "evalset/questions.jsonl line 3: doesn't say it is made up",
    ]


def test_a3_a_test_question_line_that_isnt_json_is_reported_not_a_crash(tmp_path: Path) -> None:
    (tmp_path / "evalset").mkdir()
    (tmp_path / "evalset" / "questions.jsonl").write_text('{"id": "q1", "made_up": true}\n{not json\n')

    assert not_made_up(tmp_path) == ["evalset/questions.jsonl line 2: isn't valid JSON"]
