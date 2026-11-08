import os
from pathlib import Path

import pytest

from help_assistant.env import load_env


def test_env_values_are_read_with_or_without_quotes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ONE", "TWO", "THREE", "EMPTY"):
        monkeypatch.delenv(name, raising=False)
    file = tmp_path / ".env"
    file.write_text("# a comment\nONE=plain\nTWO=\"double quoted\"\nTHREE='single'\nEMPTY=\n")

    load_env(file)

    import os

    assert (os.environ["ONE"], os.environ["TWO"], os.environ["THREE"]) == ("plain", "double quoted", "single")
    assert "EMPTY" not in os.environ


def test_a_value_already_set_is_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONE", "from the shell")
    (tmp_path / ".env").write_text("ONE=from the file\n")
    load_env(tmp_path / ".env")
    import os

    assert os.environ["ONE"] == "from the shell"


def test_the_owners_key_under_its_cloud_name_is_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Set, then removed, so the test leaves no key behind for the others.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.setenv("OWNER_ANTHROPIC_API_KEY", "sk-ant-made-up")
    load_env(tmp_path / "missing.env")
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-made-up"


def test_a_key_in_env_wins_over_the_cloud_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Set, then removed, so the test leaves no key behind for the others.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.setenv("OWNER_ANTHROPIC_API_KEY", "sk-ant-cloud")
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-ant-local\n")
    load_env(env)
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-local"
