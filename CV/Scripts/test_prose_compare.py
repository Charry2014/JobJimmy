"""Synthetic tests for the prose model comparison; no live API calls."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prose_compare as pc


LETTER = """## Sender

{{local sender}}

## Date

1 January 2030

## Recipient

Hiring team

## Subject

Example role

## Salutation

Dear hiring team,

## Body

I led @@EMPLOYER_01@@ engineering for five years.

## Closing

Kind regards,

## Signature

{{local signature}}
"""


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class ProseCompareTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bundle = self.root / "safe" / "example-slug"
        for name, text in {
            "advert.md": "Lead a team. Python required.",
            "research.md": "Research notes.",
            "application.md": "Application note.",
            "knowledge/Writing-guide.md": "Warm, direct voice.",
            "knowledge/Reasoning-profile.md": "Tests the premise.",
            "knowledge/Overview.md": "Overview of @@EMPLOYER_01@@ work.",
            "baseline/Manager.md": "## PROFILE\n\nEngineering leader.",
            "drafts/example-slug-cover-letter-prose.md": LETTER,
            "drafts/example-slug-cv-draft.md": "## PROFILE\n\nEngineering leader.",
        }.items():
            write(self.bundle, name, text)

    def test_parse_models_splits_dedupes_and_strips_prefix(self):
        self.assertEqual(pc.parse_models("a/x, b/y\nopenrouter/a/x  c/z"), ["a/x", "b/y", "c/z"])
        self.assertEqual(pc.parse_models(""), [])

    def test_bundle_order_follows_the_writer_reading_list(self):
        names = [n for n, _ in pc.bundle_files(self.bundle, "letter")]
        self.assertEqual(names[:2], ["knowledge/Writing-guide.md", "knowledge/Reasoning-profile.md"])
        self.assertIn("knowledge/Overview.md", names)
        self.assertNotIn("baseline/Manager.md", names)
        self.assertEqual(names[-1], "drafts/example-slug-cover-letter-prose.md")
        cv = [n for n, _ in pc.bundle_files(self.bundle, "cv", "Manager")]
        self.assertIn("baseline/Manager.md", cv)
        self.assertEqual(cv[-1], "drafts/example-slug-cv-draft.md")

    def test_bundle_without_voice_guides_is_refused(self):
        (self.bundle / "knowledge" / "Writing-guide.md").unlink()
        with self.assertRaisesRegex(ValueError, "Writing-guide"):
            pc.bundle_files(self.bundle, "letter")

    def test_cv_needs_a_baseline(self):
        with self.assertRaisesRegex(ValueError, "no baseline/Other"):
            pc.bundle_files(self.bundle, "cv", "Other")

    def test_raw_private_files_are_refused(self):
        private = self.root / "JobSearch"
        safe = private / "Outputs" / "safe"
        raw = write(private, "Knowledge/Overview.md", "x")
        ok = write(safe, "slug/advert.md", "x")
        with self.assertRaisesRegex(ValueError, "raw private file"):
            pc.check_location(raw, private, safe)
        self.assertEqual(pc.check_location(ok, private, safe), ok.resolve())
        self.assertEqual(pc.check_location(self.bundle, private, safe), self.bundle.resolve())

    def test_messages_carry_brief_task_and_inline_files(self):
        files = pc.bundle_files(self.bundle, "letter")
        messages = pc.build_messages("letter", files, brief="BRIEF",
                                     references=[("CV/Templates/Cover-Letter.md", "TEMPLATE")])
        self.assertEqual(messages[0], {"role": "system", "content": "BRIEF"})
        user = messages[1]["content"]
        self.assertIn("- Document: letter", user)
        self.assertIn("- Output file: out/example-slug-cover-letter-prose.md", user)
        self.assertIn("=== FILE: CV/Templates/Cover-Letter.md ===\nTEMPLATE", user)
        self.assertIn("=== FILE: advert.md ===\nLead a team.", user)

    def test_real_writer_brief_loses_front_matter_and_gains_harness_note(self):
        brief = pc.writer_brief()
        self.assertNotIn("mode: subagent", brief)
        self.assertIn("You are the JobJimmy writer", brief)
        self.assertIn(pc.TAILORING_MARK, brief)

    def test_guard_blocks_identifiers_and_contacts_before_sending(self):
        clean = ["Led @@EMPLOYER_01@@ teams."]
        pc.guard(clean, ["Synthetic Candidate"], require_policy=True)
        with self.assertRaisesRegex(ValueError, "listed identifier"):
            pc.guard(["Synthetic Candidate led."],
                     ["Synthetic Candidate"], require_policy=True)
        with self.assertRaisesRegex(ValueError, "contact pattern"):
            pc.guard(["Mail someone@example.org"],  # privacy-screen: allow
                     [], require_policy=False)
        with self.assertRaisesRegex(ValueError, "redaction policy"):
            pc.guard(clean, [], require_policy=True)

    def test_local_checks_flag_invented_tokens_and_letter_shape(self):
        ok = pc.local_checks(LETTER, "letter", "source has @@EMPLOYER_01@@")
        self.assertEqual(ok["flags"], [])
        self.assertEqual(ok["words"], 7)
        bad = pc.local_checks(LETTER.replace("## Closing", "## Close") + " @@PERSON_02@@ [EMAIL]",
                              "letter", "source has @@EMPLOYER_01@@")
        self.assertIn("1 invented token(s)", bad["flags"])
        self.assertIn("provider placeholder", bad["flags"])
        self.assertIn("letter headings differ from the eight fields", bad["flags"])
        cv = pc.local_checks("## PROFILE\n\nLed teams.", "cv", "")
        self.assertIn("no tailoring change list", cv["flags"])

    def test_run_writes_blind_results_and_prints_no_draft_text(self):
        def fake_send(model, messages, key, max_tokens, effort):
            self.assertEqual(key, "test-key")
            if model == "broken/model":
                return {"ok": False, "error": "HTTP 404", "detail": "no ZDR endpoint", "seconds": 0.1}
            return {"ok": True, "text": LETTER.replace("five", model), "prompt_tokens": 100,
                    "completion_tokens": 50, "cost": 0.01, "seconds": 1.0}
        out = self.root / "results"
        printed = io.StringIO()
        messages = [{"role": "system", "content": "BRIEF"},
                    {"role": "user", "content": "uses @@EMPLOYER_01@@"}]
        record = pc.run(["a/one", "b/two", "broken/model"], messages, "letter", "test-key", out,
                        sender=fake_send, seed=1, echo=lambda line: print(line, file=printed))
        self.assertEqual(sorted(record), ["A", "B", "C"])
        drafts = sorted(p.name for p in out.glob("?.md"))
        self.assertEqual(len(drafts), 2)
        key = json.loads((out / "key.json").read_text())
        self.assertEqual({v["model"] for v in key.values()}, {"a/one", "b/two", "broken/model"})
        self.assertIn("no ZDR endpoint", json.dumps(key))
        review = (out / "REVIEW.md").read_text()
        self.assertNotIn("a/one", review)
        self.assertNotIn("Dear hiring team", printed.getvalue())
        self.assertIn("FAIL broken/model: HTTP 404", printed.getvalue())
        self.assertEqual(oct(os.stat(out / "key.json").st_mode & 0o777), "0o600")

    def test_dry_run_sends_nothing(self):
        env = write(self.root, "test.env", "OPENROUTER_API_KEY=unused\nPROSE_COMPARE_MODELS=a/one,b/two\n")
        out = self.root / "dry"
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(pc, "send", side_effect=AssertionError("network used")), \
                patch.dict(os.environ, {}, clear=True), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = pc.main([str(self.bundle), "--env", str(env), "--out", str(out), "--dry-run"])
        self.assertEqual(code, 0, stderr.getvalue())
        request = json.loads((out / "request.json").read_text())
        self.assertEqual(request["models"], ["a/one", "b/two"])
        self.assertIn("2 model(s)", stdout.getvalue())

    def test_missing_models_stops(self):
        env = write(self.root, "empty.env", "OPENROUTER_API_KEY=unused\n")
        stderr = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(stderr):
            code = pc.main([str(self.bundle), "--env", str(env), "--out", str(self.root / "x")])
        self.assertEqual(code, 2)
        self.assertIn("PROSE_COMPARE_MODELS", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
