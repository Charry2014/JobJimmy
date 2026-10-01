"""Tests for the tools/privacy_screen.py gate — synthetic data only."""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import privacy_screen as ps  # noqa: E402


class ScreenTextTests(unittest.TestCase):
    def setUp(self) -> None:
        ps.set_derived_patterns([
            ("candidate-name", "Alex Fictional"),
            ("company-name", "Fictional Robotics GmbH"),
            ("application-slug", "2026-01-fictional-robotics-lead"),
            ("application-slug", "fictional-robotics-lead"),
            ("recruiter-email", "jane.doe@agency.test"),
        ])

    def tearDown(self) -> None:
        ps.set_derived_patterns([])

    def screen(self, text: str):
        return ps.screen_text(text)

    def test_candidate_name_flagged(self) -> None:
        hits = self.screen("Prepared for Alex Fictional in Munich.")
        self.assertEqual([h[0] for h in hits], ["candidate-name"])

    def test_company_name_case_insensitive(self) -> None:
        hits = self.screen("fictional robotics gmbh builds chargers")
        self.assertEqual(hits[0][0], "company-name")

    def test_application_slug_flagged(self) -> None:
        hits = self.screen("see JobSearch/Applications/2026-01-fictional-robotics-lead/…")
        categories = {h[0] for h in hits}
        self.assertIn("application-slug", categories)

    def test_recruiter_email_flagged(self) -> None:
        hits = self.screen("contact jane.doe@agency.test today")
        categories = {h[0] for h in hits}
        self.assertIn("recruiter-email", categories)
        self.assertIn("email", categories)

    def test_placeholder_email_allowed(self) -> None:
        self.assertEqual(self.screen("write to company@example.com"), [])

    def test_fictional_phone_allowed(self) -> None:
        self.assertEqual(self.screen("call +1 555-0100 for details"), [])

    def test_real_phone_flagged(self) -> None:
        hits = self.screen("call +49 89 12345678 today")
        self.assertEqual([h[0] for h in hits], ["phone"])

    def test_linkedin_person_flagged(self) -> None:
        hits = self.screen("profile: linkedin.com/in/janedoe-rec")
        self.assertEqual(hits[0][0], "linkedin-profile")

    def test_placeholder_linkedin_allowed(self) -> None:
        self.assertEqual(self.screen("linkedin.com/in/your-name"), [])

    def test_iban_flagged(self) -> None:
        hits = self.screen("IBAN DE89 3704 0044 0532 0130 00")
        self.assertEqual(hits[0][0], "iban")

    def test_private_knowledge_path_flagged(self) -> None:
        hits = self.screen("opened JobSearch/Knowledge/Sources/Character-context")
        self.assertEqual(hits[0][0], "private-knowledge-path")

    def test_word_boundary_no_substring_hits(self) -> None:
        self.assertEqual(self.screen("the process closes encyclopaedic gaps"), [])

    def test_no_raw_value_in_report(self) -> None:
        findings = [
            ps.Finding("candidate-name", "README.md", 12, ps.mask("Alex Fictional")),
        ]
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = ps.report(findings, 5, True)
        output = buffer.getvalue()
        self.assertEqual(code, 1)
        self.assertNotIn("Alex Fictional", output)
        self.assertIn("[candidate-name]", output)


class DerivationTests(unittest.TestCase):
    def test_derive_from_private_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge = root / "JobSearch" / "Knowledge"
            knowledge.mkdir(parents=True)
            (knowledge / "Overview.md").write_text(
                "---\ntype: cv-knowledge\nsubject: Alex Fictional\n---\n", encoding="utf-8"
            )
            companies = root / "JobSearch" / "Companies"
            companies.mkdir()
            (companies / "acme.md").write_text(
                "---\ncompany: Acme Rocketry\n---\n", encoding="utf-8"
            )
            recruiters = root / "JobSearch" / "Recruiters"
            recruiters.mkdir()
            (recruiters / "agency-jane.md").write_text(
                "---\nrecruitment_company: Talent Hunt\nrecruiter_name: Jane Doe\n"
                "email: jane@talenthunt.test\nphone: \"+49 89 123456\"\n---\n",
                encoding="utf-8",
            )
            apps = root / "JobSearch" / "Applications" / "2026-02-acme-rocketry-lead"
            apps.mkdir(parents=True)
            identifiers = ps.derive_identifiers(root / "JobSearch")
            values = {(cat, val) for cat, val in identifiers}
            self.assertIn(("candidate-name", "Alex Fictional"), values)
            self.assertIn(("company-name", "Acme Rocketry"), values)
            self.assertIn(("recruiter-email", "jane@talenthunt.test"), values)
            self.assertIn(("application-slug", "2026-02-acme-rocketry-lead"), values)
            self.assertIn(("application-slug", "acme-rocketry-lead"), values)

    def test_absent_private_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            identifiers = ps.derive_identifiers(Path(tmp) / "JobSearch")
            self.assertEqual(identifiers, [])


class CliTests(unittest.TestCase):
    def test_clean_run_on_tmp_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "README.md").write_text("# JobJimmy\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = ps.main(["--all"], root=root)
            self.assertEqual(code, 0)
            self.assertIn("PRIVACY SCREEN CLEAN", buffer.getvalue())

    def test_violation_run_on_tmp_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "README.md").write_text(
                "# JobJimmy\n\nContact alex.fictional@somewhere.test now.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = ps.main(["--all"], root=root)
            self.assertEqual(code, 1)
            self.assertIn("PRIVACY VIOLATIONS FOUND", buffer.getvalue())
            self.assertIn("[email]", buffer.getvalue())

    def test_private_tree_files_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            private = root / "JobSearch" / "Companies"
            private.mkdir(parents=True)
            (private / "leaky.md").write_text(
                "email jane.doe@agency.test\n", encoding="utf-8"
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = ps.main(["--all"], root=root)
            self.assertEqual(code, 0)


class IndexBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q")
        ps.set_derived_patterns([])

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def categories(self):
        hits = ps.screen_index(self.root, all_files=True)
        hits += ps.screen_targets(self.root, ps.gather_targets(self.root, "all", []))
        return {hit.category for hit in hits}

    def test_forced_private_file_in_index_is_blocked(self):
        (self.root / ".gitignore").write_text("/JobSearch/\n")
        (self.root / "JobSearch").mkdir()
        (self.root / "JobSearch/note.md").write_text("Synthetic only")
        self.git("add", "-f", "JobSearch/note.md")
        self.assertIn("private-tree-file-in-public-index", self.categories())

    def test_staged_text_is_scanned_even_after_worktree_is_cleaned(self):
        path = self.root / "note.md"
        path.write_text("synthetic@fixture.test")
        self.git("add", "note.md")
        path.write_text("Clean working copy")
        self.assertIn("email", self.categories())
        path.unlink()
        self.assertIn("email", self.categories())

    def test_staged_binary_document_is_blocked(self):
        (self.root / "document.pdf").write_bytes(b"%PDF-1.7\0synthetic")
        self.git("add", "document.pdf")
        self.assertIn("document-file-added-to-public-repo", self.categories())

    def test_unicode_and_newline_paths_are_scanned(self):
        path = self.root / "résumé with\nnewline.md"
        path.write_text("synthetic@fixture.test")
        self.git("add", path.name)
        self.assertIn("email", self.categories())

    def test_ignored_text_is_scanned_by_all(self):
        (self.root / ".gitignore").write_text("ignored/\n")
        (self.root / "ignored").mkdir()
        (self.root / "ignored/output.md").write_text("synthetic@fixture.test")
        self.assertIn("email", self.categories())

    def test_private_symlink_is_not_followed(self):
        (self.root / "JobSearch").mkdir()
        (self.root / "JobSearch/note.md").write_text("Synthetic only")
        (self.root / "public.md").symlink_to(self.root / "JobSearch/note.md")
        self.assertIn("public-symlink-or-path-escape", self.categories())

    def test_filename_is_checked(self):
        (self.root / "synthetic@fixture.test.md").write_text("No content")
        self.assertIn("filename-email", self.categories())


if __name__ == "__main__":
    unittest.main()