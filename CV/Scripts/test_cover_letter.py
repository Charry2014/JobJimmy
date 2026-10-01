"""Cover-letter content preservation and template safety checks.

Tests activate once the supplied cover-letter document template and its anchor
configuration exist in CV/Templates; otherwise they are skipped.
"""
from pathlib import Path
import re
import tempfile
import unittest
import zipfile
from xml.dom import minidom as D

import cover_letter as cl
import cv

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_READY = cl.TEMPLATE.exists() and cl.CONFIG.exists()


def cv_templates():
    templates = []
    for path in sorted((ROOT / 'Templates').glob('*.odt')):
        if path == cl.TEMPLATE:
            continue
        try:
            with zipfile.ZipFile(path) as z:
                z.read(cv.MAP)
            templates.append(path)
        except (KeyError, zipfile.BadZipFile, OSError):
            continue
    return templates


def template_mailto(template_path):
    with zipfile.ZipFile(template_path) as z:
        doc = D.parseString(z.read('content.xml'))
    for link in doc.getElementsByTagName('text:a'):
        href = link.getAttribute('xlink:href')
        if href.startswith('mailto:'):
            return href
    return None


@unittest.skipIf(not TEMPLATE_READY, 'Cover-letter template and anchor configuration not imported yet')
class CoverLetterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.md = Path(self.tmp.name) / 'example-cover-letter.md'
        self.odt = self.md.with_suffix('.odt')
        self.text = (cl.ROOT / 'Templates/Cover-Letter.md').read_text()
        replacements = {'date': '1 September 2026', 'recipient and address': 'Hiring Manager\nExample GmbH\nCity',
                        'complete subject line': 'Application - Example Role',
                        'salutation': 'Dear Hiring Manager,',
                        'letter paragraphs': 'First paragraph with R&D and Unicode: Greetings.\nA soft wrap.\n\nSecond paragraph.  \nAn explicit break.',
                        'closing': 'Kind regards,'}
        for key, value in replacements.items():
            self.text = self.text.replace('{{' + key + '}}', value)
        self.template_email = template_mailto(cl.TEMPLATE)
        self.template_email_line = self.template_email[7:] if self.template_email else 'your.name@example.com'
        if self.template_email:
            # Keep the draft's signature email identical to the template's own
            # contact so the unchanged-run/changed-run behaviours can both be
            # asserted generically.
            self.text = self.text.replace('your.name@example.com', self.template_email_line)
        self.md.write_text(self.text)

    def test_all_content_and_package_styles_preserved(self):
        values = cl.render(self.md, cl.TEMPLATE, self.odt)
        with zipfile.ZipFile(self.odt) as out, zipfile.ZipFile(cl.TEMPLATE) as template:
            self.assertEqual(out.infolist()[0].filename, 'mimetype')
            self.assertEqual(out.infolist()[0].compress_type, zipfile.ZIP_STORED)
            self.assertNotIn('Thumbnails/thumbnail.png', out.namelist())
            for name in template.namelist():
                if name not in ('content.xml', 'META-INF/manifest.xml', 'Thumbnails/thumbnail.png'):
                    self.assertEqual(out.read(name), template.read(name), name)
            doc = D.parseString(out.read('content.xml'))
            actual = [cl.visible(p) for p in cv.paragraphs(doc) if cl.visible(p)]
            expected = [p for name in cl.SECTIONS for p in values[name]]
            self.assertEqual(actual, expected)
            self.assertEqual(len(values['Body']), 2)
            self.assertTrue(any('Greetings. A soft wrap.' in p for p in actual))
            if self.template_email:
                self.assertIn(self.template_email, doc.toxml())

    def test_many_paragraphs_and_changed_signature(self):
        text = self.text.replace('Second paragraph.  \nAn explicit break.',
                                 '\n\n'.join(f'Paragraph {i}.' for i in range(20)))
        self.md.write_text(text.replace(self.template_email_line, 'new@example.com'))
        values = cl.render(self.md, cl.TEMPLATE, self.odt)
        self.assertEqual(len(values['Body']), 21)
        with zipfile.ZipFile(self.odt) as z:
            content = z.read('content.xml').decode()
        if self.template_email:
            self.assertNotIn(self.template_email, content)
        self.assertIn('new@example.com', content)

    def test_bad_markdown_rejected_without_output(self):
        for text in (self.text + '\n## Body\nDuplicate', self.text.replace('## Date', '## Unknown'),
                     'Unmapped text\n' + self.text, self.text.replace('Kind regards,', '{{closing}}'),
                     self.text.replace('Kind regards,', '**Kind regards,**'),
                     self.text.replace('## Closing\n\nKind regards,', ''),
                     self.text.replace('Kind regards,', '')):
            with self.subTest(text=text):
                self.md.write_text(text)
                with self.assertRaises(ValueError):
                    cl.render(self.md, cl.TEMPLATE, self.odt)
                self.assertFalse(self.odt.exists())

    def test_wrong_template_and_overwrite_rejected(self):
        cv_list = cv_templates()
        if cv_list:
            with self.assertRaisesRegex(ValueError, 'Template structure'):
                cl.render(self.md, cv_list[0], self.odt)
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            cl.render(self.md, cl.TEMPLATE, cl.TEMPLATE)
        with self.assertRaises(ValueError):
            cl.render(self.md, cl.TEMPLATE, self.md)

    def test_missing_signature_contacts_rejected(self):
        phone_pattern = re.compile(r'^\+?[\d ()-]{7,}$')
        signature_lines = [line.strip() for line in
                           self.text.split('## Signature', 1)[1].splitlines() if line.strip()]
        phone = next(line for line in signature_lines[1:] if phone_pattern.fullmatch(line))
        email = next(line for line in signature_lines[1:] if '@' in line)
        for contact in (phone + '\n', email + '\n'):
            with self.subTest(contact=contact):
                self.md.write_text(self.text.replace(contact, ''))
                with self.assertRaisesRegex(ValueError, 'Signature must retain'):
                    cl.render(self.md, cl.TEMPLATE, self.odt)
                self.assertFalse(self.odt.exists())


if __name__ == '__main__':
    unittest.main()
