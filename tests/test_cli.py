from pathlib import Path

import pytest

from help_assistant.cli import main


def test_index_then_search_by_keywords(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = str(tmp_path / "help.db")
    assert main(["--db", db, "index"]) == 0
    assert main(["--db", db, "index"]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "0 passages added, 0 changed, 0 removed"

    assert main(["--db", db, "search", "OTP not arriving", "--mode", "keyword"]) == 0
    assert capsys.readouterr().out.startswith("login-and-otp#")


def test_search_before_indexing_says_what_to_do(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(["--db", str(tmp_path / "help.db"), "search", "hours"])


def test_ask_without_an_api_key_says_where_to_put_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db = str(tmp_path / "help.db")
    main(["--db", db, "index"])
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        main(
            [
                "--db",
                db,
                "--pages",
                str(Path(__file__).parent.parent / "help_pages"),
                "ask",
                "When do branches open?",
            ]
        )
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
