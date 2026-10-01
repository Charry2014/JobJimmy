"""Synthetic send-file copy checks; never read private documents."""
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prepare_send_files as psf

NAME = 'Synthetic Candidate'
CV_BYTES = b'%PDF-1.4 synthetic cv'


class PrepareSendFilesTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / 'workspace'
        self.cv_dir = self.root / 'JobSearch/Applications/2026-08-example-role/CV'
        self.cv_dir.mkdir(parents=True)
        self.identity = self.root / 'JobSearch/Templates/letter-identity.json'
        self.identity.parent.mkdir(parents=True)
        self.identity.write_text(json.dumps({
            'Sender': [NAME, 'Example Street'],
            'Signature': [NAME, '+00 000 0000000', 'user@example.com'],
        }))
        self.cv = self.cv_dir / '2026-08-example-cv.pdf'
        self.letter = self.cv_dir / '2026-08-example-cover-letter.pdf'
        self.cv.write_bytes(CV_BYTES)
        self.letter.write_bytes(CV_BYTES + b' letter')

    def plan(self):
        return psf.plan(self.identity, [(self.cv, 'CV'), (self.letter, 'Cover Letter')],
                        root=self.root)

    def test_creates_named_copies_and_preserves_sources(self):
        before = {path: psf.sha256(path) for path in (self.cv, self.letter)}
        created = psf.create(self.plan())
        self.assertEqual([p.name for p in created],
                         [f'{NAME} - CV.pdf', f'{NAME} - Cover Letter.pdf'])
        for source, copy in zip((self.cv, self.letter), created):
            self.assertEqual(copy.read_bytes(), source.read_bytes())
            self.assertEqual(psf.sha256(source), before[source])
        self.assertTrue(self.cv.is_file() and self.letter.is_file())

    def test_refuses_to_overwrite_an_existing_copy(self):
        (self.cv_dir / f'{NAME} - CV.pdf').write_bytes(b'%PDF-1.4 stale')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.plan()

    def test_rejects_unsafe_or_missing_identity_name(self):
        fields = json.loads(self.identity.read_text())
        fields['Signature'][0] = 'Bad/Name'
        self.identity.write_text(json.dumps(fields))
        with self.assertRaisesRegex(ValueError, 'not a safe filename'):
            psf.display_name(self.identity)
        with self.assertRaisesRegex(ValueError, 'Cannot read local identity'):
            psf.display_name(self.root / 'missing.json')

    def test_rejects_missing_or_non_pdf_source(self):
        missing = self.cv_dir / 'absent.pdf'
        with self.assertRaisesRegex(ValueError, 'missing'):
            psf.plan(self.identity, [(missing, 'CV')], root=self.root)
        not_pdf = self.cv_dir / 'source.odt'
        not_pdf.write_bytes(b'not a pdf')
        with self.assertRaisesRegex(ValueError, 'PDF'):
            psf.plan(self.identity, [(not_pdf, 'CV')], root=self.root)

    def test_rolls_back_all_copies_when_a_copy_fails(self):
        planned = self.plan()
        real_copyfile = psf.shutil.copyfile
        calls = {'n': 0}

        def flaky(source, destination):
            calls['n'] += 1
            if calls['n'] == 2:
                raise OSError('synthetic failure')
            return real_copyfile(source, destination)

        with patch.object(psf.shutil, 'copyfile', flaky), self.assertRaises(OSError):
            psf.create(planned)
        self.assertEqual(list(self.cv_dir.glob(f'{NAME} - *.pdf')), [])

    def test_cli_reports_only_generic_status(self):
        args = ['prepare_send_files.py', '--identity', str(self.identity),
                '--cv', str(self.cv), '--cover-letter', str(self.letter)]
        output = io.StringIO()
        with patch('sys.argv', args), patch.object(psf, 'check_output'), redirect_stdout(output):
            psf.main()
        printed = output.getvalue()
        self.assertIn('verified', printed)
        for secret in (NAME, 'Synthetic', str(self.cv_dir)):
            self.assertNotIn(secret, printed)
        self.assertTrue((self.cv_dir / f'{NAME} - CV.pdf').is_file())

    def test_cli_requires_a_source(self):
        with patch('sys.argv', ['prepare_send_files.py']), redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit):
            psf.main()


if __name__ == '__main__':
    unittest.main()
