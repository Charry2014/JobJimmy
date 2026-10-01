#!/usr/bin/env python3
"""Advisory Jev checks on reviewed anonymous Markdown; offline preview by default."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from output_paths import check_output
from redact_md import CONTACT, policy_values

DEFAULT_REQUESTS = Path(__file__).resolve().parents[1] / "Jev" / "requests.json"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
# Reject these in the outbound text; never rewrite executable paths or numeric IDs.
LOCATORS = re.compile(r"https?://|www\.|\[\[|(?:/Users/|/home/|JobSearch/)|[A-Za-z]:[\\/]", re.I)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("Cannot read JSON input.") from None


def read_markdown(path):
    if path.suffix.lower() != ".md":
        raise ValueError("Text inputs must be Markdown files.")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("Markdown input is empty.")
    return text


def check_payload(payload, values):
    # Walk decoded strings so JSON escaping cannot conceal a listed identifier.
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for key, item in value.items():
                yield str(key)
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)
    for text in strings(payload):
        if (any(v.casefold() in text.casefold() for v in values)
                or CONTACT.search(text) or LOCATORS.search(text)):
            raise ValueError("Outbound input contains an identifier, contact or locator; sanitise locally.")


def validate_templates(config):
    if not isinstance(config, dict) or set(config) != {"version", "model", "fit", "document", "point"}:
        raise ValueError("Request configuration has invalid fields.")
    if not all(isinstance(config[k], str) and config[k].strip() for k in ("version", "model")):
        raise ValueError("Request version and model must be nonempty strings.")
    for name in ("fit", "document", "point"):
        q = config[name]
        if not isinstance(q, dict) or set(q) != {"type", "instructions", "criteria"}:
            raise ValueError("Question template has invalid fields.")
        if not isinstance(q["instructions"], str) or not q["instructions"].strip():
            raise ValueError("Question instructions must be nonempty text.")
        if name == "point":
            if (q["type"] != "choice" or not isinstance(q["criteria"], dict)
                    or set(q["criteria"]) != {"covered", "partial", "missing", "unclear"}
                    or "INDEX" not in q["instructions"]):
                raise ValueError("Point template requires the four coverage choices and INDEX placeholder.")
            descriptions = q["criteria"].values()
        else:
            if q["type"] != "score" or not isinstance(q["criteria"], list) or not 2 <= len(q["criteria"]) <= 10:
                raise ValueError("Score templates require two to ten ordered levels.")
            descriptions = q["criteria"]
        if any(not isinstance(v, str) or not v.strip() for v in descriptions):
            raise ValueError("Criteria must have nonempty text descriptions.")


def build_payload(config, kind, job, content, requirements=None):
    validate_templates(config)
    config = copy.deepcopy(config)
    if kind not in {"fit", "cv", "cover-letter"}:
        raise ValueError("Unknown check kind.")
    state = {"job_description": job}
    if kind == "fit":
        state["fit_analysis"] = content
        questions = {"match": config["fit"]}
    else:
        if (not isinstance(requirements, list) or not requirements
                or any(not isinstance(v, str) or not v.strip() for v in requirements)
                or len(set(requirements)) != len(requirements)):
            raise ValueError("Required points must be a nonempty JSON array of unique strings.")
        state.update(document_kind=kind, document_markdown=content, requirements=requirements)
        questions = {"match": config["document"]}
        for index in range(len(requirements)):
            questions[f"point_{index + 1}"] = {
                **config["point"],
                "instructions": config["point"]["instructions"].replace("INDEX", str(index)),
            }
    return {"model": config["model"], "state": state, "questions": questions}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def send(payload):
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise ValueError("Jev unavailable: TYPESAFE_API_KEY is not set; no request sent.")
    request = urllib.request.Request(ENDPOINT, data=encoded(payload), headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json",
    }, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError(f"Jev unavailable: HTTP {error.code}; response body withheld.") from None
    except (OSError, ValueError):
        raise ValueError("Jev unavailable: connection or response failure; details withheld.") from None


def number(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def validate_response(response, payload):
    if not isinstance(response, dict) or not isinstance(response.get("model"), str):
        raise ValueError("Invalid Jev response metadata.")
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(payload["questions"]):
        raise ValueError("Jev response is missing or has unexpected answers.")
    clean = {}
    for key, question in payload["questions"].items():
        answer = answers[key]
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            raise ValueError("Jev answer type mismatch.")
        levels = question["criteria"]
        expected = {str(i) for i in range(len(levels))} if question["type"] == "score" else set(levels)
        probabilities = answer.get("probabilities")
        if (not number(answer.get("confidence"), 0, 1)
                or not isinstance(probabilities, dict) or set(probabilities) != expected
                or any(not number(v, 0, 1) for v in probabilities.values())
                or not math.isclose(sum(probabilities.values()), 1, abs_tol=0.001)):
            raise ValueError("Invalid Jev confidence or probability distribution.")
        item = {"type": question["type"], "confidence": answer["confidence"], "probabilities": probabilities}
        if question["type"] == "score":
            maximum = len(levels) - 1
            score = answer.get("score")
            if (not number(score, 0, maximum)
                    or not math.isclose(score, sum(int(k) * v for k, v in probabilities.items()), abs_tol=0.01)):
                raise ValueError("Invalid Jev score.")
            item.update(score=score, match_score=100 * score / maximum,
                        legend={str(i): v for i, v in enumerate(levels)})
        else:
            choice = answer.get("choice")
            if not isinstance(choice, str) or choice not in expected or probabilities[choice] < max(probabilities.values()):
                raise ValueError("Invalid Jev coverage choice.")
            item["choice"] = choice
        clean[key] = item
    return clean


def report_markdown(report):
    match = report["answers"]["match"]
    lines = [f"# Jev {report['kind']} check", "",
             f"Match score: **{match['match_score']:.1f}/100**; confidence: **{match['confidence']:.1%}**.",
             "", "Advisory result. Confidence describes the answer distribution, not hiring probability or factual verification.",
             "", f"Request SHA-256: `{report['request_sha256']}`", "",
             f"Request version: `{report['request_version']}`; model: `{report['model']}`; evaluated: {report['evaluated_at']}."]
    if report["kind"] != "fit":
        lines += ["", "| Required point | Coverage | Confidence |", "| --- | --- | --- |"]
        for i, point in enumerate(report["request"]["state"]["requirements"]):
            answer = report["answers"][f"point_{i + 1}"]
            label = point.replace("|", "\\|").replace("\n", " ").replace("\r", " ")
            lines.append(f"| {label} | {answer['choice']} | {answer['confidence']:.1%} |")
    return "\n".join(lines) + "\n"


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as stream:
        stream.write(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["fit", "cv", "cover-letter"])
    parser.add_argument("--job", type=Path, required=True, help="Anonymous job-description Markdown")
    parser.add_argument("--analysis", type=Path, help="Anonymous completed fit/gap analysis Markdown")
    parser.add_argument("--document", type=Path, help="One final anonymous Markdown document")
    parser.add_argument("--requirements", type=Path, help="Anonymous required points as a JSON array")
    parser.add_argument("--policy", type=Path, required=True, help="Local reviewed redaction policy; never transmitted")
    parser.add_argument("--requests", type=Path, default=DEFAULT_REQUESTS, help="Editable question/rubric configuration")
    parser.add_argument("--reviewed", action="store_true", help="Inputs were locally checked for remaining identifiers")
    parser.add_argument("--send", action="store_true", help="Send to Jev; otherwise save an offline request preview")
    parser.add_argument("--output", type=Path, required=True, help="New private JSON file; --send also writes sibling Markdown")
    args = parser.parse_args(argv)
    try:
        if not args.reviewed:
            raise ValueError("Locally review anonymous inputs, then supply --reviewed.")
        if args.kind == "fit":
            if not args.analysis or args.document or args.requirements:
                raise ValueError("Fit requires --analysis and excludes --document/--requirements.")
            source = args.analysis
        else:
            if not args.document or not args.requirements or args.analysis:
                raise ValueError("Document checks require --document and --requirements, without --analysis.")
            source = args.document
        inputs = [args.job, source, args.policy, args.requests]
        if args.requirements:
            inputs.append(args.requirements)
        if args.output.suffix != ".json":
            raise ValueError("Output must be a new .json file.")
        outputs = [args.output] + ([args.output.with_suffix(".md")] if args.send else [])
        for target in outputs:
            check_output(target, *inputs)
            if target.exists() or target.resolve() in {p.resolve() for p in inputs}:
                raise ValueError("Output exists or collides with an input; choose a new version.")
        config = read_json(args.requests)
        payload = build_payload(config, args.kind, read_markdown(args.job), read_markdown(source),
                                read_json(args.requirements) if args.requirements else None)
        values = policy_values(args.policy)
        check_payload(payload, values)
        if not args.send:
            write_new(args.output, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            print("Offline Jev request prepared. Nothing sent; no score generated.")
            return 0
        response = send(payload)
        answers = validate_response(response, payload)
        report = {"kind": args.kind, "evaluated_at": datetime.now(timezone.utc).isoformat(),
                  "request_version": config["version"], "request_sha256": digest(payload),
                  "model": response["model"], "request": payload, "answers": answers}
        check_payload(report, values)
        write_new(args.output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        write_new(args.output.with_suffix(".md"), report_markdown(report))
        match = answers["match"]
        print(f"Jev {args.kind}: match {match['match_score']:.1f}/100; confidence {match['confidence']:.1%}.")
        for key, answer in answers.items():
            if key != "match":
                print(f"{key}: {answer['choice']}; confidence {answer['confidence']:.1%}.")
        return 0
    except (OSError, UnicodeError):
        parser.exit(1, "Error: Cannot read or write a check artifact; private details withheld.\n")
    except ValueError as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
