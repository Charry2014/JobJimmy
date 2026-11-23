#!/usr/bin/env python3
"""Prepare Markdown for a remote model and restore exact local identifiers.

The reviewed private JSON policy contains
{"reviewed": true, "redact_values": [...]}, where each entry is a literal
string or {"value": "literal", "label": "EMPLOYER"}. Labels (capital letters
and underscores) only make tokens readable for the model, for example
@@EMPLOYER_03@@; unlabelled values become @@ID_07@@.

Tokens are stable: a private registry (default
JobSearch/Templates/redaction-tokens.json) assigns each value one token the
first time it is redacted and reuses it in every later document. A model can
therefore combine several safe sources (advert, knowledge base, baseline,
earlier drafts) in one response, drop or repeat tokens freely, and `restore`
needs only the registry. Restoration still refuses unknown or damaged tokens
and provider redaction placeholders, and writes nothing in that case.

Never pass the policy, registry or restored output to a remote model.

The `check` command is a local safety scanner: it reports a listed identifier,
a reserved privacy token or an unlisted contact pattern, prints only generic
status and never the matched value. A pass is not proof of anonymity and does
not authorise remote use; review content and the private policy first.

`restore-legacy` restores responses made with the older per-document
APP_MAN_PRIVATE mappings.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys

from output_paths import check_output
from cover_letter import load_identity


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "JobSearch" / "Templates" / "redaction-tokens.json"
TOKEN = re.compile(r"@@([A-Z][A-Z_]{0,19})_(\d{2,4})@@")
LEGACY_TOKEN = re.compile(r"APP_MAN_PRIVATE_[0-9a-f]{24}_\d+_TOKEN")
RESERVED = re.compile(r"APP_MAN_PRIVATE_[A-Za-z0-9_]+_TOKEN|@@[A-Za-z_]*\d*@@")
LABEL = re.compile(r"[A-Z][A-Z_]{0,19}")
CONTACT = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+\d[\d ()-]{7,}\d|linkedin\.com/in/", re.I)
PROVIDER = re.compile(r"\[(?:EMAIL|PHONE|PERSON(?:_NAME)?|ADDRESS|REDACTED)\]", re.I)


def policy_entries(path):
    """Return [(value, label)] from a reviewed policy, longest value first."""
    try:
        policy = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("Cannot read private redaction policy.") from None
    entries = policy.get("redact_values") if isinstance(policy, dict) else None
    if (not isinstance(policy, dict) or set(policy) != {"redact_values", "reviewed"}
            or not isinstance(entries, list) or not entries):
        raise ValueError("Policy requires reviewed and a nonempty redact_values list.")
    parsed = {}
    for entry in entries:
        if isinstance(entry, str):
            value, label = entry, "ID"
        elif isinstance(entry, dict) and set(entry) <= {"value", "label"} and "value" in entry:
            value, label = entry["value"], entry.get("label", "ID")
        else:
            raise ValueError("Each policy entry is a string or {value, label}.")
        if (not isinstance(value, str) or not value.strip() or RESERVED.search(value)
                or not isinstance(label, str) or not LABEL.fullmatch(label)):
            raise ValueError("Policy values must be nonempty literals; labels capital letters and underscores.")
        parsed.setdefault(value, label)
    if policy["reviewed"] is not True:
        raise ValueError("Policy is unreviewed; add all identifiers locally before exporting.")
    return sorted(parsed.items(), key=lambda item: (-len(item[0]), item[0]))


def policy_values(path):
    return [value for value, _ in policy_entries(path)]


def load_registry(path):
    """Return {token: value} from the private registry; empty when absent."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("Cannot read private token registry.") from None
    tokens = data.get("tokens") if isinstance(data, dict) else None
    if (not isinstance(tokens, dict) or data.get("version") != 1
            or any(not TOKEN.fullmatch(t) or not isinstance(v, str) or not v for t, v in tokens.items())
            or len(set(tokens.values())) != len(tokens)):
        raise ValueError("Invalid private token registry.")
    return dict(tokens)


def save_registry(path, registry):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump({"version": 1, "tokens": registry}, stream, ensure_ascii=False, indent=1)
    temporary.replace(path)
    path.chmod(0o600)


def token_for(value, label, registry):
    """Return the stable token for value, adding one to registry if new."""
    for token, known in registry.items():
        if known == value:
            return token
    number = 1 + max((int(TOKEN.fullmatch(t).group(2)) for t in registry), default=0)
    token = f"@@{label}_{number:02d}@@"
    registry[token] = value
    return token


def redact(text, entries, registry):
    """Return (safe text, number of identifiers replaced); updates registry in place."""
    if RESERVED.search(text):
        raise ValueError("Input contains reserved privacy tokens.")
    present = [(value, label) for value, label in entries if value in text]
    replaced = 0
    if present:
        tokens = {value: token_for(value, label, registry) for value, label in present}
        pattern = re.compile("|".join(re.escape(value) for value, _ in present))
        text, replaced = pattern.subn(lambda match: tokens[match.group()], text)
        if any(value in text for value, _ in present):
            raise ValueError("Identifier remains after redaction; update the private policy.")
    if CONTACT.search(text):
        raise ValueError("Unlisted contact pattern remains; add it to the private policy.")
    return text, replaced


def restore(response, registry):
    """Replace stable tokens; refuse unknown, damaged or legacy tokens and provider placeholders."""
    if LEGACY_TOKEN.search(response):
        raise ValueError("Response contains legacy tokens; use restore-legacy with its mapping.")
    if any(match.group() not in registry for match in TOKEN.finditer(response)):
        raise ValueError("Unknown privacy tokens in the response; no output written.")
    if "@@" in TOKEN.sub("", response):
        raise ValueError("Damaged privacy token in the response; no output written.")
    if PROVIDER.search(response):
        raise ValueError("Provider redaction placeholders found; no output written.")
    return TOKEN.sub(lambda match: registry[match.group()], response)


def restore_legacy(original, response, mapping):
    """Strict restore for the older per-document APP_MAN_PRIVATE mappings."""
    if not isinstance(mapping, dict) or not mapping or any(
            not LEGACY_TOKEN.fullmatch(token) or not isinstance(value, str) or not value
            for token, value in mapping.items()):
        raise ValueError("Invalid private token mapping.")
    if (Counter(LEGACY_TOKEN.findall(original)) != Counter(LEGACY_TOKEN.findall(response))
            or set(RESERVED.findall(response)) != set(LEGACY_TOKEN.findall(original))
            or not set(LEGACY_TOKEN.findall(original)) <= set(mapping)):
        raise ValueError("Privacy tokens changed or missing; no output written.")
    if PROVIDER.search(response):
        raise ValueError("Provider redaction placeholders found; no output written.")
    for token, value in mapping.items():
        response = response.replace(token, value)
    return response


def scan_reasons(text, values):
    """Stable tokens are expected in safe copies; legacy or damaged ones are not."""
    reasons = []
    if LEGACY_TOKEN.search(text) or "@@" in TOKEN.sub("", text):
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


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed-policy", help="Create a private policy from local identity without printing it")
    seed.add_argument("identity", type=Path)
    seed.add_argument("policy", type=Path)
    prepare = commands.add_parser("prepare", help="Write a redacted copy (overwrites the safe output)")
    prepare.add_argument("source", type=Path)
    prepare.add_argument("policy", type=Path)
    prepare.add_argument("safe", type=Path)
    prepare.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    check = commands.add_parser("check", help="Local scanner: report a listed identifier, token or contact pattern")
    check.add_argument("policy", type=Path)
    check.add_argument("paths", type=Path, nargs="+")
    finish = commands.add_parser("restore", help="Restore stable tokens locally; OUTPUT may equal RESPONSE (in place)")
    finish.add_argument("response", type=Path)
    finish.add_argument("output", type=Path)
    finish.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    legacy = commands.add_parser("restore-legacy", help="Restore an older APP_MAN_PRIVATE response with its mapping")
    legacy.add_argument("safe", type=Path)
    legacy.add_argument("response", type=Path)
    legacy.add_argument("mapping", type=Path)
    legacy.add_argument("output", type=Path)
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
            for target in (args.safe, args.registry):
                check_output(target, args.source, args.policy)
            if len({p.resolve() for p in (args.source, args.policy, args.safe, args.registry)}) != 4:
                raise ValueError("Source, policy, safe copy and registry must be distinct.")
            registry = load_registry(args.registry)
            before = len(registry)
            safe, replaced = redact(args.source.read_text(encoding="utf-8"), policy_entries(args.policy), registry)
            if len(registry) != before:
                save_registry(args.registry, registry)
            write_text(args.safe, safe)
            print(f"Redacted Markdown prepared: {replaced} identifier occurrence(s) replaced.")
            if not replaced:
                print("No listed identifiers found; review the safe copy for names the policy does not list.",
                      file=sys.stderr)
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
        elif args.command == "restore":
            check_output(args.output, args.response, args.registry)
            if args.output.resolve() == args.registry.resolve():
                raise ValueError("Output must differ from the registry.")
            result = restore(args.response.read_text(encoding="utf-8"), load_registry(args.registry))
            write_text(args.output, result)
            print("Identifiers restored locally.")
        else:
            check_output(args.output, args.safe, args.response, args.mapping)
            if args.output.resolve() in {p.resolve() for p in (args.safe, args.response, args.mapping)}:
                raise ValueError("Output must differ from inputs.")
            try:
                mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise ValueError("Cannot read private token mapping.") from None
            result = restore_legacy(args.safe.read_text(encoding="utf-8"),
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
