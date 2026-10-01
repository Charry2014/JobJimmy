"""Regression tests for structured German CV translation."""
import io
import urllib.error
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import translate


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.policy = {"models": ["openai/gpt"], "providers": ["approved-provider"],
                       "keep_blocks": [], "redact_values": []}
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / "cv.md"
        self.source.write_text(
            "---\ntype: cv-reference\nvariant: example\n---\n\n"
            "<!-- cv:p000 -->\n# JANE DOE\n<!-- /cv:p000 -->\n\n"
            "<!-- cv:p001 -->\nProfile<br>Leadership\tCity\n<!-- /cv:p001 -->\n\n"
            "<!-- cv:p002 -->\n- Built teams\n- Improved delivery\n<!-- /cv:p002 -->\n",
            encoding="utf-8",
        )

    @patch("translate.urllib.request.urlopen")
    def test_translates_into_default_de_output_without_changing_structure(self, urlopen):
        urlopen.return_value = FakeResponse({
            "choices": [{"message": {"content": json.dumps({"translations": [
                {"id": "p001", "text": "Profil<br>Führung\tCity"},
                {"id": "p002", "text": ["Teams aufgebaut", "Lieferfähigkeit verbessert"]},
            ]})}}]
        })
        output = translate.translate(self.source, Path(self.tmp.name) / "cv-DE.md", "secret", "openai/gpt", policy=self.policy)
        actual = output.read_text(encoding="utf-8")
        self.assertIn("variant: example", actual)
        self.assertIn("<!-- cv:p001 -->\nProfil<br>Führung\tCity\n<!-- /cv:p001 -->", actual)
        self.assertIn("<!-- cv:p002 -->\n- Teams aufgebaut\n- Lieferfähigkeit verbessert\n<!-- /cv:p002 -->", actual)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer secret")
        request_body = json.loads(request.data)
        self.assertNotIn("JANE DOE", request.data.decode())
        self.assertEqual(request_body["provider"], {
            "zdr": True, "data_collection": "deny", "only": ["approved-provider"],
            "order": ["approved-provider"], "allow_fallbacks": False})
        self.assertEqual(request_body["model"], "openai/gpt")
        self.assertEqual(request_body["reasoning"], {"effort": "high"})

    def test_guidance_is_included_in_translation_prompt(self):
        guidance = {
            "glossary": {"embedded software": "Embedded-Software"},
            "style_instructions": ["Use concise German."],
        }
        prompt = translate.prompt_for([{"id": "p001", "prefix": "", "value": "Embedded software"}], guidance)
        self.assertIn("Embedded-Software", prompt)
        self.assertIn("Use concise German.", prompt)

    def test_guidance_rejects_unknown_keys(self):
        path = Path(self.tmp.name) / "guidance.json"
        path.write_text(json.dumps({"unknown": []}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            translate.load_guidance(path)

    def test_rejects_changed_formatting_markers(self):
        blocks = [
            {"id": "p001", "prefix": "", "value": "Profile<br>Leadership\tCity"},
        ]
        with self.assertRaisesRegex(ValueError, "formatting markers"):
            translate.validate_translations(blocks, [{"id": "p001", "text": "Profil Leadership City"}])

    def test_rejects_changed_block_order(self):
        blocks = [
            {"id": "p001", "prefix": "", "value": "Profile"},
            {"id": "p002", "prefix": "", "value": "Experience"},
        ]
        with self.assertRaisesRegex(ValueError, "IDs"):
            translate.validate_translations(blocks, [
                {"id": "p002", "text": "Erfahrung"},
                {"id": "p001", "text": "Profil"},
            ])

    @patch("translate.urllib.request.urlopen")
    def test_empty_block_survives_translation(self, urlopen):
        # align_md.py emits emptied bullet/prose blocks; they must not crash the
        # parser and must stay empty even if the model returns text for them.
        source = Path(self.tmp.name) / "folded.md"
        source.write_text(
            "---\ntype: cv-reference\nvariant: example\n---\n\n"
            "<!-- cv:p000 -->\n# JANE DOE\n<!-- /cv:p000 -->\n\n"
            "<!-- cv:p001 -->\n\n<!-- /cv:p001 -->\n"
            "<!-- cv:p002 -->\n- Built teams\n<!-- /cv:p002 -->\n",
            encoding="utf-8",
        )
        urlopen.return_value = FakeResponse({
            "choices": [{"message": {"content": json.dumps({"translations": [
                {"id": "p002", "text": ["Teams aufgebaut"]},
            ]})}}]
        })
        output = translate.translate(source, Path(self.tmp.name) / "folded-de.md", "secret", "openai/gpt", policy=self.policy)
        actual = output.read_text(encoding="utf-8")
        self.assertIn("<!-- cv:p001 -->\n\n<!-- /cv:p001 -->", actual)
        self.assertNotIn("unexpected model text", actual)

    def test_empty_source_emits_empty_result(self):
        checked = translate.validate_translations(
            [{"id": "p001", "prefix": "", "value": ""},
             {"id": "p002", "prefix": "", "value": []}],
            [{"id": "p001", "text": "hallucinated"},
             {"id": "p002", "text": ["hallucinated"]}],
        )
        self.assertEqual(checked, ["", []])

    @patch("translate.urllib.request.urlopen")
    def test_duplicate_blocks_fail_before_network(self, urlopen):
        self.source.write_text(self.source.read_text().replace('p002', 'p001'))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            translate.translate(self.source, Path(self.tmp.name) / 'out.md', 'secret', 'openai/gpt', policy=self.policy)
        urlopen.assert_not_called()

    def test_default_output_uses_lowercase_language_suffix(self):
        self.assertEqual(translate.default_output(Path("cv-blocks.md")).name, "cv-blocks-de.md")


    @patch("translate.urllib.request.urlopen")
    def test_missing_policy_blocks_before_network(self, urlopen):
        with self.assertRaisesRegex(ValueError, "privacy-policy"):
            translate.translate(self.source, Path(self.tmp.name) / "out.md", "secret", "openai/gpt")
        urlopen.assert_not_called()

    @patch("translate.urllib.request.urlopen")
    def test_unapproved_model_blocks_before_network(self, urlopen):
        with self.assertRaisesRegex(ValueError, "not approved"):
            translate.translate(self.source, Path(self.tmp.name) / "out.md", "secret", "other/model", policy=self.policy)
        urlopen.assert_not_called()

    def test_contacts_and_selected_address_stay_local(self):
        blocks = [{"id": "p001", "prefix": "", "value": "user@example.com"},
                  {"id": "p002", "prefix": "", "value": "Example Street"},
                  {"id": "p003", "prefix": "", "value": "Built systems"}]
        policy = {**self.policy, "keep_blocks": ["p002"]}
        outbound, _, kept, _ = translate.prepare_payload(blocks, {}, policy)
        self.assertEqual([b["id"] for b in outbound], ["p003"])
        self.assertEqual(kept["p002"], "Example Street")

    def test_redactions_restore_and_cannot_be_lost_or_duplicated(self):
        blocks = [{"id": "p001", "prefix": "", "value": "Led Synthetic Organisation"}]
        policy = {**self.policy, "redact_values": ["Synthetic Organisation"]}
        outbound, _, _, mapping = translate.prepare_payload(blocks, {}, policy)
        token = next(iter(mapping))
        self.assertNotIn("Synthetic Organisation", outbound[0]["value"])
        self.assertEqual(translate.restore_payload(outbound, ["Leitete " + token], mapping),
                         ["Leitete Synthetic Organisation"])
        for result in ("Leitete", token + token, "APP_MAN_PRIVATE_99_TOKEN"):
            with self.assertRaisesRegex(ValueError, "privacy tokens"):
                translate.restore_payload(outbound, [result], mapping)

    @patch("translate.urllib.request.urlopen")
    def test_http_error_does_not_echo_payload(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError("https://example.com", 403, "denied", {}, io.BytesIO(b"sensitive echo"))
        with self.assertRaises(RuntimeError) as error:
            translate.translate(self.source, Path(self.tmp.name) / "out.md", "secret", "openai/gpt", policy=self.policy)
        self.assertNotIn("sensitive echo", str(error.exception))
        self.assertFalse((Path(self.tmp.name) / "out.md").exists())

    def test_guidance_contact_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "Contact data"):
            translate.prepare_payload([], {"notes": ["user@example.com"]}, self.policy)




if __name__ == "__main__":
    unittest.main()
