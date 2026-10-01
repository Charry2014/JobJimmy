"""Tests for tools/check_env.py — synthetic values only, no real secrets."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import check_env as ce  # noqa: E402

SECRET = "sk-synthetic-should-never-print"


class CheckEnvTests(unittest.TestCase):
    def check(self, **kwargs):
        env = kwargs.pop("environ", {})
        return ce.check(root=Path("."), environ=env, which=lambda name: "/bin/" + name, **kwargs)

    def test_all_required_present_is_ok(self) -> None:
        result = self.check(version_info=(3, 12, 0))
        self.assertTrue(result["ok"])
        self.assertEqual(result["missing_keys"], ["OPENROUTER_API_KEY", "OPENROUTER_MODEL", "TYPESAFE_API_KEY"])

    def test_missing_uv_fails(self) -> None:
        result = ce.check(
            root=Path("."), environ={}, which=lambda name: None if name == "uv" else "/bin/" + name
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["tools"]["uv"])

    def test_old_python_fails(self) -> None:
        result = self.check(version_info=(3, 10, 0))
        self.assertFalse(result["ok"])
        self.assertFalse(result["python"]["ok"])

    def test_keys_report_set_flag_only(self) -> None:
        result = self.check(environ={"TYPESAFE_API_KEY": SECRET})
        self.assertTrue(result["keys"]["TYPESAFE_API_KEY"]["set"])
        self.assertNotIn("TYPESAFE_API_KEY", result["missing_keys"])

    def test_secret_value_never_rendered(self) -> None:
        result = self.check(environ={"TYPESAFE_API_KEY": SECRET})
        text = ce.render_text(result)
        self.assertNotIn(SECRET, text)
        self.assertNotIn(SECRET, json.dumps(result))

    def test_missing_private_tree_is_reported(self) -> None:
        result = ce.check(
            root=Path("/nonexistent-appman-root"),
            environ={},
            which=lambda name: "/bin/" + name,
        )
        self.assertFalse(result["private_tree"])
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
