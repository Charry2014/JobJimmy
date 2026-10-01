#!/usr/bin/env python3
"""Lossless ODT extraction and CV rendering with variable bullet counts.

Python standard library only. Run --help for commands. Application-specific
Markdown and generated outputs should be passed from the relevant
JobSearch/Applications/<application-slug>/CV/ directory; shared references and templates
remain under CV/.
"""
import argparse
import bisect
import difflib
import hashlib
import json
from pathlib import Path
from output_paths import check_output
import re
import sys
import zipfile
from xml.dom import minidom as D
import xml.etree.ElementTree as ET

TEXT_NS = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
SCHEMA = 1
MAP = 'cv-template.json'
BLOCK = re.compile(r'<!-- cv:(p\d+) -->\n(.*?)\n<!-- /cv:\1 -->', re.S)
TOKEN = re.compile(r'\{\{CV:(p\d+):(\d+)\}\}')

# Paragraph titles treated as level-3 headings during extraction, in addition
# to tab-aligned employer/date lines. Edit for a new source document, or use
# Writer heading styles (text:h) in the source instead.
H3_SUBHEADINGS = ('Executive Impact', 'Engineering Leadership', 'Technology Expertise')
YEAR = re.compile(r'\b(19|20)\d\d\b')


def visible_leaves(node):
    """Text content only: skip graphics/alt text, annotations and tracked deletions."""
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            yield child, child.data
        elif child.nodeType == child.ELEMENT_NODE:
            tag = child.tagName
            if tag.startswith(('draw:', 'svg:')) or tag in ('office:annotation', 'text:tracked-changes'):
                continue
            if tag == 'text:s':
                yield child, ' ' * int(child.getAttribute('text:c') or '1')
            elif tag == 'text:tab':
                yield child, '\t'
            elif tag == 'text:line-break':
                yield child, '\n'
            else:
                yield from visible_leaves(child)


def paragraphs(doc):
    body = doc.getElementsByTagName('office:text')[0]
    return [e for e in body.getElementsByTagName('*') if e.tagName in ('text:p', 'text:h')]


def prefix_for(p, index, text):
    if index == 0:
        return '# '
    if p.tagName == 'text:h':
        return '## '
    if text in H3_SUBHEADINGS:
        return '### '
    if p.parentNode.tagName == 'text:list-item':
        return '- '
    if '\t' in text and YEAR.search(text):
        # Tab-aligned employer/role/date line, matching the supplied sources.
        return '### '
    return ''


def pack(source, output, replacements, excluded=()):
    output = check_output(output, source)
    if output.resolve() == Path(source).resolve():
        raise ValueError('Output must not overwrite the source/template.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, 'w') as dst:
        # ODF requires an uncompressed mimetype as the first entry.
        dst.writestr('mimetype', src.read('mimetype'), compress_type=zipfile.ZIP_STORED)
        names = set(src.namelist())
        for item in src.infolist():
            if item.filename == 'mimetype' or item.filename in excluded:
                continue
            dst.writestr(item, replacements.get(item.filename, src.read(item.filename)))
        for name, value in replacements.items():
            if name not in names and name not in excluded:
                dst.writestr(name, value, compress_type=zipfile.ZIP_DEFLATED)


def manifest(data, add_map=False):
    doc = D.parseString(data)
    root = doc.documentElement
    for e in list(doc.getElementsByTagName('manifest:file-entry')):
        if e.getAttribute('manifest:full-path') in (MAP, 'Thumbnails/thumbnail.png'):
            root.removeChild(e)
    if add_map:
        e = doc.createElement('manifest:file-entry')
        e.setAttribute('manifest:full-path', MAP)
        e.setAttribute('manifest:media-type', 'application/json')
        root.appendChild(e)
    return doc.toxml(encoding='UTF-8')


def build(source, markdown, template, variant):
    check_output(markdown, source)
    check_output(template, source)
    with zipfile.ZipFile(source) as z:
        doc = D.parseString(z.read('content.xml'))
        mf = manifest(z.read('META-INF/manifest.xml'), add_map=True)
    mapping = {'schema': SCHEMA, 'variant': variant, 'source_name': Path(source).name,
               'source_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(), 'blocks': []}
    lines = ['---', 'type: cv-reference', f'variant: {variant}',
             f'source_file: {json.dumps(str(Path(source).resolve()))}', '---', '',
             '<!-- Edit text inside cv blocks; preserve IDs, headings and list prefixes.',
             'Use <br> for a line break. Formatting comes from the ODT template. -->', '']
    for i, p in enumerate(paragraphs(doc)):
        leaves = list(visible_leaves(p))
        original = ''.join(s for _, s in leaves)
        clean = original.strip()
        if not clean:
            continue  # retain empty layout paragraphs in the template
        key = f'p{i:03d}'
        prefix = prefix_for(p, i, clean)
        block = {'id': key, 'prefix': prefix, 'leading': original[:len(original)-len(original.lstrip())],
                 'trailing': original[len(original.rstrip()):], 'slots': []}
        for n, (leaf, text) in enumerate(leaves):
            slot = {'text': text, 'xml': leaf.toxml() if leaf.nodeType == leaf.ELEMENT_NODE else None}
            block['slots'].append(slot)
            leaf.parentNode.replaceChild(doc.createTextNode(f'{{{{CV:{key}:{n}}}}}'), leaf)
        mapping['blocks'].append(block)
        lines += [f'<!-- cv:{key} -->', prefix + clean.replace('\n', '<br>'), f'<!-- /cv:{key} -->', '']
    Path(markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(markdown).write_text('\n'.join(lines), encoding='utf-8')
    pack(source, template, {'content.xml': doc.toxml(encoding='UTF-8'),
         MAP: json.dumps(mapping, ensure_ascii=False, indent=2).encode(), 'META-INF/manifest.xml': mf},
         excluded=('Thumbnails/thumbnail.png',))
    return len(mapping['blocks'])


def read_markdown(path, mapping):
    text = Path(path).read_text(encoding='utf-8')
    matches = list(BLOCK.finditer(text))
    ids = [m[1] for m in matches]
    expected = [b['id'] for b in mapping['blocks']]
    if ids != expected:
        raise ValueError('CV blocks must occur exactly once in template order; missing, duplicate or reordered blocks found.')
    remainder = BLOCK.sub('', text)
    if '<!-- cv:' in remainder or '<!-- /cv:' in remainder:
        raise ValueError('Malformed CV block marker.')
    remainder = re.sub(r'\A---\n.*?\n---\n', '', remainder, flags=re.S)
    remainder = re.sub(r'<!--.*?-->', '', remainder, flags=re.S)
    if remainder.strip():
        raise ValueError('Text outside CV blocks would not be rendered; move it inside a block.')
    values = {}
    for m, block in zip(matches, mapping['blocks']):
        content = m[2]
        if block['prefix'] == '- ':
            bullets = [] if not content.strip() else content.splitlines()
            if any(not line.startswith('- ') or not line[2:].strip() for line in bullets):
                raise ValueError(f"Each bullet in {block['id']} must start with '- ' and contain text.")
            values[block['id']] = [block['leading'] + line[2:].replace('<br>', '\n') + block['trailing']
                                   for line in bullets]
            continue
        if not content.startswith(block['prefix']):
            raise ValueError(f"Keep the heading/list prefix for {block['id']}.")
        content = content[len(block['prefix']):]
        if '\n' in content:
            raise ValueError(f"Use <br> for line breaks inside {block['id']}; do not wrap source lines.")
        values[block['id']] = block['leading'] + content.replace('<br>', '\n') + block['trailing']
    return values


def distribute(old_slots, new):
    """Map edits into original style runs; unchanged characters keep their styles."""
    old = ''.join(old_slots)
    starts = []
    pos = 0
    for s in old_slots:
        starts.append(pos)
        pos += len(s)
    result = [''] * len(old_slots)
    def owner(offset):
        return min(len(starts)-1, max(0, bisect.bisect_right(starts, offset)-1))
    for op, a, b, c, d in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if op == 'equal':
            pos = a
            while pos < b:
                slot = owner(pos)
                end = min(b, starts[slot] + len(old_slots[slot]))
                result[slot] += old[pos:end]
                pos = end
        elif op in ('insert', 'replace'):
            result[owner(a)] += new[c:d]
    assert ''.join(result) == new
    return result


def fragment(doc, value):
    """Encode whitespace explicitly so Writer preserves it."""
    result = []
    for s in re.split(r'( +|\t|\n)', value):
        if not s:
            continue
        if s[0] == ' ' or s in ('\t', '\n'):
            tag = 'text:s' if s[0] == ' ' else ('text:tab' if s == '\t' else 'text:line-break')
            e = doc.createElementNS(TEXT_NS, tag)
            if tag == 'text:s' and len(s) > 1:
                e.setAttribute('text:c', str(len(s)))
            result.append(e)
        else:
            result.append(doc.createTextNode(s))
    return result


def render(markdown, template, output):
    check_output(output, markdown, template)
    with zipfile.ZipFile(template) as z:
        mapping = json.loads(z.read(MAP))
        if mapping['schema'] != SCHEMA:
            raise ValueError('Unsupported template schema.')
        doc = D.parseString(z.read('content.xml'))
        mf = manifest(z.read('META-INF/manifest.xml'))
    values = read_markdown(markdown, mapping)
    # Keep anchors before editing: adding/removing bullets shifts paragraph indices.
    original_paragraphs = paragraphs(doc)
    bullet_anchors = {b['id']: original_paragraphs[int(b['id'][1:])]
                      for b in mapping['blocks'] if b['prefix'] == '- '}
    slots = {}
    for block in mapping['blocks']:
        value = values[block['id']]
        if isinstance(value, list):
            value = value[0] if value else ''
        updated = distribute([s['text'] for s in block['slots']], value)
        for i, (source, value) in enumerate(zip(block['slots'], updated)):
            slots[(block['id'], str(i))] = source, value
    nodes = []
    def visit(node):
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE and TOKEN.search(child.data):
                nodes.append(child)
            else:
                visit(child)
    visit(doc)
    used = []
    for node in nodes:
        # Adjacent placeholders may be coalesced into one XML text node.
        parts = re.split(r'(\{\{CV:p\d+:\d+\}\})', node.data)
        for part in parts:
            if not part:
                continue
            match = TOKEN.fullmatch(part)
            if not match:
                raise ValueError('Unexpected literal text mixed with template slots.')
            key = match.groups()
            source, value = slots[key]
            used.append(key)
            if value == source['text']:
                if source['xml']:
                    wrapper = D.parseString('<root xmlns:text="'+TEXT_NS+'">'+source['xml']+'</root>')
                    replacements = [doc.importNode(wrapper.documentElement.firstChild, True)]
                else:
                    replacements = [doc.createTextNode(value)]
            else:
                replacements = fragment(doc, value)
            for replacement in replacements:
                node.parentNode.insertBefore(replacement, node)
        node.parentNode.removeChild(node)
    if len(used) != len(slots) or set(used) != set(slots):
        raise ValueError('Template slots missing or duplicated.')
    for key, p in bullet_anchors.items():
        bullets = values[key]
        item = p.parentNode
        siblings = [c for c in item.childNodes if c.nodeType == c.ELEMENT_NODE and c is not p]
        if item.tagName != 'text:list-item' or any(''.join(t for _, t in visible_leaves(c)).strip() for c in siblings):
            raise ValueError(f'Unsupported compound list item in {key}.')
        if not bullets:
            if siblings:
                item.removeChild(p)  # preserve the existing page-break paragraphs
            else:
                item.parentNode.removeChild(item)
        else:
            previous = item
            for text in bullets[1:]:
                # Inherit list and paragraph styles without duplicating inline IDs,
                # bookmarks, or bold formatting from a specific original phrase.
                new_item = doc.createElementNS(TEXT_NS, 'text:list-item')
                new_p = doc.createElementNS(TEXT_NS, 'text:p')
                if p.hasAttribute('text:style-name'):
                    new_p.setAttribute('text:style-name', p.getAttribute('text:style-name'))
                for node in fragment(doc, text):
                    new_p.appendChild(node)
                new_item.appendChild(new_p)
                previous.parentNode.insertBefore(new_item, previous.nextSibling)
                previous = new_item
            if len(bullets) > 1:
                # Layout-only trailing paragraphs must stay after the final bullet.
                for sibling in siblings:
                    previous.appendChild(sibling)
    pack(template, output, {'content.xml': doc.toxml(encoding='UTF-8'), 'META-INF/manifest.xml': mf},
         excluded=(MAP, 'Thumbnails/thumbnail.png'))
    return values


def signature(element):
    return (element.tag, sorted(element.attrib.items()), element.text or '', element.tail or '',
            [signature(c) for c in element])


def validate(source, rendered):
    with zipfile.ZipFile(source) as a, zipfile.ZipFile(rendered) as b:
        assert b.infolist()[0].filename == 'mimetype'
        assert b.infolist()[0].compress_type == zipfile.ZIP_STORED
        assert b.testzip() is None
        for z in (a,b):
            for name in z.namelist():
                if name.endswith('.xml'):
                    ET.fromstring(z.read(name))
        structural = signature(ET.fromstring(a.read('content.xml'))) == signature(ET.fromstring(b.read('content.xml')))
        assert structural, 'Document content or XML structure differs from original.'
        ignored = {'content.xml','META-INF/manifest.xml','Thumbnails/thumbnail.png'}
        assert set(a.namelist()) - ignored == set(b.namelist()) - ignored
        preserved = [n for n in a.namelist() if n not in ignored]
        assert all(a.read(n) == b.read(n) for n in preserved), 'Styles/assets/package data changed.'
        return {'content_xml_structurally_identical': True, 'unchanged_package_entries': len(preserved),
                'source_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                'rendered_sha256': hashlib.sha256(Path(rendered).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('extract', help='Create reference Markdown and ODT template from a source ODT')
    p.add_argument('source'); p.add_argument('markdown'); p.add_argument('template'); p.add_argument('--variant', required=True)
    p = sub.add_parser('render', help='Render edited Markdown to an ODT through its matching template; retain the ODT for PDF export')
    p.add_argument('markdown'); p.add_argument('template'); p.add_argument('output')
    p = sub.add_parser('validate', help='Compare an unchanged round trip with its source')
    p.add_argument('source'); p.add_argument('rendered')
    args = parser.parse_args()
    try:
        if args.command == 'extract':
            print(f"Extracted {build(args.source,args.markdown,args.template,args.variant)} editable blocks.")
        elif args.command == 'render':
            print(f"Rendered {len(render(args.markdown,args.template,args.output))} blocks locally.")
        else:
            print(json.dumps(validate(args.source,args.rendered), indent=2))
    except OSError:
        parser.exit(1, 'Error: Cannot read or write private CV files.\n')
    except (ValueError, AssertionError, KeyError, zipfile.BadZipFile) as e:
        parser.exit(1, f'Error: {e}\n')

if __name__ == '__main__':
    main()
