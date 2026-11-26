#!/usr/bin/env python3
"""Run several OpenRouter models on the same prose-drafting request.

The request is the one the Kilo `writer` subagent receives: its brief from
`.kilo/agents/writer.md` as the system message, and a task message naming the
document, language and output file. Because a comparison run has no file
tools, the files the writer would read are included inline. Each model gets
exactly the same messages, so the outputs differ only by model.

Input is a checked safe copy, never raw private text:

- a safe bundle folder from `jobflow.py bundle` (`JobSearch/Outputs/safe/<slug>`),
  read in the writer's order: the voice guides, advert, research and
  application notes, the other knowledge articles, the baseline (CV only) and
  the current draft for the document; or
- one Markdown or text file prepared the same way.

Settings come from a `.env` file (default: the repository's `.env`; a variable
already set in the shell wins):

    OPENROUTER_API_KEY=...
    PROSE_COMPARE_MODELS=anthropic/claude-opus-5.5, google/gemini-4-argon
    PROSE_COMPARE_EFFORT=high          # optional: low|medium|high|xhigh
    PROSE_COMPARE_MAX_TOKENS=40000     # optional

Every request asks OpenRouter for zero-data-retention endpoints with data
collection denied; a model without such a route fails with an HTTP error
instead of falling back. Before sending, the outgoing messages are scanned
with the reviewed redaction policy (listed identifiers, contact patterns,
damaged tokens); any finding stops the run with no request sent.

Outputs are written blind to a private folder (default
`JobSearch/Outputs/model-compare/<timestamp>/`): `A.md`, `B.md`, ... with a
shuffled label per model, `REVIEW.md` with the reading order and local checks,
`key.json` mapping labels to models with tokens, cost and time, and
`request.json` with the exact messages sent. The console prints status, token
and cost figures only, never draft text, so the run can be driven by an agent
without the drafts entering its context. Read the drafts before opening
`key.json`.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import random
import re
import ssl
import string
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import env_file  # noqa: E402
import redact_md as rm  # noqa: E402

try:
    import certifi
except ImportError:  # optional; the system trust store is used without it
    certifi = None

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / "JobSearch"
SAFE = PRIVATE / "Outputs" / "safe"
POLICY = PRIVATE / "Templates" / "redaction-policy.json"
DEFAULT_OUT = PRIVATE / "Outputs" / "model-compare"
WRITER = ROOT / ".kilo" / "agents" / "writer.md"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
EFFORTS = ("low", "medium", "high", "xhigh")
LETTER_HEADINGS = ("Sender", "Date", "Recipient", "Subject", "Salutation", "Body",
                   "Closing", "Signature")
PUBLIC_REFERENCES = {
    "letter": ["CV/Templates/Cover-Letter.md"],
    "cv": ["CV/Style-guide.md"],
}
FIRST = ["knowledge/Writing-guide.md", "knowledge/Reasoning-profile.md",
         "advert.md", "research.md", "application.md", "company.md"]
DRAFT_PATTERN = {"letter": "*cover-letter-prose*.md", "cv": "*cv-draft*.md"}
TAILORING_MARK = "=== TAILORING ==="
HARNESS_NOTE = f"""

## This run: model comparison outside Kilo

This request comes from a model-comparison harness, not a Kilo session. You
have no tools: the files you would read are included in the user message, each
under a `=== FILE: <path> ===` header, and nothing else is available. Do not
ask for missing inputs; work with what is included. Do not write files and do
not send the report described under "Report back". Reply with the complete
document only, with no preamble or commentary. For a CV, reply with the draft,
then a line `{TAILORING_MARK}`, then the tailoring change list.
"""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_models(value):
    """Comma- or whitespace-separated model ids, deduplicated in order."""
    models = []
    for item in re.split(r"[,\s]+", value or ""):
        item = item.strip().removeprefix("openrouter/")
        if item and item not in models:
            models.append(item)
    return models


def writer_brief(path=None):
    text = Path(path or WRITER).read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end < 0:
            raise ValueError("Writer brief has unterminated front matter.")
        text = text[end + 5:]
    return text.strip() + "\n" + HARNESS_NOTE


def check_location(path, private=None, safe=None):
    """Refuse raw private files: under JobSearch/ only safe copies may be sent."""
    private = PRIVATE if private is None else private
    safe = SAFE if safe is None else safe
    resolved = Path(path).resolve()
    if resolved.is_relative_to(private.resolve()) and not resolved.is_relative_to(safe.resolve()):
        raise ValueError("Input is a raw private file; prepare a safe copy with "
                         "jobflow.py bundle and pass that instead.")
    return resolved


def bundle_files(folder, task, baseline=None):
    """The writer's reading list for a safe bundle, in its reading order."""
    folder = Path(folder)
    chosen = [folder / name for name in FIRST if (folder / name).is_file()]
    for name in ("knowledge/Writing-guide.md", "knowledge/Reasoning-profile.md"):
        if not (folder / name).is_file():
            raise ValueError(f"Bundle lacks {name}; the writer must not draft without it.")
    chosen += [p for p in sorted((folder / "knowledge").glob("*.md")) if p not in chosen]
    if task == "cv":
        baselines = sorted((folder / "baseline").glob("*.md"))
        if baseline:
            baselines = [p for p in baselines if p.stem == baseline]
            if not baselines:
                raise ValueError(f"Bundle has no baseline/{baseline}.md.")
        if not baselines:
            raise ValueError("A CV run needs a baseline in the bundle (bundle --baseline NAME).")
        chosen += baselines
    chosen += sorted((folder / "drafts").glob(DRAFT_PATTERN[task]))
    return [(p.relative_to(folder).as_posix(), p.read_text(encoding="utf-8")) for p in chosen]


def input_files(path, task, baseline=None):
    path = Path(path)
    if path.is_dir():
        return bundle_files(path, task, baseline)
    if not path.is_file():
        raise ValueError("Input is not a file or folder.")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("Input file is empty.")
    return [(path.name, text)]


def output_name(task, files, language):
    for name, _ in files:
        if name.startswith("drafts/"):
            return name.removeprefix("drafts/")
    suffix = "-en" if language != "en" else ""
    return f"draft-cover-letter-prose{suffix}.md" if task == "letter" else f"draft-cv-draft{suffix}.md"


def build_messages(task, files, language="en", baseline=None, notes=None, brief=None,
                   references=None):
    """System: the writer brief. User: the calling agent's task plus the files."""
    brief = writer_brief() if brief is None else brief
    if references is None:
        references = [(name, (ROOT / name).read_text(encoding="utf-8"))
                      for name in PUBLIC_REFERENCES[task]]
    lines = [
        "Draft one document from the safe bundle included below.",
        "",
        "- Bundle: included inline (files under `=== FILE: ... ===` headers).",
        f"- Document: {task}",
        f"- Output file: out/{output_name(task, files, language)}",
        f"- Drafting language: {language}",
    ]
    if task == "cv":
        lines.append("- Pipeline: extracted")
        lines.append(f"- Baseline: {baseline or 'the one under baseline/'}")
    lines.append("- Revision notes: " + (notes.strip() if notes and notes.strip() else "none (new draft)"))
    body = "\n".join(lines) + "\n"
    for name, text in references + files:
        body += f"\n=== FILE: {name} ===\n{text.rstrip()}\n"
    return [{"role": "system", "content": brief}, {"role": "user", "content": body}]


def policy_values(path=None):
    path = POLICY if path is None else path
    return rm.policy_values(path) if Path(path).is_file() else []


def guard(texts, values, require_policy):
    """Stop before networking if anything identifying is in the input text.

    Scans the supplied inputs (bundle files, revision notes). The writer brief
    and the public templates are tracked files that carry synthetic
    placeholders such as an example.com address, so they are not scanned.
    """
    if require_policy and not values:
        raise ValueError("Private input needs the reviewed redaction policy "
                         "(JobSearch/Templates/redaction-policy.json); nothing sent.")
    for text in texts:
        reasons = rm.scan_reasons(text, values)
        if reasons:
            raise ValueError("Outgoing request failed the privacy scan (" + ", ".join(sorted(set(reasons)))
                             + "); fix the safe copy locally. Nothing sent.")


def ssl_context():
    return ssl.create_default_context(cafile=certifi.where()) if certifi else ssl.create_default_context()


def send(model, messages, key, max_tokens=40000, effort=None, timeout=600):
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "provider": {"zdr": True, "data_collection": "deny", "allow_fallbacks": True},
        "usage": {"include": True},
    }
    if effort:
        payload["reasoning"] = {"effort": effort}
    request = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json",
        "X-Title": "JobJimmy prose comparison",
    }, method="POST")
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl_context()))
    started = time.monotonic()
    try:
        with opener.open(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:2000]
        return {"ok": False, "error": f"HTTP {error.code}", "detail": detail,
                "seconds": round(time.monotonic() - started, 1)}
    except (OSError, ValueError) as error:
        return {"ok": False, "error": type(error).__name__, "detail": str(error)[:500],
                "seconds": round(time.monotonic() - started, 1)}
    seconds = round(time.monotonic() - started, 1)
    if "error" in data:
        return {"ok": False, "error": "API error", "detail": json.dumps(data["error"])[:2000],
                "seconds": seconds}
    choice = (data.get("choices") or [{}])[0]
    text = ((choice.get("message") or {}).get("content") or "")
    usage = data.get("usage") or {}
    return {
        "ok": bool(text.strip()),
        "error": None if text.strip() else "empty reply",
        "text": text,
        "finish": choice.get("finish_reason"),
        "served_model": data.get("model"),
        "provider": data.get("provider"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "cost": usage.get("cost"),
        "seconds": seconds,
    }


def local_checks(text, task, input_text):
    """Counts and flags only: invented tokens, provider placeholders, shape."""
    known = set(rm.TOKEN.findall(input_text))
    used = rm.TOKEN.findall(text)
    draft = text.split(TAILORING_MARK)[0]
    flags = []
    invented = sorted({f"@@{a}_{b}@@" for a, b in used if (a, b) not in known})
    if invented:
        flags.append(f"{len(invented)} invented token(s)")
    if rm.PROVIDER.search(text):
        flags.append("provider placeholder")
    if "@@" in rm.TOKEN.sub("", text):
        flags.append("damaged token")
    if task == "letter":
        found = re.findall(r"^##\s+(\w+)\s*$", draft, re.M)
        if tuple(found) != LETTER_HEADINGS:
            flags.append("letter headings differ from the eight fields")
        body = re.search(r"^##\s+Body\s*$(.*?)^##\s", draft, re.M | re.S)
        words = len(body.group(1).split()) if body else 0
    else:
        if TAILORING_MARK not in text:
            flags.append("no tailoring change list")
        words = len(draft.split())
    return {"words": words, "tokens_used": len(used), "flags": flags, "invented": invented}


def labels_for(models, seed=None):
    shuffled = list(models)
    random.Random(seed).shuffle(shuffled)
    names = list(string.ascii_uppercase) + [f"Z{i}" for i in range(1, 100)]
    return dict(zip(shuffled, names))


def default_out_dir(now=None):
    if not PRIVATE.is_dir():
        raise ValueError("No private vault attached; pass --out for the results folder.")
    return DEFAULT_OUT / (now or datetime.now()).strftime("%Y%m%d-%H%M%S")


def run(models, messages, task, key, out_dir, max_tokens=40000, effort=None, workers=4,
        sender=send, seed=None, echo=print):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(out_dir, 0o700)
    labels = labels_for(models, seed)
    input_text = "\n".join(m["content"] for m in messages if m["role"] == "user")
    request_record = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "task": task, "models": models, "effort": effort, "max_tokens": max_tokens,
        "provider": {"zdr": True, "data_collection": "deny"},
        "sha256": hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode()).hexdigest(),
        "messages": messages,
    }
    write_private(out_dir / "request.json", json.dumps(request_record, ensure_ascii=False, indent=2))
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(sender, model, messages, key, max_tokens, effort): model
                   for model in models}
        for future in concurrent.futures.as_completed(futures):
            model = futures[future]
            try:
                result = future.result()
            except Exception as error:  # a broken sender must not lose the other results
                result = {"ok": False, "error": type(error).__name__, "detail": str(error)[:500]}
            label = labels[model]
            entry = {k: v for k, v in result.items() if k != "text"}
            entry["label"] = label
            if result.get("ok"):
                write_private(out_dir / f"{label}.md", result["text"].rstrip() + "\n")
                entry["checks"] = local_checks(result["text"], task, input_text)
            results[model] = entry
            echo(status_line(model, entry))
    key_record = {entry["label"]: {"model": model, **{k: v for k, v in entry.items() if k != "label"}}
                  for model, entry in sorted(results.items(), key=lambda kv: kv[1]["label"])}
    write_private(out_dir / "key.json", json.dumps(key_record, ensure_ascii=False, indent=2))
    write_private(out_dir / "REVIEW.md", review_text(key_record, task, out_dir))
    total = sum(e.get("cost") or 0 for e in results.values())
    echo(f"Total cost: ${total:.4f}. Results (blind): {out_dir}")
    return key_record


def status_line(model, entry):
    if not entry.get("ok"):
        return f"FAIL {model}: {entry.get('error')} after {entry.get('seconds', '?')}s (detail in key.json)"
    checks = entry.get("checks") or {}
    flags = "; ".join(checks.get("flags") or []) or "checks ok"
    cost = entry.get("cost")
    cost_text = f"${cost:.4f}" if isinstance(cost, (int, float)) else "cost n/a"
    return (f"OK   {model}: {entry.get('prompt_tokens')} in / {entry.get('completion_tokens')} out, "
            f"{cost_text}, {entry.get('seconds')}s, {checks.get('words')} words; {flags}")


def review_text(key_record, task, out_dir):
    unit = "body words" if task == "letter" else "draft words"
    lines = [
        f"# Blind prose comparison ({task})",
        "",
        "Read each draft before opening `key.json`, which names the models.",
        "Note for each: does it sound like a person you would want to hire, is every",
        "claim traceable to the bundle, and would you send it with light edits?",
        "",
        f"| Draft | {unit} | Local checks | Your verdict |",
        "| --- | --- | --- | --- |",
    ]
    for label, entry in key_record.items():
        if entry.get("ok"):
            checks = entry.get("checks") or {}
            flags = "; ".join(checks.get("flags") or []) or "ok"
            lines.append(f"| [[{label}]] | {checks.get('words')} | {flags} | |")
        else:
            lines.append(f"| {label} | — | failed: {entry.get('error')} | |")
    lines += ["", "Restore a chosen draft locally before reading it with real names:",
              "`tools/py CV/Scripts/redact_md.py restore <draft.md> <restored.md>`.", ""]
    return "\n".join(lines)


def write_private(path, text):
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o600)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="See the module docstring for the .env settings.")
    parser.add_argument("input", help="safe bundle folder or a safe Markdown/text file")
    parser.add_argument("--task", choices=("letter", "cv"), default="letter")
    parser.add_argument("--env", help="path to the .env file (default: the repository's .env)")
    parser.add_argument("--models", help="override PROSE_COMPARE_MODELS (comma-separated)")
    parser.add_argument("--language", default="en", help="drafting language code (default en)")
    parser.add_argument("--baseline", help="CV baseline name in the bundle (e.g. Manager)")
    parser.add_argument("--notes", help="file with revision notes to pass, as the calling agent would")
    parser.add_argument("--effort", choices=EFFORTS, help="override PROSE_COMPARE_EFFORT")
    parser.add_argument("--max-tokens", type=int, help="override PROSE_COMPARE_MAX_TOKENS")
    parser.add_argument("--workers", type=int, default=4, help="parallel requests (default 4)")
    parser.add_argument("--out", help="results folder (default JobSearch/Outputs/model-compare/<time>)")
    parser.add_argument("--seed", type=int, help="fix the label shuffle (default random)")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and scan the request, write request.json, send nothing")
    args = parser.parse_args(argv)

    try:
        environ = dict(os.environ)
        if args.env and not Path(args.env).is_file():
            raise ValueError("The --env file does not exist.")
        env_file.load_env_file(args.env, environ)
        models = parse_models(args.models or environ.get("PROSE_COMPARE_MODELS"))
        if not models:
            raise ValueError("No models: set PROSE_COMPARE_MODELS in .env or pass --models.")
        effort = args.effort or environ.get("PROSE_COMPARE_EFFORT") or None
        if effort and effort not in EFFORTS:
            raise ValueError(f"PROSE_COMPARE_EFFORT must be one of {', '.join(EFFORTS)}.")
        max_tokens = args.max_tokens or int(environ.get("PROSE_COMPARE_MAX_TOKENS") or 40000)

        source = check_location(args.input)
        files = input_files(source, args.task, args.baseline)
        notes = Path(args.notes).read_text(encoding="utf-8") if args.notes else None
        if args.notes:
            check_location(args.notes)
        messages = build_messages(args.task, files, args.language, args.baseline, notes)
        private_input = source.is_relative_to(PRIVATE.resolve())
        guard([text for _, text in files] + ([notes] if notes else []), policy_values(),
              require_policy=private_input)

        chars = sum(len(m["content"]) for m in messages)
        print(f"Request: {len(files)} input file(s), about {chars // 4} tokens, "
              f"{len(models)} model(s), effort {effort or 'model default'}; privacy scan passed.")
        out_dir = Path(args.out) if args.out else default_out_dir()
        if args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=False)
            write_private(out_dir / "request.json",
                          json.dumps({"models": models, "messages": messages}, ensure_ascii=False, indent=2))
            print(f"Dry run: nothing sent. Request written to {out_dir / 'request.json'}")
            return 0
        key = environ.get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY is not set in the shell or the .env file.")
        key_record = run(models, messages, args.task, key, out_dir, max_tokens, effort,
                         args.workers, seed=args.seed)
    except ValueError as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        return 2
    return 0 if any(e.get("ok") for e in key_record.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
