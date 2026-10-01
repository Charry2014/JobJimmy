"""Regression checks for actual Markdown edits, data-loss guards, and ODT round trips.

Tests activate automatically once a reference/template pair exists in
CV/References and CV/Templates (generated with `cv.py extract`); otherwise they
are skipped, so an empty template checkout still passes the suite.
"""
import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile
from xml.dom import minidom as D
import cv

ROOT = Path(__file__).resolve().parents[1]


def discover_pairs():
    pairs = {}
    templates, references = ROOT / 'Templates', ROOT / 'References'
    if not (templates.is_dir() and references.is_dir()):
        return pairs
    for template in sorted(templates.glob('*.odt')):
        try:
            with zipfile.ZipFile(template) as z:
                mapping = json.loads(z.read(cv.MAP))
        except (KeyError, zipfile.BadZipFile, OSError):
            continue
        variant = mapping.get('variant')
        reference = references / f'{variant}.md'
        if variant and reference.exists():
            pairs[variant] = (reference, template)
    return pairs


PAIRS = discover_pairs()


def page_break_paragraphs(odt_path, inside_list_items=None):
    """Paragraphs whose style carries an explicit page break.

    With inside_list_items=True/False, restrict to paragraphs whose parent is
    (or is not) a text:list-item. Layout-only breaks after bullet lists sit
    inside the final bullet's list item; section headings carry their own
    break-before styles.
    """
    with zipfile.ZipFile(odt_path) as z:
        names = set()
        for xml_name in ('styles.xml', 'content.xml'):
            doc = D.parseString(z.read(xml_name))
            for style in doc.getElementsByTagName('style:style'):
                if style.getAttribute('style:family') != 'paragraph':
                    continue
                for props in style.getElementsByTagName('style:paragraph-properties'):
                    for attr in (props.getAttribute('fo:break-before'),
                                 props.getAttribute('fo:break-after')):
                        if 'page' in attr:
                            names.add(style.getAttribute('style:name'))
        doc = D.parseString(z.read('content.xml'))
        result = []
        for paragraph in cv.paragraphs(doc):
            if paragraph.getAttribute('text:style-name') not in names:
                continue
            if inside_list_items is not None and \
                    (paragraph.parentNode.tagName == 'text:list-item') != inside_list_items:
                continue
            result.append(paragraph)
        return result


@unittest.skipIf(not PAIRS, 'No reference/template pairs; run cv.py extract first')
class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.temp = Path(self.tmp.name)
        self.variant, (self.reference, self.template) = sorted(PAIRS.items())[0]
        with zipfile.ZipFile(self.template) as z:
            self.mapping = json.loads(z.read(cv.MAP))

    def render_text(self, text, template=None):
        md = self.temp / 'edited.md'
        out = self.temp / 'edited.odt'
        md.write_text(text)
        values = cv.render(md, template or self.template, out)
        with zipfile.ZipFile(out) as z:
            self.assertNotIn(b'{{CV:', z.read('content.xml'))
            self.assertNotIn(cv.MAP, z.namelist())
            doc = D.parseString(z.read('content.xml'))
            actual = [''.join(s for _, s in cv.visible_leaves(p)) for p in cv.paragraphs(doc)]
            expected = []
            for value in values.values():
                expected.extend(value if isinstance(value, list) else [value])
            self.assertEqual([t for t in actual if t.strip()], [t for t in expected if t.strip()])
        return out

    def first_prose_block(self):
        for block in self.mapping['blocks']:
            if block['prefix'] == '' and ''.join(s['text'] for s in block['slots']).strip():
                return block
        self.skipTest('No prose block in this template.')

    def last_bullet_block(self):
        bullets = [b for b in self.mapping['blocks'] if b['prefix'] == '- ']
        if not bullets:
            self.skipTest('No bullet block in this template.')
        return bullets[-1]

    def bullet_block_before_list_page_break(self):
        """The bullet block whose list item contains a layout-only page break."""
        with zipfile.ZipFile(self.template) as z:
            names = set()
            for xml_name in ('styles.xml', 'content.xml'):
                style_doc = D.parseString(z.read(xml_name))
                for style in style_doc.getElementsByTagName('style:style'):
                    if style.getAttribute('style:family') != 'paragraph':
                        continue
                    for props in style.getElementsByTagName('style:paragraph-properties'):
                        for attr in (props.getAttribute('fo:break-before'),
                                     props.getAttribute('fo:break-after')):
                            if 'page' in attr:
                                names.add(style.getAttribute('style:name'))
            doc = D.parseString(z.read('content.xml'))
            paragraphs = cv.paragraphs(doc)
            break_nodes = [p for p in paragraphs
                           if p.getAttribute('text:style-name') in names
                           and p.parentNode.tagName == 'text:list-item']
        for block in reversed([b for b in self.mapping['blocks'] if b['prefix'] == '- ']):
            item = paragraphs[int(block['id'][1:])].parentNode
            if any(p.parentNode is item for p in break_nodes):
                return block
        self.skipTest('No bullet block with a page break inside its list item.')

    def replace_block(self, text, block, new_content):
        pattern = re.compile(r'(<!-- cv:%s -->\n).*?(\n<!-- /cv:%s -->)' % (block['id'], block['id']), re.S)
        if not pattern.search(text):
            self.skipTest('Reference does not contain the expected block markers.')
        body = block['prefix'] + new_content if block['prefix'] != '- ' else new_content
        return pattern.sub(lambda m: m.group(1) + body + m.group(2), text, count=1)

    def test_edited_text_and_whitespace_reach_odt(self):
        block = self.first_prose_block()
        text = self.replace_block(self.reference.read_text(), block,
                                  'Edited wording & characters <platforms><br>Extra line\twith a tab')
        self.render_text(text)

    def test_complete_rewrite_across_existing_styles(self):
        block = self.mapping['blocks'][0]
        text = self.replace_block(self.reference.read_text(), block,
                                  'A completely new focus & direction<br>Second line')
        self.render_text(text)

    def test_empty_paragraph_supported(self):
        block = self.first_prose_block()
        text = self.replace_block(self.reference.read_text(), block, '')
        self.render_text(text)

    def test_missing_block_rejected(self):
        text = re.sub(r'<!-- cv:\w+ -->.*?<!-- /cv:\w+ -->', '',
                      self.reference.read_text(), count=1, flags=re.S)
        with self.assertRaisesRegex(ValueError, 'blocks'):
            self.render_text(text)

    def test_duplicate_block_rejected(self):
        text = self.reference.read_text()
        text += cv.BLOCK.search(text)[0]
        with self.assertRaisesRegex(ValueError, 'blocks'):
            self.render_text(text)

    def test_unmapped_text_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside CV blocks'):
            self.render_text(self.reference.read_text() + '\nThis must not be silently discarded.\n')

    def test_wrong_variant_rejected(self):
        if len(PAIRS) < 2:
            self.skipTest('Needs a second reference/template pair.')
        other_variant = next(v for v in sorted(PAIRS) if v != self.variant)
        with self.assertRaisesRegex(ValueError, 'blocks'):
            self.render_text(self.reference.read_text(), PAIRS[other_variant][1])

    def test_add_bullets_within_existing_section(self):
        block = self.last_bullet_block()
        text = self.reference.read_text().replace(f"<!-- /cv:{block['id']} -->",
            '- Additional distinct achievement & evidence.\n- Another point.<br>With a second line.\n'
            f'<!-- /cv:{block['id']} -->')
        self.render_text(text)

    def test_remove_bullet_without_removing_section(self):
        block = self.last_bullet_block()
        text = self.replace_block(self.reference.read_text(), block, '')
        self.render_text(text)

    def test_invalid_bullet_line_rejected(self):
        block = self.last_bullet_block()
        text = self.reference.read_text().replace(f"<!-- /cv:{block['id']} -->",
            f'Unmarked second bullet\n<!-- /cv:{block['id']} -->')
        with self.assertRaisesRegex(ValueError, 'Each bullet'):
            self.render_text(text)

    def test_added_bullet_stays_before_explicit_page_break(self):
        block = self.bullet_block_before_list_page_break()
        break_count = len(page_break_paragraphs(self.template, inside_list_items=True))
        text = self.reference.read_text().replace(f"<!-- /cv:{block['id']} -->",
            '- Additional closing evidence for this section.\n'
            f'<!-- /cv:{block['id']} -->')
        out = self.render_text(text)
        remaining = page_break_paragraphs(out, inside_list_items=True)
        self.assertEqual(len(remaining), break_count)
        anchor = remaining[-1]
        texts = [''.join(t for _, t in cv.visible_leaves(c)).strip()
                 for c in anchor.parentNode.childNodes if c.nodeType == c.ELEMENT_NODE]
        self.assertIn('Additional closing evidence for this section.', texts)

    def test_remove_bullet_keeps_explicit_page_break(self):
        block = self.bullet_block_before_list_page_break()
        break_count = len(page_break_paragraphs(self.template, inside_list_items=True))
        text = self.replace_block(self.reference.read_text(), block, '')
        out = self.render_text(text)
        self.assertEqual(len(page_break_paragraphs(out, inside_list_items=True)), break_count)

    def test_source_protected(self):
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            cv.render(self.reference, self.template, self.template)


if __name__ == '__main__':
    unittest.main()
