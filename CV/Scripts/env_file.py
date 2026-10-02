#!/usr/bin/env python3
"""Local .env fallback for required keys and paths.

Reading required keys and path settings from the shell is error-prone, so the
scripts fall back to an optional ``.env`` file at the repository root. The file
is never committed (see .gitignore) and its values are read into memory only,
never printed. A variable already present in the process environment always wins
over the file, so exported values and IDE/secret-manager environments keep
precedence.

Format (one ``KEY=VALUE`` per line, ``#`` comments, optional ``export`` and
single/double quotes)::

    OPENROUTER_API_KEY=sk-...
    OPENROUTER_MODEL=<provider>/<model-id>
    OPENROUTER_TRANSLATION_GUIDANCE=CV/Translation/german.json
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ENV_FILENAME = ".env"
_EXPORT = re.compile(r"^export\s+")
_INLINE_COMMENT = re.compile(r"\s+#")


def find_env_file(*starts: Path) -> Path | None:
    """Return the nearest .env searching each start upward, or None.

    Starts default to the current directory and this module's directory, so the
    repository-root .env is found whether a script is run from the project root
    or directly from ``CV/Scripts``.
    """
    seen: set[Path] = set()
    for start in starts or (Path.cwd(), Path(__file__).resolve().parent):
        base = Path(start).resolve()
        for directory in (base, *base.parents):
            if directory in seen:
                continue
            seen.add(directory)
            candidate = directory / ENV_FILENAME
            if candidate.is_file():
                return candidate
    return None


def parse_env(text: str) -> dict[str, str]:
    """Parse .env content into a name-to-value mapping."""
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = _EXPORT.sub("", line)
        if "=" not in line:
            continue
        name, _, raw_value = line.partition("=")
        name = name.strip()
        if not name:
            continue
        values[name] = _parse_value(raw_value)
    return values


def _parse_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if value[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\n", "\n")
        return inner
    match = _INLINE_COMMENT.search(value)
    if match:
        value = value[: match.start()]
    return value.strip()


def load_env_file(path: Path | str | None = None, environ: dict | None = None) -> dict:
    """Populate ``environ`` (default ``os.environ``) from the nearest .env.

    Existing variables are never overridden. Returns the environment mapping.
    Missing or unreadable files are ignored; the fallback is always optional.
    """
    environ = os.environ if environ is None else environ
    candidate = Path(path) if path else find_env_file()
    if candidate is None or not candidate.is_file():
        return environ
    try:
        text = candidate.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return environ
    for name, value in parse_env(text).items():
        if not environ.get(name):
            environ[name] = value
    return environ


def get(name: str, default=None, path: Path | str | None = None, environ: dict | None = None):
    """Return an environment value, falling back to the nearest .env."""
    environ = os.environ if environ is None else environ
    if environ.get(name):
        return environ[name]
    load_env_file(path=path, environ=environ)
    return environ.get(name, default)
