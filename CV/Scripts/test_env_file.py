"""Tests for the local .env fallback loader — synthetic values only."""
from pathlib import Path
import tempfile
import unittest

import env_file


class ParseEnvTests(unittest.TestCase):
    def test_parses_plain_comments_export_and_quotes(self) -> None:
        text = (
            "# comment\n"
            "\n"
            "PLAIN=value\n"
            "export EXPORTED=other\n"
            "SPACED=\"a value with spaces\"\n"
            "SINGLE='quoted'\n"
            "INLINE=value # trailing comment\n"
            "EMPTY=\n"
            "NOT_A_PAIR\n"
        )
        self.assertEqual(env_file.parse_env(text), {
            "PLAIN": "value",
            "EXPORTED": "other",
            "SPACED": "a value with spaces",
            "SINGLE": "quoted",
            "INLINE": "value",
            "EMPTY": "",
        })

    def test_double_quotes_support_escapes(self) -> None:
        parsed = env_file.parse_env('KEY="line1\\nline2"')
        self.assertEqual(parsed["KEY"], "line1\nline2")


class LoadEnvFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = self.root / ".env"
        self.env.write_text(
            "OPENROUTER_API_KEY=file-secret\n"
            "OPENROUTER_MODEL=example/model\n",
            encoding="utf-8",
        )

    def test_loads_values_into_given_environ(self) -> None:
        environ: dict = {}
        env_file.load_env_file(self.env, environ)
        self.assertEqual(environ["OPENROUTER_API_KEY"], "file-secret")
        self.assertEqual(environ["OPENROUTER_MODEL"], "example/model")

    def test_existing_environment_wins(self) -> None:
        environ = {"OPENROUTER_API_KEY": "shell-secret"}
        env_file.load_env_file(self.env, environ)
        self.assertEqual(environ["OPENROUTER_API_KEY"], "shell-secret")
        self.assertEqual(environ["OPENROUTER_MODEL"], "example/model")

    def test_nonempty_shell_value_is_not_replaced_by_empty_file_value(self) -> None:
        self.env.write_text("OPENROUTER_API_KEY=\n", encoding="utf-8")
        environ = {"OPENROUTER_API_KEY": "shell-secret"}
        env_file.load_env_file(self.env, environ)
        self.assertEqual(environ["OPENROUTER_API_KEY"], "shell-secret")

    def test_missing_file_is_ignored(self) -> None:
        environ: dict = {}
        env_file.load_env_file(self.root / "absent.env", environ)
        self.assertEqual(environ, {})

    def test_get_falls_back_to_file(self) -> None:
        environ: dict = {}
        self.assertEqual(env_file.get("OPENROUTER_MODEL", path=self.env, environ=environ),
                         "example/model")
        self.assertEqual(env_file.get("ABSENT", "fallback", path=self.env, environ=environ),
                         "fallback")

    def test_find_env_file_walks_upward(self) -> None:
        nested = self.root / "a" / "b"
        nested.mkdir(parents=True)
        self.assertEqual(env_file.find_env_file(nested), self.env.resolve())


if __name__ == "__main__":
    unittest.main()
