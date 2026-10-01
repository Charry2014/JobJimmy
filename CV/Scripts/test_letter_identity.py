"""Synthetic local identity assembly checks, independent of ODT templates."""
import io
from contextlib import redirect_stdout, redirect_stderr
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import cover_letter as cl


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.draft = self.root / 'prose.md'
        self.identity = self.root / 'identity.json'
        values = {'Sender': '{{local sender}}', 'Signature': '{{local signature}}',
                  'Date': '29.09.2026', 'Recipient': 'Example Organisation',
                  'Subject': 'Application', 'Salutation': 'Dear Hiring Manager,',
                  'Body': 'First paragraph.\n\nSecond paragraph.', 'Closing': 'Kind regards,'}
        self.draft.write_text('\n\n'.join('## ' + key + '\n\n' + values[key] for key in cl.SECTIONS))
        self.fields = {'Sender': ['Synthetic Candidate', 'Example Street'],
                       'Signature': ['Synthetic Candidate', '+00 000 0000000', 'user@example.com']}
        self.identity.write_text(json.dumps(self.fields))

    def test_local_hydration_preserves_body_and_full_signature(self):
        values = cl.read_markdown(self.draft, self.identity)
        self.assertEqual(values['Signature'], self.fields['Signature'])
        self.assertEqual(values['Body'], ['First paragraph.', 'Second paragraph.'])
        self.assertIn('{{local sender}}', self.draft.read_text())

    def test_check_identity_reports_only_completeness(self):
        output = io.StringIO()
        with patch('sys.argv', ['cover_letter.py', 'check-identity', str(self.identity)]), redirect_stdout(output):
            cl.main()
        self.assertIn('complete', output.getvalue())
        for line in self.fields['Signature']:
            self.assertNotIn(line, output.getvalue())

    def test_check_identity_rejects_missing_or_placeholder_contact(self):
        with self.assertRaisesRegex(ValueError, 'Cannot read local identity'):
            cl.load_identity(self.root / 'missing.json')
        self.fields['Signature'][-1] = '[EMAIL]'
        self.identity.write_text(json.dumps(self.fields))
        with self.assertRaisesRegex(ValueError, 'Signature must retain'):
            cl.load_identity(self.identity)

    def test_hydration_cli_produces_readable_complete_draft_and_refuses_overwrite(self):
        output = self.root / 'complete.md'
        args = ['cover_letter.py', 'hydrate-identity', str(self.draft), str(self.identity), str(output)]
        with patch('sys.argv', args), redirect_stdout(io.StringIO()):
            cl.main()
        self.assertEqual(cl.read_markdown(output)['Signature'], self.fields['Signature'])
        before = output.read_bytes()
        with patch('sys.argv', args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cl.main()
        self.assertEqual(output.read_bytes(), before)

    def test_identity_renders_into_synthetic_odt(self):
        template = self.root / 'template.odt'
        config = self.root / 'anchors.json'
        output = self.root / 'letter.odt'
        content = ('<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
                   'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
                   'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
                   'xmlns:xlink="http://www.w3.org/1999/xlink"><office:body><office:text>'
                     + ''.join(('<text:p/>' if name == 'Salutation' else '') + '<text:p>' + name + '</text:p>'
                               for name in cl.SECTIONS)
                    + '<text:p>Signature contacts<draw:a xlink:href="https://example.com/profile"/></text:p>'
                   + '</office:text></office:body></office:document-content>')
        with zipfile.ZipFile(template, 'w') as z:
            z.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
            z.writestr('content.xml', content)
            z.writestr('META-INF/manifest.xml', '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>')
        config.write_text(json.dumps({'paragraph_count': 10, 'body_spacer_index': None,
                                      'anchors': {name: {'index': i + (i >= cl.SECTIONS.index('Salutation')),
                                                         'count': 2 if name == 'Signature' else 1,
                                                         'text': name}
                                                  for i, name in enumerate(cl.SECTIONS)}}))
        values = cl.render(self.draft, template, output, config_path=config, identity=self.identity)
        with zipfile.ZipFile(output) as z:
            normal = cl.D.parseString(z.read('content.xml'))
        normal_paragraphs = [cl.visible(p) for p in cl.cv.paragraphs(normal)]
        self.assertEqual(normal_paragraphs.index(values['Salutation'][0]) -
                         normal_paragraphs.index(values['Subject'][0]), 2)
        values = cl.render(self.draft, template, output, config_path=config,
                           identity=self.identity, compact_title_gap=True)
        self.assertEqual(values['Signature'], self.fields['Signature'])
        with zipfile.ZipFile(output) as z:
            rendered = z.read('content.xml').decode()
        self.assertIn('user@example.com', rendered)
        self.assertNotIn('{{', rendered)
        doc = cl.D.parseString(rendered)
        paragraphs = [cl.visible(p) for p in cl.cv.paragraphs(doc)]
        self.assertIn('Second paragraph.', paragraphs)
        self.assertIn('Synthetic Candidate\nExample Street', paragraphs)
        self.assertIn('\n'.join(self.fields['Signature'][1:]), paragraphs)
        self.assertEqual(paragraphs.index(values['Salutation'][0]) -
                         paragraphs.index(values['Subject'][0]), 1)
        self.assertEqual(len(doc.getElementsByTagName('draw:a')), 1)

    def test_missing_contact_rejected(self):
        self.fields['Signature'].pop()
        self.identity.write_text(json.dumps(self.fields))
        with self.assertRaisesRegex(ValueError, 'Signature must retain'):
            cl.read_markdown(self.draft, self.identity)

    def test_unhydrated_placeholder_cannot_be_rendered(self):
        with self.assertRaisesRegex(ValueError, 'Fill in'):
            cl.read_markdown(self.draft)

    def test_identity_cannot_inject_another_section(self):
        self.fields['Sender'] = ['Synthetic\n## Body\nReplacement']
        self.identity.write_text(json.dumps(self.fields))
        with self.assertRaises(ValueError):
            cl.read_markdown(self.draft, self.identity)

    def test_pdf_export_rejects_overflow_without_final_file(self):
        odt = self.root / 'letter.odt'
        final = self.root / 'letter.pdf'
        odt.write_bytes(b'synthetic odt')

        def convert(command, **kwargs):
            Path(command[command.index('--outdir') + 1], 'letter.pdf').write_bytes(
                b'%PDF-1.4\n1 0 obj <</Type /Page>>\n2 0 obj <</Type /Page>>\n')
            return type('Result', (), {'returncode': 0})()

        with patch.object(cl.shutil, 'which', return_value='/usr/bin/true'), patch.object(cl.subprocess, 'run', side_effect=convert):
            with self.assertRaisesRegex(ValueError, '2 pages'):
                cl.export_pdf(odt, final)
        self.assertFalse(final.exists())

    def test_pdf_export_publishes_one_page_only(self):
        odt = self.root / 'letter.odt'
        final = self.root / 'letter.pdf'
        odt.write_bytes(b'synthetic odt')

        def convert(command, **kwargs):
            Path(command[command.index('--outdir') + 1], 'letter.pdf').write_bytes(
                b'%PDF-1.4\n1 0 obj <</Type /Page>>\n')
            return type('Result', (), {'returncode': 0})()

        with patch.object(cl.shutil, 'which', return_value='/usr/bin/true'), patch.object(cl.subprocess, 'run', side_effect=convert):
            self.assertEqual(cl.export_pdf(odt, final), 1)
        self.assertTrue(final.exists())
