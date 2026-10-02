"""Synthetic contract, privacy-boundary and workflow tests; no live API calls."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import jev_check as jev


def response_for(payload):
    answers = {}
    for key, q in payload["questions"].items():
        if q["type"] == "score":
            top = len(q["criteria"]) - 1
            answers[key] = {"type": "score", "score": top, "confidence": 0.9,
                            "probabilities": {str(i): float(i == top) for i in range(top + 1)}}
        else:
            answers[key] = {"type": "choice", "choice": "missing", "confidence": 0.8,
                            "probabilities": {k: float(k == "missing") for k in q["criteria"]}}
    return {"model": "jev-test", "answers": answers}


class JevTests(unittest.TestCase):
    def setUp(self):
        self.config = jev.read_json(jev.DEFAULT_REQUESTS)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, text in {"job.md": "Requires testing and leading a team.",
                           "analysis.md": "Testing: strong evidence. Leadership: unknown.",
                           "cv.md": "I tested software.", "letter.md": "I led a team.",
                           "requirements.json": json.dumps(["Testing", "Team leadership"]),
                           "policy.json": json.dumps({"reviewed": True, "redact_values": ["Synthetic Candidate"]})}.items():
            (self.root / name).write_text(text)

    def args(self, kind="fit", name="result.json"):
        args = [kind, "--job", str(self.root / "job.md"), "--policy", str(self.root / "policy.json"),
                "--output", str(self.root / name), "--reviewed"]
        if kind == "fit":
            args += ["--analysis", str(self.root / "analysis.md")]
        else:
            args += ["--document", str(self.root / ("cv.md" if kind == "cv" else "letter.md")),
                     "--requirements", str(self.root / "requirements.json")]
        return args

    def invoke(self, args):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            result = jev.main(args)
        return result, out.getvalue(), err.getvalue()

    def test_preview_never_sends(self):
        with patch.object(jev, "send") as send:
            self.invoke(self.args())
            send.assert_not_called()
        payload = jev.read_json(self.root / "result.json")
        self.assertEqual(set(payload["state"]), {"job_description", "fit_analysis"})
        self.assertNotIn("policy", payload)
        self.assertFalse((self.root / "result.md").exists())

    def test_three_independent_calls_and_visible_results(self):
        with patch.object(jev, "send", side_effect=response_for) as send:
            for kind in ("fit", "cv", "cover-letter"):
                _, stdout, _ = self.invoke(self.args(kind, "check-" + kind + ".json") + ["--send"])
                self.assertIn("match 100.0/100; confidence 90.0%", stdout)
                report = jev.read_json(self.root / ("check-" + kind + ".json"))
                self.assertEqual(report["request_sha256"], jev.digest(report["request"]))
                self.assertTrue((self.root / ("check-" + kind + ".md")).exists())
            self.assertEqual(send.call_count, 3)
            cv, letter = [call.args[0] for call in send.call_args_list[1:]]
            self.assertNotIn("fit_analysis", cv["state"])
            self.assertEqual(cv["state"]["document_markdown"], "I tested software.")
            self.assertEqual(letter["state"]["document_markdown"], "I led a team.")
            self.assertIn("requirements[1]", cv["questions"]["point_2"]["instructions"])
            self.assertIn("| Team leadership | missing | 80.0% |", (self.root / "check-cv.md").read_text())

    def test_private_identifiers_and_locators_fail_before_network(self):
        for value in ["synthetic candidate", "test@example.com", "https://example.com/jobs/1234567890",
                      "/home/example/project/file.md", "[[Knowledge/Source]]"]:
            with self.subTest(value=value):
                (self.root / "analysis.md").write_text(value)
                with patch.object(jev, "send") as send, self.assertRaises(SystemExit):
                    self.invoke(self.args() + ["--send"])
                send.assert_not_called()
                self.assertFalse((self.root / "result.json").exists())

    def test_no_redaction_of_numeric_ids_or_existing_tokens(self):
        jev.check_payload({"text": "ID 1234567890; APP_MAN_PRIVATE_0123456789abcdef01234567_0_TOKEN"},
                          ["Synthetic Candidate"])

    def test_unreviewed_policy_and_input_fail(self):
        with patch.object(jev, "send") as send:
            with self.assertRaises(SystemExit):
                self.invoke([arg for arg in self.args() if arg != "--reviewed"] + ["--send"])
            (self.root / "policy.json").write_text('{"reviewed": false, "redact_values": ["Synthetic Candidate"]}')
            with self.assertRaises(SystemExit):
                self.invoke(self.args() + ["--send"])
            send.assert_not_called()

    def test_document_requires_nonempty_checklist(self):
        for data in [[], [""], ["Testing", "Testing"], {"point": "Testing"}]:
            (self.root / "requirements.json").write_text(json.dumps(data))
            with patch.object(jev, "send") as send, self.assertRaises(SystemExit):
                self.invoke(self.args("cv") + ["--send"])
            send.assert_not_called()

    def test_mixed_modes_rejected(self):
        with patch.object(jev, "send") as send, self.assertRaises(SystemExit):
            self.invoke(self.args() + ["--document", str(self.root / "cv.md"), "--send"])
        send.assert_not_called()

    def test_output_collision_and_public_destination_fail_before_network(self):
        for output in [self.root / "analysis.md", jev.DEFAULT_REQUESTS.parent / "forbidden.json"]:
            args = self.args()
            args[args.index("--output") + 1] = str(output)
            with patch.object(jev, "send") as send, self.assertRaises(SystemExit):
                self.invoke(args + ["--send"])
            send.assert_not_called()
        (self.root / "result.md").write_text("Keep existing report")
        with patch.object(jev, "send") as send, self.assertRaises(SystemExit):
            self.invoke(self.args() + ["--send"])
        send.assert_not_called()

    def test_private_symlink_escape(self):
        private = self.root / "JobSearch"
        private.mkdir()
        (private / "escape").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            jev.check_output(private / "escape/result.json", private / "input.md", root=self.root)

    def test_score_scale_changes_with_rubric_and_hash_changes(self):
        first = jev.build_payload(self.config, "fit", "job", "analysis")
        self.config["fit"]["criteria"] = ["No match", "Full match"]
        second = jev.build_payload(self.config, "fit", "job", "analysis")
        self.assertNotEqual(jev.digest(first), jev.digest(second))
        response = response_for(second)
        response["answers"]["match"].update(score=0.25, probabilities={"0": 0.75, "1": 0.25})
        self.assertEqual(jev.validate_response(response, second)["match"]["match_score"], 25)

    def test_bad_response_does_not_create_result(self):
        payload = jev.build_payload(self.config, "fit", "job", "analysis")
        for change in [{"confidence": None}, {"confidence": float("nan")}, {"score": True},
                       {"score": 900}, {"probabilities": {"0": 1}}, {"type": "noul"}, {"score": 1}]:
            response = response_for(payload)
            response["answers"]["match"].update(change)
            with self.subTest(change=change), patch.object(jev, "send", return_value=response), self.assertRaises(SystemExit):
                self.invoke(self.args() + ["--send"])
            self.assertFalse((self.root / "result.json").exists())
        with self.assertRaises(ValueError):
            jev.validate_response({"model": "test", "answers": {}}, payload)

    def test_openrouter_jev_key_is_explicit_and_can_be_shared(self):
        payload = jev.build_payload(self.config, "fit", "job", "analysis")
        # Never silently charge the application budget or use a legacy key.
        with patch.dict(jev.os.environ, {"OPENROUTER_API_KEY": "app-secret",
                                         "TYPESAFE_API_KEY": "legacy-secret"}, clear=True), \
                patch.object(jev.urllib.request, "build_opener") as opener:
            with self.assertRaisesRegex(ValueError, "OPENROUTER_JEV_API_KEY"):
                jev.send(payload)
            opener.assert_not_called()
        for app_key in ("other-secret", "jev-secret"):
            with self.subTest(shared=app_key == "jev-secret"), \
                    patch.dict(jev.os.environ, {"OPENROUTER_API_KEY": app_key,
                                               "OPENROUTER_JEV_API_KEY": "jev-secret"}, clear=True), \
                    patch.object(jev.urllib.request, "build_opener") as opener:
                response = response_for(payload)
                opener.return_value.open.return_value.__enter__.return_value = io.StringIO(json.dumps(response))
                self.assertEqual(jev.send(payload), response)
                request = opener.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/systemone")
                self.assertEqual(request.get_header("Authorization"), "Bearer jev-secret")
                self.assertEqual(json.loads(request.data), payload)

    def test_api_errors_do_not_echo_payload_or_credentials(self):
        payload = jev.build_payload(self.config, "fit", "job", "analysis")
        with patch.dict(jev.os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, "not set"):
            jev.send(payload)
        error = urllib.error.HTTPError(jev.ENDPOINT, 403, "private detail", {}, io.BytesIO(b"private body"))
        with patch.dict(jev.os.environ, {"OPENROUTER_JEV_API_KEY": "synthetic-secret"}), patch.object(jev.urllib.request, "build_opener") as opener:
            opener.return_value.open.side_effect = error
            with self.assertRaisesRegex(ValueError, "HTTP 403; response body withheld") as caught:
                jev.send(payload)
            self.assertNotIn("private", str(caught.exception))
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, jev.ENDPOINT)
            self.assertEqual(json.loads(request.data), payload)


if __name__ == "__main__":
    unittest.main()
