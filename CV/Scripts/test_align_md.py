"""Regression tests for plain-Markdown alignment onto cv:pNNN block markers."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import align_md
import cv


def synthetic_template(path, blocks):
    mapping = {'schema': 1, 'variant': 'test', 'source_name': 'synthetic.odt',
               'blocks': blocks}
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('cv-template.json', json.dumps(mapping))
    return mapping


def block(block_id, prefix, text):
    return {'id': block_id, 'prefix': prefix, 'leading': '', 'trailing': '',
            'slots': [{'text': text, 'xml': None}]}


class TextHelpers(unittest.TestCase):
    def test_norm_and_similar(self):
        self.assertEqual(align_md.norm('**Data processing & architecture:**'), 'data processing and architecture')
        self.assertEqual(align_md.similar('PROFILE', 'Profile'), 1.0)
        self.assertGreater(align_md.similar('Engineering Leadership', 'Engineering and Department Leadership'), 0.4)
        self.assertLess(align_md.similar('Tagline', 'WORK  EXPERIENCE'), 0.3)

    def test_strip_markdown_links_and_emphasis(self):
        self.assertEqual(align_md.strip_md('**[Source](https://x.test)**'), 'Source')
        self.assertEqual(align_md.strip_md('A `code` value'), 'A code value')


class ParseSource(unittest.TestCase):
    def test_paragraphs_bullets_and_runs(self):
        units = align_md.parse_source(
            '# Name\n\n## Skills\n\n- one\n- two\n\nPlain paragraph.\n')
        self.assertEqual(units[0], ['h1', 'Name'])
        self.assertEqual(units[1], ['h2', 'Skills'])
        self.assertEqual(units[2], ['bullets', ['one', 'two']])
        self.assertEqual(units[3], ['para', 'Plain paragraph.'])

    def test_hard_break_splits_paragraphs(self):
        units = align_md.parse_source('Line one  \nLine two\n')
        self.assertEqual(units, [['para', 'Line one'], ['para', 'Line two']])

    def test_employer_header_folding(self):
        units = align_md.parse_source(
            '### Acme GmbH\n\nHead of Software | January 2020 – March 2024  \nSample City\n\n- Led the team.\n')
        self.assertEqual(units[0], ['h3', 'Acme GmbH\tHead of Software\tJanuary 2020 – March 2024'])
        self.assertEqual(units[1], ['para', 'Sample City'])
        self.assertEqual(units[2], ['bullets', ['Led the team.']])

    def test_location_does_not_fold_into_employer_without_blank_line(self):
        source = '### Sample Organisation\nLead | January 2020 – March 2024\nSample City\n\n- Led the team.\n'
        units = align_md.parse_source(source)
        self.assertEqual(units[0], ['h3', 'Sample Organisation\tLead\tJanuary 2020 – March 2024'])
        self.assertEqual(units[1], ['para', 'Sample City'])
        self.assertEqual(units[2], ['bullets', ['Led the team.']])

        blocks = [block('p024', '### ', 'Sample Organisation\tLead\tJanuary 2020 – March 2024'),
                  block('p025', '', 'Sample City'), block('p026', '- ', 'Led the team.')]
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / 'synthetic.odt'
            mapping = synthetic_template(template, blocks)
            _, tunits = align_md.load_template(template)
            pairs, dropped, fallback = align_md.align(tunits, units)
            markdown, report = align_md.build_markdown(mapping, tunits, units, pairs, dropped, fallback)
            self.assertEqual(report['dropped_source'], [])
            self.assertEqual(report['fallback_blocks'], [])
            self.assertIn('### Sample Organisation\tLead\tJanuary 2020 – March 2024', markdown)
            self.assertIn('<!-- cv:p025 -->\nSample City\n', markdown)

            without_location = align_md.parse_source(
                '### Sample Organisation\nLead | January 2020 – March 2024\n\n- Led the team.\n')
            pairs, dropped, fallback = align_md.align(tunits, without_location)
            markdown, report = align_md.build_markdown(mapping, tunits, without_location,
                                                       pairs, dropped, fallback)
            self.assertEqual(report['dropped_source'], [])
            self.assertEqual(report['fallback_blocks'], ['p025'])
            self.assertIn('<!-- cv:p025 -->\nSample City\n', markdown)


class Distribute(unittest.TestCase):
    def test_extra_bullets_join_earlier_blocks(self):
        result = align_md.distribute(['p1', 'p2', 'p3'], ['a', 'b', 'c', 'd'])
        self.assertEqual(result, {'p1': ['a', 'b'], 'p2': ['c'], 'p3': ['d']})

    def test_fewer_bullets_leave_blocks_empty(self):
        result = align_md.distribute(['p1', 'p2', 'p3', 'p4'], ['a', 'b', 'c'])
        self.assertEqual(result, {'p1': ['a'], 'p2': ['b'], 'p3': ['c'], 'p4': []})


class EndToEnd(unittest.TestCase):
    def test_alignment_maps_variable_counts(self):
        blocks = [
            block('p000', '# ', 'JANE DOE'),
            block('p001', '', 'Reference positioning\nsecond line'),
            block('p002', '## ', 'PROFILE'),
            block('p003', '', 'Profile baseline.'),
            block('p004', '', 'Language A & Language B'),
            block('p005', '## ', 'SKILLS'),
            block('p006', '- ', 'Reference skill one'),
            block('p007', '- ', 'Reference skill two'),
        ]
        source = (
            '# Jane Doe — CV for ACME\n\n'
            '## Tagline\n'
            'Positioning line one\n\n'
            'Positioning line two\n\n'
            '## Profile\n'
            'Draft profile paragraph.\n\n'
            '## Skills\n'
            '- alpha\n- beta\n- gamma\n\n'
            '## Appendix guidance\n'
            'Do not include this note.\n')
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / 'synthetic.odt'
            mapping = synthetic_template(template, blocks)
            output = Path(tmp) / 'out.md'
            sunits = align_md.parse_source(source)
            _, tunits = align_md.load_template(template)
            pairs, dropped, fallback = align_md.align(tunits, sunits)
            markdown, report = align_md.build_markdown(mapping, tunits, sunits, pairs, dropped, fallback)

            # The intermediate loads in the real renderer unchanged.
            output.write_text(markdown, encoding='utf-8')
            values = cv.read_markdown(output, mapping)
            self.assertEqual(values['p000'], 'Jane Doe')
            self.assertEqual(values['p001'], 'Positioning line one\nPositioning line two')
            self.assertEqual(values['p003'], 'Draft profile paragraph.')
            self.assertEqual(values['p004'], 'Language A & Language B')  # baseline fallback
            self.assertEqual(values['p006'], ['alpha', 'beta'])
            self.assertEqual(values['p007'], ['gamma'])
            self.assertIn('Appendix guidance', [item['text'] for item in report['dropped_source']])

            order = [b['id'] for b in mapping['blocks']]
            positions = [markdown.index(f'<!-- cv:{bid} -->') for bid in order]
            self.assertEqual(positions, sorted(positions))


if __name__ == '__main__':
    unittest.main()
