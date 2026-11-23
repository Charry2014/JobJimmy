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

    def entries(self, *values):
        return sorted(((v, "ID") for v in values), key=lambda item: (-len(item[0]), item[0]))

    def test_round_trip_and_overlapping_values(self):
        source = "Ada Example, Example Labs, labs.example; [EMAIL]"
        values = ["Example Labs", "Example", "Ada Example", "[EMAIL]"]
        registry = {}
        safe, replaced = r.redact(source, self.entries(*values), registry)
        self.assertEqual(replaced, 3)
        for value in values:
            self.assertNotIn(value, safe)
        self.assertEqual(r.restore(safe, registry), source)

    def test_tokens_are_stable_across_documents(self):
        registry = {}
        first, _ = r.redact("Led Example Labs.", self.entries("Example Labs"), registry)
        second, _ = r.redact("At Example Labs and Other Co.", self.entries("Example Labs", "Other Co"), registry)
        token = first.split()[1].rstrip(".")
        self.assertIn(token, second)
        self.assertEqual(len(registry), 2)

    def test_labels_make_readable_tokens(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.json"
            path.write_text(json.dumps({"reviewed": True, "redact_values": [
                "Ada Example", {"value": "Example Labs", "label": "EMPLOYER"}]}))
            registry = {}
            safe, _ = r.redact("Ada Example at Example Labs", r.policy_entries(path), registry)
            self.assertRegex(safe, r"^@@ID_\d\d@@ at @@EMPLOYER_\d\d@@$")
            self.assertEqual(r.policy_values(path), ["Example Labs", "Ada Example"])

    def test_invalid_label_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.json"
            path.write_text(json.dumps({"reviewed": True, "redact_values": [{"value": "X Co", "label": "bad label"}]}))
            with self.assertRaisesRegex(ValueError, "labels"):
                r.policy_entries(path)

    def test_restore_accepts_dropped_repeated_and_combined_tokens(self):
        registry = {}
        advert, _ = r.redact("Example Labs seeks a lead.", self.entries("Example Labs"), registry)
        evidence, _ = r.redact("Ada Example led Other Co.", self.entries("Ada Example", "Other Co"), registry)
        labs, ada, other = (t for t in registry)
        draft = f"{ada} would join {labs}. At {other}, {ada} built teams. {labs} again."
        self.assertEqual(r.restore(draft, registry),
                         "Ada Example would join Example Labs. At Other Co, Ada Example built teams. Example Labs again.")
        self.assertEqual(r.restore("No tokens at all.", registry), "No tokens at all.")

    def test_unlisted_contact_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "contact pattern"):
            r.redact("Someone at +00 000 0000000", self.entries("Someone"), {})

    def test_listed_contact_is_reversible(self):
        source = "[EMAIL] at Example Labs"
        registry = {}
        safe, _ = r.redact(source, self.entries("[EMAIL]", "Example Labs"), registry)
        self.assertNotIn("[EMAIL]", safe)
        self.assertEqual(r.restore(safe, registry), source)

    def test_document_without_listed_values_is_allowed(self):
        safe, replaced = r.redact("Different text", self.entries("Example Labs"), {})
        self.assertEqual((safe, replaced), ("Different text", 0))

    def test_unknown_damaged_and_legacy_tokens_rejected(self):
        registry = {}
        safe, _ = r.redact("Example Labs", self.entries("Example Labs"), registry)
        with self.assertRaisesRegex(ValueError, "Unknown"):
            r.restore(safe + " @@ID_99@@", registry)
        with self.assertRaisesRegex(ValueError, "Damaged"):
            r.restore(safe[:-1], registry)
        with self.assertRaisesRegex(ValueError, "Damaged"):
            r.restore(safe.lower(), registry)
        with self.assertRaisesRegex(ValueError, "legacy"):
            r.restore("APP_MAN_PRIVATE_" + "0" * 24 + "_0_TOKEN", registry)

    def test_provider_placeholder_rejected(self):
        registry = {}
        safe, _ = r.redact("Example Labs", self.entries("Example Labs"), registry)
        with self.assertRaisesRegex(ValueError, "placeholders"):
            r.restore(safe + " [REDACTED]", registry)

    def test_input_with_reserved_token_rejected(self):
        with self.assertRaisesRegex(ValueError, "reserved"):
            r.redact("Text @@ID_01@@", self.entries("Text"), {})

    def test_legacy_restore_still_strict(self):
        token = "APP_MAN_PRIVATE_" + "0" * 24 + "_0_TOKEN"
        mapping = {token: "Example Labs"}
        self.assertEqual(r.restore_legacy(token, token, mapping), "Example Labs")
        with self.assertRaisesRegex(ValueError, "tokens changed"):
            r.restore_legacy(token, token + token, mapping)

    def test_cli_prepare_and_restore_use_private_registry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            policy = root / "policy.json"
            policy.write_text(json.dumps({"reviewed": True, "redact_values": ["Example Labs"]}))
            source, safe, registry = root / "a.md", root / "a-safe.md", root / "tokens.json"
            source.write_text("Joined Example Labs.")
            for argv in (["prepare", str(source), str(policy), str(safe), "--registry", str(registry)],
                         ["restore", str(safe), str(root / "out.md"), "--registry", str(registry)]):
                with patch.object(r, "check_output", lambda *a: None), \
                        patch("sys.argv", ["redact_md.py", *argv]), redirect_stdout(io.StringIO()), \
                        redirect_stderr(io.StringIO()):
                    r.main()
            self.assertNotIn("Example Labs", safe.read_text())
            self.assertEqual((root / "out.md").read_text(), "Joined Example Labs.")
            self.assertEqual(registry.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(registry.read_text())["version"], 1)
            note = root / "note.md"
            note.write_text(safe.read_text())
            with patch.object(r, "check_output", lambda *a: None), \
                    patch("sys.argv", ["redact_md.py", "restore", str(note), str(note), "--registry", str(registry)]), \
                    redirect_stdout(io.StringIO()):
                r.main()
            self.assertEqual(note.read_text(), "Joined Example Labs.")

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
        self.assertIn("reserved privacy token", r.scan_reasons("@@EMPLOYER_03@", []))
        self.assertEqual(r.scan_reasons("Led @@EMPLOYER_03@@.", []), [])

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
