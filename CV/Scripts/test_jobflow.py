"""Synthetic tests for the local workflow steps (no private tree needed)."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import jobflow as jf
import redact_md as rm

PUBLIC = Path(__file__).resolve().parents[2]

EMAIL_TEXT = """From: Jane Placeholder <jane.placeholder@agency.example.com>
To: Candidate Person <candidate@example.org>
Subject: Head of Platform role

Hi Candidate,

Our client Example Robotics is hiring a Head of Platform in Exampletown.

## Requirements

- Ten years of platform leadership
- Fluent English

Call me on +00 000 0000000 or 0000 0000000.
Best regards,
Jane Placeholder
linkedin.com/in/your-linkedin
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(PUBLIC / "Templates", self.root / "Templates",
                        ignore=shutil.ignore_patterns("jobsearch-repository"))
        private = self.root / "JobSearch"
        (private / "Templates").mkdir(parents=True)
        (private / "Knowledge").mkdir()
        (private / "Templates" / "redaction-policy.json").write_text(json.dumps(
            {"reviewed": True, "redact_values": [
                {"value": "Candidate Person", "label": "CANDIDATE"},
                "candidate@example.org", "Former Employer AG"]}))
        (private / "Knowledge" / "Overview.md").write_text(
            "# Overview\n\nCandidate Person led platform work at Former Employer AG.\n")
        self.vault = jf.Vault(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def policy_values(self):
        return [v for v, _ in rm.policy_entries(self.vault.policy)]

    def captured(self):
        return jf.capture(self.vault, EMAIL_TEXT, "https://jobs.example.com/123")

    def spec(self, **extra):
        spec = {"capture": "latest", "slug": "2026-11-example-robotics-platform",
                "position": "Head of Platform", "location": "Exampletown, hybrid",
                "source": "Email", "publisher_type": "recruiter",
                "company": {"slug": "example-robotics", "name": "Example Robotics",
                            "website": "https://robotics.example.com", "location": "Exampletown"},
                "recruiter": {"agency": "Agency Example", "agency_slug": "agency-example",
                              "name": self.token("Jane Placeholder"),
                              "email": self.token("jane.placeholder@agency.example.com")}}
        spec.update(extra)
        return spec

    def token(self, value):
        registry = rm.load_registry(self.vault.registry)
        return next(t for t, v in registry.items() if v == value)


class CaptureTests(Base):
    def test_capture_adds_contacts_and_header_names_and_writes_clean_safe_copy(self):
        result = self.captured()
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["added"]["EMAIL"], 1)  # the candidate's own address was listed
        self.assertEqual(result["added"]["PHONE"], 2)
        self.assertEqual(result["added"]["LINKEDIN"], 1)
        self.assertGreaterEqual(result["added"]["PERSON"], 1)
        folder = self.vault.capture_dir()
        safe = (folder / "advert-safe.md").read_text()
        for private in ("Jane Placeholder", "Placeholder", "jane.placeholder@", "Candidate Person",
                        "+00 000", "linkedin.com/in/"):
            self.assertNotIn(private, safe)
        self.assertIn("Example Robotics", safe)  # the target employer stays visible
        self.assertEqual((folder / "original.txt").read_text(), EMAIL_TEXT)
        self.assertEqual((folder / "original.txt").stat().st_mode & 0o777, 0o600)
        self.assertEqual(rm.restore(safe, rm.load_registry(self.vault.registry)), EMAIL_TEXT)

    def test_recapture_adds_nothing_new(self):
        self.captured()
        before = self.policy_values()
        self.assertEqual(sum(jf.capture(self.vault, EMAIL_TEXT)["added"].values()), 0)
        self.assertEqual(self.policy_values(), before)

    def test_surname_inside_other_words_is_not_listed_alone(self):
        names = dict(jf.discover("From: Ann Marketing <a@x.example.com>\nMarketingteam\n"))
        self.assertIn("Ann Marketing", names)
        self.assertNotIn("Marketing", names)

    def test_last_first_header_form(self):
        names = dict(jf.discover('From: "Placeholder, Jane" <j@x.example.com>\n'))
        self.assertIn("Jane Placeholder", names)

    def test_provider_placeholders_refused(self):
        with self.assertRaisesRegex(ValueError, "placeholders"):
            jf.capture(self.vault, "Contact [EMAIL] for details\n")

    def test_add_name_reprepares_safe_copy(self):
        self.captured()
        result = jf.add_name(self.vault, "Exampletown")
        self.assertEqual(result["added"], 1)
        safe = (self.vault.capture_dir() / "advert-safe.md").read_text()
        self.assertNotIn("Exampletown", safe)


class RecordTests(Base):
    def test_records_create_linked_notes_and_archive_advert_verbatim(self):
        self.captured()
        status = jf.records(self.vault, self.spec())
        self.assertEqual(status["application"], "created")
        self.assertEqual(status["research"], "created")
        self.assertEqual(status["company"], "created")
        self.assertEqual(status["recruiter"], "created")
        slug = "2026-11-example-robotics-platform"
        app = self.vault.application(slug).read_text()
        self.assertIn('company: "[[Companies/example-robotics]]"', app)
        self.assertIn('recruiter: "[[Recruiters/agency-example-jane-placeholder]]"', app)
        self.assertIn("# Head of Platform — Example Robotics", app)
        self.assertIn(f"Activities/{slug}-research", app)
        self.assertNotIn("{{", app)
        research = self.vault.research(slug).read_text()
        self.assertIn(EMAIL_TEXT.strip(), research)
        self.assertIn("advert_url: https://jobs.example.com/123", research)
        self.assertNotIn("{{", research)
        self.assertEqual(jf.advert_text(research), EMAIL_TEXT)
        recruiter = (self.root / "JobSearch/Recruiters/agency-example-jane-placeholder.md").read_text()
        self.assertIn("recruiter_name: Jane Placeholder", recruiter)
        self.assertNotIn("@@", recruiter)
        company = (self.root / "JobSearch/Companies/example-robotics.md").read_text()
        self.assertIn(f"- [[Applications/{slug}/{slug}]]", company)

    def test_rerun_is_a_no_op(self):
        self.captured()
        jf.records(self.vault, self.spec())
        before = {p: p.read_text() for p in (self.root / "JobSearch").rglob("*.md")}
        status = jf.records(self.vault, self.spec())
        self.assertEqual({status[k] for k in ("application", "research", "company", "recruiter")}, {"exists"})
        self.assertEqual(before, {p: p.read_text() for p in (self.root / "JobSearch").rglob("*.md")})

    def test_same_advert_url_in_another_application_is_refused(self):
        self.captured()
        jf.records(self.vault, self.spec(advert_url="https://jobs.example.com/123"))
        with self.assertRaisesRegex(ValueError, "already recorded"):
            jf.records(self.vault, self.spec(slug="2026-11-example-robotics-other",
                                             advert_url="https://jobs.example.com/123"))

    def test_unknown_token_in_spec_refused(self):
        self.captured()
        with self.assertRaisesRegex(ValueError, "Unknown privacy tokens"):
            jf.records(self.vault, self.spec(location="@@PERSON_99@@"))

    def test_update_section_restores_tokens_and_protects_advert(self):
        self.captured()
        jf.records(self.vault, self.spec())
        slug = "2026-11-example-robotics-platform"
        jf.update(self.vault, slug, "research", "Research notes",
                  f"### Key requirements\n\n- Platform leadership (contact {self.token('Jane Placeholder')})\n")
        jf.update(self.vault, slug, "application", "Assessment", "Assessment: 7/10.\n", {"fit": "7"})
        research = self.vault.research(slug).read_text()
        self.assertIn("contact Jane Placeholder", research)
        self.assertEqual(jf.advert_text(research), EMAIL_TEXT)  # advert headings untouched
        app = self.vault.application(slug).read_text()
        self.assertIn("fit: 7", app)
        self.assertIn("## Assessment\n\nAssessment: 7/10.\n\n## Strengths", app)
        jf.update(self.vault, slug, "research", "Research notes", "### Jev fit check\n\nScore 0.8\n", append=True)
        notes = jf.section_text(self.vault.research(slug).read_text(), "Research notes")
        self.assertLess(notes.index("Key requirements"), notes.index("Jev fit check"))
        with self.assertRaisesRegex(ValueError, "never rewritten"):
            jf.update(self.vault, slug, "research", "Original job advert", "changed")


class BundleTests(Base):
    def setUp(self):
        super().setUp()
        self.captured()
        jf.records(self.vault, self.spec())
        self.slug = "2026-11-example-robotics-platform"
        self.cv = self.vault.app_dir(self.slug) / "CV"
        self.cv.mkdir()
        (self.cv / "robotics-cv-draft.md").write_text("Candidate Person\n\nLed Former Employer AG platform.\n")

    def test_bundle_writes_checked_safe_copies(self):
        out, results = jf.bundle(self.vault, self.slug)
        self.assertTrue(all(state == "PASS" for _, state, _ in results), results)
        names = {name for name, _, _ in results}
        self.assertTrue({"advert.md", "research.md", "application.md", "company.md",
                         "knowledge/Overview.md", "drafts/robotics-cv-draft.md"} <= names)
        values = self.policy_values()
        for path in out.rglob("*.md"):
            self.assertEqual(rm.scan_reasons(path.read_text(), values), [], path.name)
        self.assertNotIn("Head of Platform role", (out / "research.md").read_text())

    def test_restore_writes_drafts_and_refuses_user_changed_ones(self):
        out, _ = jf.bundle(self.vault, self.slug)
        safe = (out / "drafts/robotics-cv-draft.md").read_text()
        (out / "out/robotics-cv-draft.md").write_text(safe.replace("Led", "Built and led"))
        (out / "out/robotics-cover-letter-prose.md").write_text(f"## Body\n\nDear {self.token('Jane Placeholder')}\n")
        results = {name: state for name, state, _ in jf.restore_drafts(self.vault, self.slug)}
        self.assertEqual(results, {"robotics-cv-draft.md": "RESTORED", "robotics-cover-letter-prose.md": "RESTORED"})
        self.assertEqual((self.cv / "robotics-cv-draft.md").read_text(),
                         "Candidate Person\n\nBuilt and led Former Employer AG platform.\n")
        self.assertIn("Dear Jane Placeholder", (self.cv / "robotics-cover-letter-prose.md").read_text())
        # The user edits the draft in Obsidian; a stale model response must not overwrite it.
        (self.cv / "robotics-cv-draft.md").write_text("User edit\n")
        (out / "out/robotics-cv-draft.md").write_text("Model text\n")
        results = {name: state for name, state, _ in jf.restore_drafts(self.vault, self.slug)}
        self.assertEqual(results, {"robotics-cv-draft.md": "REFUSED"})
        self.assertEqual((self.cv / "robotics-cv-draft.md").read_text(), "User edit\n")

    def test_restore_refuses_provider_placeholders(self):
        out, _ = jf.bundle(self.vault, self.slug)
        (out / "out/robotics-cv-draft.md").write_text("Contact [EMAIL]\n")
        results = jf.restore_drafts(self.vault, self.slug)
        self.assertEqual(results[0][1], "REFUSED")

    def test_render_requires_document_language(self):
        with self.assertRaisesRegex(ValueError, "document_language"):
            jf.document_language(self.vault, self.slug)
        jf.update(self.vault, self.slug, "research", fields={"document_language": "de"})
        self.assertEqual(jf.document_language(self.vault, self.slug), "de")


class ReviewFixTests(Base):
    def test_lowercase_or_team_headers_are_not_names(self):
        names = dict(jf.discover("To: hiring team\nFrom: Talent <t@example.com>\nCc: Jane Placeholder\n"))
        self.assertNotIn("hiring team", names)
        self.assertIn("Jane Placeholder", names)
        self.assertNotIn("Placeholder", names)  # no surname-alone entries

    def test_add_name_without_capture_updates_policy(self):
        result = jf.add_name(self.vault, "Someone Example")
        self.assertEqual((result["added"], result["safe"]), (1, None))
        self.assertIn("Someone Example", self.policy_values())

    def test_bundle_lists_unlisted_contacts_instead_of_withholding(self):
        self.captured()
        jf.records(self.vault, self.spec())
        slug = "2026-11-example-robotics-platform"
        jf.update(self.vault, slug, "company", "Contacts", "- press@robotics.example.com\n")
        _, results = jf.bundle(self.vault, slug)
        states = {name: state for name, state, _ in results}
        self.assertEqual(states["policy"], "UPDATED")
        self.assertEqual(states["company.md"], "PASS")
        self.assertIn("press@robotics.example.com", self.policy_values())

    def test_update_recruiter_note_and_find(self):
        self.captured()
        jf.records(self.vault, self.spec())
        slug = "2026-11-example-robotics-platform"
        jf.update(self.vault, slug, "recruiter", "Contact details", "General agency line.\n")
        recruiter = (self.root / "JobSearch/Recruiters/agency-example-jane-placeholder.md").read_text()
        self.assertIn("General agency line.", recruiter)
        found = jf.find(self.vault, "example-robotics")
        self.assertEqual(found["applications"], [slug])
        self.assertTrue(found["company note"])
        self.assertEqual(jf.find(self.vault, "agency-example")["agency recruiter notes"], 1)

    def test_template_drift_reported(self):
        self.captured()
        private = self.root / "JobSearch/Templates/Application.md"
        private.write_text((self.root / "Templates/Application.md").read_text() + "\n## Extra\n")
        status = jf.records(self.vault, self.spec())
        self.assertIn("Application", status["template drift"])


class NoteEditingTests(unittest.TestCase):
    def test_yaml_values_quoted_when_needed(self):
        self.assertEqual(jf.yaml_value("[[Companies/x]]"), '"[[Companies/x]]"')
        self.assertEqual(jf.yaml_value("Berlin: hybrid"), '"Berlin: hybrid"')
        self.assertEqual(jf.yaml_value("Head of R&D"), "Head of R&D")

    def test_headings_inside_code_fences_ignored(self):
        text = "---\na: 1\n---\n## One\n\n```\n## Two\n```\n\n## Three\n\nx\n"
        self.assertIn("## Two", jf.section_text(text, "One"))


if __name__ == "__main__":
    unittest.main()
