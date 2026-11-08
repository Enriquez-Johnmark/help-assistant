"""Reading `.env`, where the owner's API key is kept out of git."""

import os
from pathlib import Path

# In a cloud session the owner's key is kept under this name: Claude Code itself
# reads ANTHROPIC_API_KEY, and the owner's key must pay for this app only.
CLOUD_KEY = "OWNER_ANTHROPIC_API_KEY"


def load_env(file: Path = Path(".env")) -> None:
    """Sets each `NAME=value` in `file` that isn't set already. Quotes around a
    value are removed; empty values and comments are skipped. Without a key in
    `.env` or the environment, the owner's key under `CLOUD_KEY` is used."""
    if file.exists():
        _read(file)
    if not os.environ.get("ANTHROPIC_API_KEY") and os.environ.get(CLOUD_KEY):
        os.environ["ANTHROPIC_API_KEY"] = os.environ[CLOUD_KEY]


def _read(file: Path) -> None:
    for line in file.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not sep or not name or name.startswith("#"):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            os.environ.setdefault(name, value)
