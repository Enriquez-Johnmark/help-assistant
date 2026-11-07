"""Reading `.env`, where the owner's API key is kept out of git."""

import os
from pathlib import Path


def load_env(file: Path = Path(".env")) -> None:
    """Sets each `NAME=value` in `file` that isn't set already. Quotes around a
    value are removed; empty values and comments are skipped."""
    if not file.exists():
        return
    for line in file.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not sep or not name or name.startswith("#"):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            os.environ.setdefault(name, value)
