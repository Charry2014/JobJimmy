#!/usr/bin/env python3
"""Verify the JobJimmy environment: Python, external tools, private tree and API keys.

Secret values are never read into output: API keys and model identifiers are
reported only as set or missing. Exit status is non-zero only when an
unconditionally required component (Python version, uv or git) is unavailable.
Missing optional keys and a missing private tree are reported as signals for the
calling workflow to resolve with the user.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

MIN_PYTHON = (3, 11)
SOFFICE_FALLBACK = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")

KEYS = (
    ("OPENROUTER_API_KEY", "English-to-German CV translation (optional)"),
    ("OPENROUTER_MODEL", "OpenRouter model id for translation (optional)"),
    ("TYPESAFE_API_KEY", "live Jev fit and document checks (optional)"),
)


def tool_status(which=shutil.which) -> dict:
    return {
        "uv": bool(which("uv")),
        "git": bool(which("git")),
        "libreoffice": bool(which("soffice")) or SOFFICE_FALLBACK.exists(),
    }


def key_status(environ=None) -> dict:
    environ = os.environ if environ is None else environ
    return {
        name: {"set": bool(environ.get(name)), "purpose": purpose}
        for name, purpose in KEYS
    }


def check(root=None, environ=None, which=shutil.which, version_info=None) -> dict:
    version_info = sys.version_info if version_info is None else version_info
    python_ok = version_info[:2] >= MIN_PYTHON
    tools = tool_status(which)
    keys = key_status(environ)
    private_tree = (Path(root) / "JobSearch").exists() if root else None
    required_ok = python_ok and tools["uv"] and tools["git"]
    return {
        "ok": required_ok,
        "python": {
            "ok": python_ok,
            "version": ".".join(str(part) for part in version_info[:3]),
            "required": ".".join(str(part) for part in MIN_PYTHON),
        },
        "tools": tools,
        "keys": keys,
        "missing_keys": [name for name, item in keys.items() if not item["set"]],
        "private_tree": private_tree,
    }


def render_text(result: dict) -> str:
    lines = ["JobJimmy environment check"]
    python = result["python"]
    lines.append(
        "  python       {:<8} {} (needs >= {})".format(
            "ok" if python["ok"] else "MISSING", python["version"], python["required"]
        )
    )
    for name, required in (("uv", True), ("git", True), ("libreoffice", False)):
        present = result["tools"][name]
        label = "ok" if present else ("MISSING" if required else "absent")
        note = "" if required else " (optional; needed for document export)"
        lines.append("  {:<12} {}{}".format(name, label, note))
    if result["private_tree"] is not None:
        lines.append(
            "  private tree {}".format("present" if result["private_tree"] else "MISSING")
        )
    lines.append("API keys (values never shown)")
    for name, item in result["keys"].items():
        state = "set" if item["set"] else "missing"
        lines.append("  {:<22} {:<8} {}".format(name, state, item["purpose"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="project root used to detect the private JobSearch tree",
    )
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args(argv)

    result = check(root=args.root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
