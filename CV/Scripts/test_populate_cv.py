"""Regression tests for the .ott population workflow (populate_cv.py).

Structural tests run against a synthetic token/bookmark template; an
integration test activates when the delivered Test CV Template.odt is present.
"""
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile
from xml.dom import minidom as D

import cv
import populate_cv as pop

ROOT = Path(__file__).resolve().parents[1]
TEST_MASTER = ROOT / 'Templates/Test CV Template.odt'

NAMESPACES = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"')


def content_xml(taglines_split=False, identity_token=None):
    taglines_token = ('<text:span>{{TAG</text:span><text:span>LINES}}</text:span>'
                      if taglines_split else '{{TAGLINES}}')
    identity = identity_token or 'Test Name'
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {NAMESPACES} office:version="1.2">
 <office:automatic-styles>
  <style:style style:name="Brk" style:family="paragraph">
   <style:paragraph-properties fo:break-before="page"/>
  </style:style>
 </office:automatic-styles>
 <office:body><office:text>
  <text:p text:style-name="P1">{identity}</text:p>
  <text:p text:style-name="P2">{taglines_token}<text:bookmark text:name="TAGLINES"/></text:p>
  <text:p text:style-name="P3"><text:bookmark text:name="PROFILE_CONTENT"/>{{{{PROFILE_PARAGRAPHS}}}}</text:p>
  <text:p text:style-name="PT">{{{{EXPERTISE_1_TITLE}}}}<text:bookmark text:name="EXPERTISE_1_TITLE"/></text:p>
  <text:list text:style-name="L1"><text:list-item><text:p text:style-name="PB"><text:bookmark text:name="EXPERTISE_1_BULLETS"/>{{{{EXPERTISE_1_BULLET}}}}</text:p></text:list-item></text:list>
  <text:p text:style-name="PT">{{{{EXPERTISE_2_TITLE}}}}<text:bookmark text:name="EXPERTISE_2_TITLE"/></text:p>
  <text:list text:style-name="L1"><text:list-item><text:p text:style-name="PB"><text:bookmark text:name="EXPERTISE_2_BULLETS"/>{{{{EXPERTISE_2_BULLET}}}}</text:p></text:list-item></text:list>
  <text:p text:style-name="RH">{{{{ROLE_FIRST_COMPANY}}}}<text:tab/>{{{{ROLE_FIRST_TITLE}}}} {{{{ROLE_FIRST_DATES}}}}<text:bookmark text:name="ROLE_FIRST_START"/></text:p>
  <text:p text:style-name="RL">{{{{ROLE_FIRST_LOCATION}}}}<text:bookmark text:name="ROLE_FIRST_LOCATION"/></text:p>
  <text:list text:style-name="L2"><text:list-item><text:p text:style-name="PB"><text:bookmark text:name="ROLE_FIRST_BULLETS"/>{{{{ROLE_FIRST_BULLET}}}}</text:p></text:list-item></text:list>
  <text:p text:style-name="RH">{{{{ROLE_REPEAT_COMPANY}}}}<text:tab/>{{{{ROLE_REPEAT_TITLE}}}} {{{{ROLE_REPEAT_DATES}}}}<text:bookmark text:name="ROLE_REPEAT_START"/></text:p>
  <text:p text:style-name="RL">{{{{ROLE_REPEAT_LOCATION}}}}<text:bookmark text:name="ROLE_REPEAT_LOCATION"/></text:p>
  <text:list text:style-name="L2"><text:list-item><text:p text:style-name="PB"><text:bookmark text:name="ROLE_REPEAT_BULLETS"/>{{{{ROLE_REPEAT_BULLET}}}}</text:p></text:list-item></text:list>
  <text:p text:style-name="Brk"><text:bookmark text:name="EDUCATION_PAGE_BREAK"/></text:p>
  <text:h text:style-name="H">EDUCATION</text:h>
  <text:p text:style-name="PC">Permanent education content.</text:p>
 </office:text></office:body>
</office:document-content>'''


def manifest_xml():
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            f'<manifest:manifest {NAMESPACES} manifest:version="1.2">'
            '<manifest:file-entry manifest:full-path="/" '
            'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
            '<manifest:file-entry manifest:full-path="content.xml" '
            'manifest:media-type="text/xml"/>'
            '</manifest:manifest>')


def make_template(path, **kwargs):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text',
                   compress_type=zipfile.ZIP_STORED)
        z.writestr('content.xml', content_xml(**kwargs))
        z.writestr('META-INF/manifest.xml', manifest_xml())
    return path


BODY_3_ROLES = '''---
taglines:
  - "Sample Leadership"
  - "Sample Platforms"
---

# Profile

First sample profile paragraph with enough words to stand alone as a complete thought.

Second sample profile paragraph with enough words to stand alone as a complete thought here.

# Expertise and Achievements

## Delivery Leadership

- Sample delivery achievement with several concrete words of supporting evidence included.
- Sample automation achievement with several concrete words of supporting evidence included.
- Sample governance achievement with several concrete words of supporting evidence included.

## Technology and Platforms

- Sample platform achievement with several concrete words of supporting evidence included.
- Sample cloud achievement with several concrete words of supporting evidence included.
- Sample quality achievement with several concrete words of supporting evidence included.

# Work Experience

## Role 01

Company: Example Company A GmbH
Title: Senior Director
Dates: Sep 2019 - Oct 2024
Location: Sample City, Country

- Sample achievement for the first role with several concrete words of evidence included.

## Role 02

Company: Example Company B GmbH
Title: Head of Engineering
Dates: Jan 2014 - Aug 2019
Location: Sample City, Country

- Sample achievement for the second role with several concrete words of evidence included.

## Role 03

Company: Example Company C GmbH
Title: Software Engineer
Dates: Mar 2000 - Jul 2008
Location: Other City, Country

- Sample achievement for the third role with several concrete words of evidence included.
'''


def body_text(odt_path):
    doc = D.parseString(zipfile.ZipFile(odt_path).read('content.xml'))
    parts = []
    def walk(node):
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                if child.tagName == 'text:tab':
                    parts.append('\t')
                elif child.tagName == 'text:line-break':
                    parts.append('\n')
                elif child.tagName == 'text:s':
                    parts.append(' ' * int(child.getAttribute('text:c') or 1))
                else:
                    walk(child)
            elif child.nodeType == child.TEXT_NODE:
                parts.append(child.data)
    walk(doc.getElementsByTagName('office:text')[0])
    return ''.join(parts)


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.temp = Path(self.tmp.name)
        self.master = make_template(self.temp / 'master.odt', taglines_split=True)
        self.body = self.temp / 'body.md'
        self.body.write_text(BODY_3_ROLES, encoding='utf-8')
        self.output = self.temp / 'out.odt'

    def populate(self, **kwargs):
        pop.populate(self.body, self.master, self.output, **kwargs)
        return self.output

    def test_all_sections_populated_and_tokens_gone(self):
        self.populate()
        text = body_text(self.output)
        self.assertNotIn('{{', text)
        self.assertNotIn('ROLE_REPEAT', text)
        self.assertIn('Sample Leadership | Sample Platforms', text)
        self.assertEqual(text.count('First sample profile'), 1)
        self.assertEqual(text.count('Second sample profile'), 1)
        self.assertEqual(text.count('Example Company A GmbH'), 1)
        self.assertEqual(text.count('Example Company B GmbH'), 1)
        self.assertEqual(text.count('Example Company C GmbH'), 1)
        self.assertIn('Permanent education content.', text)

    def test_split_token_across_style_runs_replaced(self):
        self.populate()
        text = body_text(self.output)
        self.assertIn('Sample Leadership | Sample Platforms', text)

    def test_role_order_and_repeat_cloning(self):
        self.populate()
        text = body_text(self.output)
        self.assertLess(text.index('Example Company A'), text.index('Example Company B'))
        self.assertLess(text.index('Example Company B'), text.index('Example Company C'))
        doc = D.parseString(zipfile.ZipFile(self.output).read('content.xml'))
        lists = [element for element in doc.getElementsByTagName('text:list')
                 if element.getAttribute('text:style-name') == 'L2']
        self.assertEqual([len(element.getElementsByTagName('text:list-item'))
                          for element in lists], [1, 1, 1])

    def test_user_owned_content_untouched(self):
        self.populate()
        text = body_text(self.output)
        self.assertIn('Test Name', text)
        self.assertIn('Permanent education content.', text)

    def test_single_role_removes_repeat_prototype(self):
        body = BODY_3_ROLES.split('## Role 02')[0]
        self.body.write_text(body, encoding='utf-8')
        self.populate()
        text = body_text(self.output)
        self.assertNotIn('ROLE_REPEAT', text)
        self.assertIn('Example Company A GmbH', text)
        self.assertNotIn('Example Company B GmbH', text)

    def test_suppress_education_break(self):
        self.populate(education_break='suppress')
        doc = D.parseString(zipfile.ZipFile(self.output).read('content.xml'))
        bookmark = next(element for tag in pop.BOOKMARK_TAGS
                        for element in doc.getElementsByTagName(tag)
                        if element.getAttribute('text:name') == 'EDUCATION_PAGE_BREAK')
        style_name = bookmark.parentNode.getAttribute('text:style-name')
        self.assertNotEqual(style_name, 'Brk')
        automatic = doc.getElementsByTagName('office:automatic-styles')[0]
        style = next(element for element in automatic.getElementsByTagName('style:style')
                     if element.getAttribute('style:name') == style_name)
        properties = style.getElementsByTagName('style:paragraph-properties')[0]
        self.assertFalse(properties.hasAttribute('fo:break-before'))

    def test_master_and_ott_untouched(self):
        before = self.master.read_bytes()
        self.populate()
        self.assertEqual(self.master.read_bytes(), before)

    def test_identity_tokens_rejected(self):
        personalised = make_template(self.temp / 'unpersonalised.odt',
                                     identity_token='{{EMAIL}}')
        with self.assertRaisesRegex(ValueError, 'not personalised'):
            pop.populate(self.body, personalised, self.output)

    def test_unknown_frontmatter_rejected(self):
        self.body.write_text(BODY_3_ROLES.replace(
            'taglines:\n  - "Sample Leadership"\n  - "Sample Platforms"\n',
            'email: "test@example.com"\n'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unknown front-matter key'):
            pop.populate(self.body, self.master, self.output)

    def test_inline_markdown_rejected(self):
        self.body.write_text(BODY_3_ROLES.replace('First sample profile',
                                                  '**First sample profile'),
                             encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Inline Markdown'):
            pop.populate(self.body, self.master, self.output)

    def test_duplicate_section_rejected(self):
        self.body.write_text(BODY_3_ROLES + '\n# Profile\n\nAnother paragraph.\n',
                             encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate section'):
            pop.populate(self.body, self.master, self.output)

    def test_nonconsecutive_roles_rejected(self):
        self.body.write_text(BODY_3_ROLES.replace('## Role 03', '## Role 04'),
                             encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'consecutively'):
            pop.populate(self.body, self.master, self.output)

    def test_missing_role_field_rejected(self):
        self.body.write_text(BODY_3_ROLES.replace('Dates: Mar 2000 - Jul 2008\n', ''),
                             encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing fields'):
            pop.populate(self.body, self.master, self.output)


class TaglineTests(unittest.TestCase):
    def test_packs_at_tag_boundaries_within_limit(self):
        tags = ['Engineering Leadership', 'Data Processing & Scientific Instruments',
                'Operational Software']
        self.assertEqual(pop.pack_taglines(tags),
                         ['Engineering Leadership', 'Data Processing & Scientific Instruments',
                          'Operational Software'])
        for line in pop.pack_taglines(tags):
            self.assertLessEqual(len(line), pop.TAGLINE_LINE_LIMIT)

    def test_short_tags_share_one_line(self):
        self.assertEqual(pop.pack_taglines(['Short one', 'Short two']),
                         ['Short one | Short two'])

    def test_tags_are_never_split_or_reworded(self):
        tags = ['Alpha Beta Gamma Delta Epsilon Zeta Eta Theta', 'Second tag here']
        lines = pop.pack_taglines(tags)
        self.assertIn(tags[0], lines)
        self.assertIn(tags[1], lines)

    def test_oversized_single_tag_reported(self):
        long_tag = 'X' * 60
        self.assertEqual(pop.pack_taglines([long_tag]), [long_tag])
        population = pop.parse_markdown
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        body = Path(tmp.name) / 'body.md'
        body.write_text(BODY_3_ROLES.replace(
            '  - "Sample Leadership"\n  - "Sample Platforms"',
            f'  - "{long_tag}"\n  - "Sample Platforms"'), encoding='utf-8')
        _, warnings = population(body)
        self.assertTrue(any('Tagline line is 60 characters' in w for w in warnings))

    def test_tagline_line_breaks_in_odt(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        temp = Path(tmp.name)
        master = make_template(temp / 'master.odt')
        body = temp / 'body.md'
        body.write_text(BODY_3_ROLES.replace(
            '  - "Sample Leadership"\n  - "Sample Platforms"',
            '  - "Engineering Leadership"\n'
            '  - "Data Processing & Scientific Instruments"\n'
            '  - "Operational Software"'), encoding='utf-8')
        output = temp / 'out.odt'
        pop.populate(body, master, output)
        doc = D.parseString(zipfile.ZipFile(output).read('content.xml'))
        breaks = doc.getElementsByTagName('text:line-break')
        self.assertEqual(len(breaks), 2)
        lines = pop.paragraph_text(next(
            element for element in doc.getElementsByTagName('text:p')
            if element.getAttribute('text:style-name') == 'P2'
            and 'Engineering' in pop.paragraph_text(element))).split('\n')
        self.assertEqual(lines, ['Engineering Leadership',
                                 'Data Processing & Scientific Instruments',
                                 'Operational Software'])



class DeliveredMasterTests(unittest.TestCase):
    def setUp(self):
        if not TEST_MASTER.exists():
            self.skipTest('delivered Test CV Template.odt is not present '
                          '(local personal master, not tracked)')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.temp = Path(self.tmp.name)
        self.body = self.temp / 'body.md'
        self.body.write_text(BODY_3_ROLES, encoding='utf-8')
        self.output = self.temp / 'populated.odt'

    def test_population_against_delivered_master(self):
        before = hashlib.sha256(TEST_MASTER.read_bytes()).hexdigest()
        pop.populate(self.body, TEST_MASTER, self.output)
        text = body_text(self.output)
        self.assertNotIn('{{', text)
        for company in ('Example Company A GmbH', 'Example Company B GmbH',
                        'Example Company C GmbH'):
            self.assertIn(company, text)
        for probe in ('TEST NAME', 'test@testing.com', '+49234567890', 'An Island',  # privacy-screen: allow
                      '1st Class Honours, School of life', 'Klingon, mostly',
                      'Beer and Bicycles'):
            self.assertIn(probe, text)
        with zipfile.ZipFile(self.output) as z:
            self.assertNotIn('Thumbnails/thumbnail.png', z.namelist())
            self.assertNotIn(cv.MAP, z.namelist())
        self.assertEqual(hashlib.sha256(TEST_MASTER.read_bytes()).hexdigest(), before)


if __name__ == '__main__':
    unittest.main()
