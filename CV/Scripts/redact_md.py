#!/usr/bin/env python3
"""Prepare Markdown for a remote model and restore exact local identifiers.

The reviewed private JSON policy contains
{"reviewed": true, "redact_values": ["literal identifier", ...]}.
Never pass the policy, mapping or restored output to a remote model.

The `check` command fails closed when a document already contains a listed
identifier, a reserved privacy token or an unlisted contact pattern. It reports
only generic status, never the matched value, and is the review mechanism for
the curated knowledge base (see PRIVACY.md).
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import secrets

from output_paths import check_output
from cover_letter import load_identity


TOKEN = re.compile(r"APP_MAN_PRIVATE_[0-9a-f]{24}_\d+_TOKEN")
RESERVED = re.compile(r"APP_MAN_PRIVATE_[A-Za-z0-9_]+_TOKEN")
CONTACT = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+\d[\d ()-]{7,}\d|linkedin\.com/in/", re.I)


def policy_values(path):
    try:
        policy = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("Cannot read private redaction policy.") from None
    if (not isinstance(policy, dict) or set(policy) != {"redact_values", "reviewed"}
            or not isinstance(policy["redact_values"], list)
            or not policy["redact_values"]
            or any(not isinstance(v, str) or not v.strip() or RESERVED.search(v)
                   for v in policy["redact_values"])):
        raise ValueError("Policy requires reviewed and a nonempty redact_values list of literal strings.")
    if policy["reviewed"] is not True:
        raise ValueError("Policy is unreviewed; add all identifiers locally before exporting.")
    return sorted(set(policy["redact_values"]), key=lambda v: (-len(v), v))


def redact(text, values):
    if RESERVED.search(text):
        raise ValueError("Input contains reserved privacy tokens.")
    values = [value for value in values if value in text]
    if not values:
        raise ValueError("No policy identifiers found; review this document's policy before export.")
    nonce = secrets.token_hex(12)
    mapping = {f"APP_MAN_PRIVATE_{nonce}_{i}_TOKEN": value for i, value in enumerate(values)}
    reverse = {value: token for token, value in mapping.items()}
    pattern = re.compile("|".join(re.escape(v) for v in values))
    safe = pattern.sub(lambda match: reverse[match.group()], text)
    if any(value in safe for value in values) or CONTACT.search(safe):
        raise ValueError("Identifier or contact pattern remains; update the private policy.")
    return safe, mapping


def scan_reasons(text, values):
    reasons = []
    if RESERVED.search(text):
        reasons.append("reserved privacy token")
    if any(value in text for value in values):
        reasons.append("listed identifier")
    if CONTACT.search(text):
        reasons.append("contact pattern")
    return reasons


def scan_targets(paths):
    targets = []
    for raw in paths:
        path = Path(raw)
        if path.is_symlink():
            raise ValueError("Symlink scan target rejected.")
        if path.is_dir():
            targets.extend(child for child in sorted(path.rglob("*.md"))
                           if not child.is_symlink())
        elif path.is_file():
            targets.append(path)
        else:
            raise ValueError("Scan target is not a file or directory.")
    return targets


def display_path(path):
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def restore(original, response, mapping):
    if not isinstance(mapping, dict) or not mapping or any(
            not TOKEN.fullmatch(token) or not isinstance(value, str) or not value
            for token, value in mapping.items()):
        raise ValueError("Invalid private token mapping.")
    if (Counter(TOKEN.findall(original)) != Counter(TOKEN.findall(response))
            or set(RESERVED.findall(response)) != set(TOKEN.findall(original))
            or not set(TOKEN.findall(original)) <= set(mapping)):
        raise ValueError("Privacy tokens changed or missing; no output written.")
    if re.search(r"\[(?:EMAIL|PHONE|PERSON(?:_NAME)?|ADDRESS|REDACTED)\]", response, re.I):
        raise ValueError("Provider redaction placeholders found; no output written.")
    for token, value in mapping.items():
        response = response.replace(token, value)
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed-policy", help="Create a private policy from local identity without printing it")
    seed.add_argument("identity", type=Path)
    seed.add_argument("policy", type=Path)
    prepare = commands.add_parser("prepare", help="Write a redacted Markdown copy and private mapping")
    prepare.add_argument("source", type=Path)
    prepare.add_argument("policy", type=Path)
    prepare.add_argument("safe", type=Path)
    prepare.add_argument("mapping", type=Path)
    check = commands.add_parser("check", help="Fail if a document holds a listed identifier, token or contact pattern")
    check.add_argument("policy", type=Path)
    check.add_argument("paths", type=Path, nargs="+")
    finish = commands.add_parser("restore", help="Restore tokens in a model response locally")
    finish.add_argument("safe", type=Path)
    finish.add_argument("response", type=Path)
    finish.add_argument("mapping", type=Path)
    finish.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "seed-policy":
            check_output(args.policy, args.identity)
            if args.policy.resolve() == args.identity.resolve():
                raise ValueError("Policy must differ from identity input.")
            fields = load_identity(args.identity)
            values = sorted(set(v for lines in fields.values() for v in lines), key=lambda v: (-len(v), v))
            args.policy.parent.mkdir(parents=True, exist_ok=True)
            with args.policy.open("x", encoding="utf-8") as stream:
                json.dump({"reviewed": False, "redact_values": values}, stream,
                          ensure_ascii=False, indent=2)
            args.policy.chmod(0o600)
            print("Private identity policy seeded; add employer, recruiter, address variants and other identifiers locally before use.")
        elif args.command == "prepare":
            for target in (args.safe, args.mapping):
                check_output(target, args.source, args.policy)
            if len({p.resolve() for p in (args.source, args.policy, args.safe, args.mapping)}) != 4:
                raise ValueError("All inputs and outputs must be distinct.")
            safe, mapping = redact(args.source.read_text(encoding="utf-8"), policy_values(args.policy))
            args.mapping.parent.mkdir(parents=True, exist_ok=True)
            with args.mapping.open("x", encoding="utf-8") as stream:
                json.dump(mapping, stream)
            args.mapping.chmod(0o600)
            args.safe.parent.mkdir(parents=True, exist_ok=True)
            with args.safe.open("x", encoding="utf-8") as stream:
                stream.write(safe)
            print("Redacted Markdown prepared; mapping retained locally.")
        elif args.command == "check":
            values = policy_values(args.policy)
            failed = False
            for target in scan_targets(args.paths):
                reasons = scan_reasons(target.read_text(encoding="utf-8"), values)
                print(f"{'FAIL' if reasons else 'PASS'} {display_path(target)}"
                      + (f": {', '.join(reasons)}" if reasons else ""))
                failed = failed or bool(reasons)
            if failed:
                parser.exit(1, "Error: check failed; fix the listed files before remote use.\n")
        else:
            check_output(args.output, args.safe, args.response, args.mapping)
            if args.output.resolve() in {p.resolve() for p in (args.safe, args.response, args.mapping)}:
                raise ValueError("Output must differ from inputs.")
            try:
                mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise ValueError("Cannot read private token mapping.") from None
            result = restore(args.safe.read_text(encoding="utf-8"),
                             args.response.read_text(encoding="utf-8"), mapping)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(result)
            print("Identifiers restored locally.")
    except OSError:
        parser.exit(1, "Error: Cannot read or write a private document.\n")
    except ValueError as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
