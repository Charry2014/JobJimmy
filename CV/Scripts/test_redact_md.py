"""Synthetic tests for local reversible Markdown redaction."""
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import redact_md as r


class RedactionTests(unittest.TestCase):
    def test_seeded_policy_cannot_export_until_reviewed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.json"
            path.write_text(json.dumps({"reviewed": False, "redact_values": ["Example Labs"]}))
            with self.assertRaisesRegex(ValueError, "unreviewed"):
                r.policy_values(path)
            path.write_text(json.dumps({"reviewed": True, "redact_values": ["Example Labs"]}))
            self.assertEqual(r.policy_values(path), ["Example Labs"])

    def test_round_trip_and_overlapping_values(self):
        source = "Ada Example, Example Labs, labs.example; [EMAIL]"
        values = ["Example Labs", "Example", "Ada Example", "[EMAIL]"]
        safe, mapping = r.redact(source, sorted(values, key=lambda v: (-len(v), v)))
        for value in values:
            self.assertNotIn(value, safe)
        self.assertEqual(r.restore(safe, safe, mapping), source)

    def test_unlisted_contact_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "contact pattern"):
            r.redact("Someone at +00 000 0000000", ["Someone"])

    def test_listed_contact_is_reversible(self):
        source = "[EMAIL] at Example Labs"
        safe, mapping = r.redact(source, ["[EMAIL]", "Example Labs"])
        self.assertNotIn("[EMAIL]", safe)
        self.assertEqual(r.restore(safe, safe, mapping), source)

    def test_missing_policy_value_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "No policy identifiers"):
            r.redact("Different text", ["Example Labs"])

    def test_shared_policy_ignores_identifiers_absent_from_document(self):
        safe, mapping = r.redact("Example Labs", ["Example Labs", "Not present"])
        self.assertEqual(len(mapping), 1)
        self.assertEqual(r.restore(safe, safe, mapping), "Example Labs")

    def test_modified_or_added_tokens_rejected(self):
        safe, mapping = r.redact("Example Labs", ["Example Labs"])
        with self.assertRaisesRegex(ValueError, "tokens changed"):
            r.restore(safe, "translated without token", mapping)
        with self.assertRaisesRegex(ValueError, "tokens changed"):
            r.restore(safe, safe + " " + safe, mapping)
        with self.assertRaisesRegex(ValueError, "tokens changed"):
            r.restore(safe, safe.replace("_TOKEN", "_token"), mapping)

    def test_provider_placeholder_rejected(self):
        safe, mapping = r.redact("Example Labs", ["Example Labs"])
        with self.assertRaisesRegex(ValueError, "placeholders"):
            r.restore(safe, safe + " [REDACTED]", mapping)

    def test_scan_clean_text_has_no_reasons(self):
        self.assertEqual(
            r.scan_reasons("A synthetic profile with no identifiers.", ["Example Labs"]), [])

    def test_scan_flags_listed_identifier(self):
        self.assertEqual(
            r.scan_reasons("Worked at Example Labs.", ["Example Labs"]), ["listed identifier"])

    def test_scan_flags_contact_and_reserved_token(self):
        self.assertIn("contact pattern", r.scan_reasons("Call +00 000 0000000", []))
        token = "APP_MAN_PRIVATE_" + "0" * 24 + "_0_TOKEN"
        self.assertIn("reserved privacy token", r.scan_reasons(token, []))

    def test_scan_targets_expands_directory_markdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.md").write_text("x")
            (root / "b.txt").write_text("x")
            (root / "sub").mkdir()
            (root / "sub" / "c.md").write_text("x")
            names = sorted(path.name for path in r.scan_targets([root]))
            self.assertEqual(names, ["a.md", "c.md"])

    def test_check_cli_reports_generic_status_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            policy = root / "policy.json"
            policy.write_text(json.dumps(
                {"reviewed": True, "redact_values": ["Example Labs", "[EMAIL]"]}))
            clean = root / "clean.md"
            clean.write_text("A synthetic profile with no identifiers.")
            dirty = root / "dirty.md"
            dirty.write_text("Worked at Example Labs.")
            show_name = lambda path: path.name  # noqa: E731 - deterministic display for the test
            output = io.StringIO()
            with patch.object(r, "display_path", show_name), \
                    patch("sys.argv", ["redact_md.py", "check", str(policy), str(clean)]), \
                    redirect_stdout(output):
                r.main()
            self.assertIn("PASS clean.md", output.getvalue())
            self.assertNotIn("Example Labs", output.getvalue())
            with patch.object(r, "display_path", show_name), \
                    patch("sys.argv", ["redact_md.py", "check", str(policy), str(dirty)]), \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as raised:
                r.main()
            self.assertEqual(raised.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
