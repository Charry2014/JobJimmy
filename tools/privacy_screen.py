#!/usr/bin/env python3
"""Privacy screening gate for the public JobJimmy repository.

Screens changes in the outer (public) project repository for personal data.
Personal data may exist only inside the private JobSearch/ tree; anything this
script flags must be fixed (moved into JobSearch/, genericised or removed)
before the change is staged, committed or pushed.

The script derives its identifier lists at runtime from the private JobSearch
tree and stores nothing: no personal value is printed, embedded or cached.
Generic patterns (emails, phones, profile URLs, IBANs) use only documented
fictional/placeholder allowlists.

Usage:
    python3 tools/privacy_screen.py             # screen current working-tree changes
    python3 tools/privacy_screen.py --all       # current files including ignored outputs
    python3 tools/privacy_screen.py -- file1 file2 ...

Exit codes: 0 = clean, 1 = violations found, 2 = could not run the screen.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = (".git", "JobSearch", "node_modules", "__pycache__")
# Vendored third-party code (installed Obsidian plugins) is not user content.
VENDORED_PREFIXES = (".obsidian/plugins/",)
# The screen's own test file contains synthetic fixtures by design; scanning it
# would flag fictional examples forever. Reasoned diff review still applies.
SCREEN_FIXTURE_FILES = {"tools/test_privacy_screen.py"}
# Inline suppression marker: a line containing this is treated as deliberate
# synthetic content and skipped. Keep it visible in diffs and code review.
ALLOW_MARKER = "privacy-screen: allow"
DOCUMENT_SUFFIXES = {".pdf", ".odt", ".ott", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".heic", ".tif", ".tiff"}
PRIVATE_TREE = "JobSearch"

ALLOWED_EMAIL_DOMAINS = {
    "example.com", "example.net", "example.org", "example.edu",
    "example.invalid", "example.test", "example.localhost",
}
ALLOWED_LINKEDIN_SLUGS = {
    "your-name", "yourname", "your-profile", "username", "your-linkedin", "in",
}
# Media-industry fictional phone range (555-0100..0199) and similar placeholders.
FICTIONAL_PHONE = re.compile(r"555[ \-().]?01\d\d")


class Finding:
    __slots__ = ("category", "path", "line", "hint")

    def __init__(self, category: str, path: str, line: int, hint: str = "") -> None:
        self.category = category
        self.path = path
        self.line = line
        self.hint = hint


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _frontmatter_values(text: str, keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    if not text.startswith("---"):
        return values
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return values
    for line in lines[1:]:
        if line.strip() in ("---", "..."):
            break
        match = re.match(r"^([A-Za-z][A-Za-z0-9_]*):\s*(.*?)\s*$", line)
        if match and match.group(1).lower() in keys and match.group(2):
            value = match.group(2).strip().strip("'\"")
            value = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", value)
            if value:
                values.append(value)
    return values


def derive_identifiers(private_root: Path) -> list[tuple[str, str]]:
    """Extract (category, value) pairs from the private tree. Never printed."""
    identifiers: list[tuple[str, str]] = []

    def add(category: str, value: str) -> None:
        value = value.strip()
        if len(value) >= 3:
            identifiers.append((category, value))

    knowledge = private_root / "Knowledge"
    if knowledge.is_dir():
        for note in knowledge.glob("*.md"):
            for value in _frontmatter_values(note.read_text(encoding="utf-8", errors="replace"), ("subject",)):
                add("candidate-name", value)

    companies = private_root / "Companies"
    if companies.is_dir():
        for note in companies.glob("*.md"):
            for value in _frontmatter_values(note.read_text(encoding="utf-8", errors="replace"), ("company",)):
                add("company-name", value)

    recruiters = private_root / "Recruiters"
    if recruiters.is_dir():
        for note in recruiters.glob("*.md"):
            text = note.read_text(encoding="utf-8", errors="replace")
            for value in _frontmatter_values(text, ("recruitment_company", "recruiter_name")):
                add("recruiter-identity", value)
            for value in _frontmatter_values(text, ("email",)):
                add("recruiter-email", value)
            for value in _frontmatter_values(text, ("phone",)):
                add("recruiter-phone", value)
            for value in _frontmatter_values(text, ("linkedin",)):
                add("recruiter-linkedin", value)

    applications = private_root / "Applications"
    if applications.is_dir():
        for folder in applications.iterdir():
            if folder.is_dir() and not folder.name.startswith("."):
                add("application-slug", folder.name)
                stem = re.sub(r"^\d{4}-\d{2}-", "", folder.name)
                if stem != folder.name:
                    add("application-slug", stem)

    return identifiers


def _word_pattern(category: str, value: str) -> tuple[str, re.Pattern]:
    return (category, re.compile(r"\b" + re.escape(value) + r"\b", re.IGNORECASE))


def _literal_pattern(category: str, value: str) -> tuple[str, re.Pattern]:
    return (category, re.compile(re.escape(value), re.IGNORECASE))


def generic_patterns() -> list[tuple[str, re.Pattern]]:
    email = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)", re.IGNORECASE)
    phone = re.compile(r"\+\d{1,3}[\s().-]{0,2}\(?\d{1,6}\)?(?:[\s().-]{0,2}\d{2,6}){2,4}")
    linkedin = re.compile(r"linkedin\.com/in/([A-Za-z0-9_%-]{2,})", re.IGNORECASE)
    iban = re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}\b")
    dob = re.compile(r"(?i)\b(date of birth|geburtsdatum)\b\s*[:=]")
    knowledge_path = re.compile(r"JobSearch/Knowledge/Sources/[A-Za-z0-9_-]+")
    return [
        ("email", email),
        ("phone", phone),
        ("linkedin-profile", linkedin),
        ("iban", iban),
        ("dob-label", dob),
        ("private-knowledge-path", knowledge_path),
    ]


def screen_text(text: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for category, regex in generic_patterns():
            for match in regex.finditer(line):
                if category == "email":
                    domain = match.group(1).lower().rstrip(".")
                    if any(domain == d or domain.endswith("." + d) for d in ALLOWED_EMAIL_DOMAINS):
                        continue
                if category == "linkedin-profile" and match.group(1).lower() in ALLOWED_LINKEDIN_SLUGS:
                    continue
                if category == "phone" and FICTIONAL_PHONE.search(match.group(0)):
                    continue
                if category == "phone" and not re.search(r"[1-9]", match.group(0)[1:]):
                    continue
                hits.append((category, line_no, match.group(0)))
        for category, regex in derived_patterns_cache:
            for match in regex.finditer(line):
                hits.append((category, line_no, match.group(0)))
    return hits


derived_patterns_cache: list[tuple[str, re.Pattern]] = []


def set_derived_patterns(identifiers: list[tuple[str, str]]) -> None:
    global derived_patterns_cache
    patterns: list[tuple[str, re.Pattern]] = []
    seen: set[tuple[str, str]] = set()
    for category, value in identifiers:
        key = (category, value.lower())
        if key in seen:
            continue
        seen.add(key)
        if category in ("recruiter-email", "recruiter-phone", "recruiter-linkedin"):
            patterns.append(_literal_pattern(category, value))
        else:
            patterns.append(_word_pattern(category, value))
    derived_patterns_cache = patterns


def mask(value: str) -> str:
    return "[redacted]"


def git_paths(root: Path, *args: str) -> set[str]:
    """NUL-delimited paths preserve spaces, Unicode and embedded newlines."""
    return set(filter(None, _run_git(root, *args, "-z").split("\0")))


def excluded(rel: str) -> bool:
    return (rel in SCREEN_FIXTURE_FILES or rel.startswith(VENDORED_PREFIXES)
            or any(part in SKIP_DIRS for part in Path(rel).parts))


def gather_targets(root: Path, mode: str, extra_paths: list[str]) -> list[tuple[Path, bool]]:
    added = git_paths(root, "diff", "--cached", "--name-only", "--diff-filter=A")
    untracked = git_paths(root, "ls-files", "--others", "--exclude-standard")
    names = set(extra_paths)
    if mode in ("all", "changed"):
        names |= untracked | git_paths(root, "diff", "--name-only")
        names |= git_paths(root, "diff", "--cached", "--name-only")
    if mode == "all":
        names |= git_paths(root, "ls-files")
        # Ignored outputs are still a filesystem privacy exposure.
        ignored = git_paths(root, "ls-files", "--others", "--ignored", "--exclude-standard")
        names |= ignored
        untracked |= ignored
    targets = []
    for name in sorted(names):
        path = root / name
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            raise RuntimeError("Screen paths must be inside the public workspace.") from None
        if ".." in Path(rel).parts:
            raise RuntimeError("Screen paths must not contain parent traversal.")
        if excluded(rel):
            continue
        if path.is_symlink() or path.is_file():
            targets.append((path, name in added or name in untracked))
    return targets


def screen_bytes(rel: str, data: bytes, added: bool = False) -> list[Finding]:
    findings = [Finding("filename-" + category, rel, 0)
                for category, _, _ in screen_text(rel)]
    if added and Path(rel).suffix.lower() in DOCUMENT_SUFFIXES:
        findings.append(Finding("document-file-added-to-public-repo", rel, 0))
    if b"\0" not in data[:8192]:
        findings.extend(Finding(category, rel, line_no)
                        for category, line_no, _ in screen_text(data.decode("utf-8", errors="replace")))
    return findings


def screen_targets(root: Path, targets: list[tuple[Path, bool]]) -> list[Finding]:
    findings = []
    private = root / PRIVATE_TREE
    for path, added in targets:
        rel = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            findings.append(Finding("public-symlink-or-path-escape", rel, 0))
            continue
        if path.resolve().is_relative_to(private.resolve()):
            findings.append(Finding("private-tree-file-in-public-repo", rel, 0))
            continue
        findings.extend(screen_bytes(rel, path.read_bytes(), added))
    return findings


def screen_index(root: Path, all_files: bool = False) -> list[Finding]:
    """Check the actual index, including private paths before any exclusions."""
    findings = []
    selected = git_paths(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRT")
    added = git_paths(root, "diff", "--cached", "--name-only", "--diff-filter=A")
    entries = _run_git(root, "ls-files", "--stage", "-z").split("\0")
    for entry in filter(None, entries):
        info, rel = entry.split("\t", 1)
        mode, oid, stage = info.split()
        if rel == PRIVATE_TREE or rel.startswith(PRIVATE_TREE + "/"):
            findings.append(Finding("private-tree-file-in-public-index", rel, 0))
            continue
        if excluded(rel) or (not all_files and rel not in selected):
            continue
        if stage != "0":
            findings.append(Finding("unmerged-index-entry", rel, 0))
            continue
        if mode in ("120000", "160000"):
            findings.append(Finding("public-link-in-index", rel, 0))
            continue
        result = subprocess.run(["git", "-C", str(root), "cat-file", "blob", oid], capture_output=True)
        if result.returncode:
            raise RuntimeError("Unable to read an indexed blob.")
        findings.extend(screen_bytes(rel, result.stdout, rel in added))
    return findings


def report(findings: list[Finding], identifiers_count: int, private_present: bool) -> int:
    if not findings:
        print(f"PRIVACY SCREEN CLEAN — no personal-data findings "
              f"({identifiers_count} private identifiers screened, "
              f"private tree {'present' if private_present else 'ABSENT — generic patterns only'}).")
        return 0
    files = sorted({f.path for f in findings})
    print(f"PRIVACY VIOLATIONS FOUND — {len(findings)} findings in {len(files)} file(s). "
          f"Personal data must not enter the public repository; fix before staging, "
          f"committing or pushing (move to JobSearch/, genericise or remove).")
    for path in files:
        for finding in findings:
            if finding.path != path:
                continue
            location = f"{finding.path}:{finding.line}" if finding.line else finding.path
            hint = f" matched {finding.hint!r}" if finding.hint else ""
            print(f"  [{finding.category}] {location}{hint}")
    return 1


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Privacy screen for the public JobJimmy repository.")
    parser.add_argument("--all", action="store_true", help="screen every tracked and untracked file, not just changes")
    parser.add_argument("paths", nargs="*", help="explicit file paths to screen (used without --all/--changed scan)")
    args = parser.parse_args(argv)

    root = (root or Path(__file__).resolve().parent.parent).resolve()
    try:
        _run_git(root, "rev-parse", "--show-toplevel")
    except RuntimeError as error:
        print(f"PRIVACY SCREEN ERROR — not a git repository? {error}", file=sys.stderr)
        return 2

    private_root = root / PRIVATE_TREE
    private_present = private_root.is_dir()
    try:
        identifiers = derive_identifiers(private_root) if private_present else []
    except OSError:
        print("PRIVACY SCREEN ERROR — unable to read local identifier sources.", file=sys.stderr)
        return 2
    set_derived_patterns(identifiers)

    mode = "all" if args.all else "changed"
    extra_paths = list(args.paths)
    if extra_paths:
        mode = "paths"
    try:
        targets = gather_targets(root, mode, extra_paths)
        findings = screen_index(root)
        findings.extend(screen_targets(root, targets))
    except (RuntimeError, OSError) as error:
        print(f"PRIVACY SCREEN ERROR — {error}", file=sys.stderr)
        return 2
    return report(findings, len(identifiers), private_present)


if __name__ == "__main__":
    sys.exit(main())