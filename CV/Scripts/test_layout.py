"""Exercise PDF layout acceptance and rejection with controlled page geometry."""
from pathlib import Path
import tempfile
import unittest
try:
    import pymupdf as pdf
    import check_layout
except ImportError:
    pdf = None


def sample_config():
    return {1: ['PROFILE', 'EXPERTISE & ACHIEVEMENTS'],
            2: ['WORK EXPERIENCE', 'Example Company A GmbH', 'Example Company B GmbH'],
            3: ['Example Company C GmbH', 'Example Company D GmbH',
                'EDUCATION', 'LANGUAGES', 'SPORTS & HOBBIES']}


@unittest.skipIf(pdf is None, 'Optional PyMuPDF dependency unavailable')
class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.expected = sample_config()

    def sample(self, bottom=790, wrong_page=False, fourth=False):
        groups = [list(self.expected[1]), list(self.expected[2]), list(self.expected[3])]
        if wrong_page:
            groups[2].insert(0, groups[1].pop())
        with pdf.open() as doc:
            for group in groups:
                p = doc.new_page(width=595, height=842)
                for n, line in enumerate(group):
                    p.insert_text((45, 55+n*20), line, fontsize=10)
                p.insert_text((45, bottom), 'Distinct final evidence.', fontsize=10)
            if fourth:
                doc.new_page()
            dest = Path(self.tmp.name)/'check.pdf'
            doc.save(dest)
        return check_layout.check(dest, self.expected, line_height_pt=12)

    def test_balanced_three_pages_pass(self):
        self.assertTrue(self.sample()['passed'])

    def test_excessive_bottom_space_fails(self):
        self.assertFalse(self.sample(bottom=680)['passed'])

    def test_heading_spilling_onto_third_page_fails(self):
        result = self.sample(wrong_page=True)
        self.assertFalse(result['passed'])
        self.assertTrue(any('Example Company B' in s for s in result['errors']))

    def test_four_pages_fail(self):
        self.assertFalse(self.sample(fourth=True)['passed'])

    def test_bottom_margin_overflow_fails(self):
        self.assertFalse(self.sample(bottom=825)['passed'])

    def test_config_validation(self):
        good = Path(self.tmp.name) / 'good.json'
        good.write_text('{"pages": {"1": ["A"], "2": ["B"]}}', encoding='utf-8')
        self.assertEqual(check_layout.load_config(good), {1: ['A'], 2: ['B']})
        for bad in ('{"pages": {}}', '{"pages": {"1": []}}', '{"pages": {"one": ["A"]}}',
                    '{"pages": {"1": [""]}}', '{"missing": true}', '{}'):
            path = Path(self.tmp.name) / 'bad.json'
            path.write_text(bad, encoding='utf-8')
            with self.assertRaises(ValueError):
                check_layout.load_config(path)


if __name__ == '__main__':
    unittest.main()
