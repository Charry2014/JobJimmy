#!/usr/bin/env python3
"""Merge a plain Markdown letter into the supplied Writer template (stdlib only).

The template's structure is described by a JSON anchor configuration
(default: CV/Templates/cover-letter-anchors.json) listing, for each section,
the zero-based paragraph index, the number of paragraphs it occupies and the
visible anchor text expected at that position. Regenerate the configuration
whenever the template structure changes.
"""
import argparse
import json
from pathlib import Path
from output_paths import check_output
import re
import shutil
import subprocess
import tempfile
import zipfile
from xml.dom import minidom as D

import cv

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'Templates/Cover-Letter.odt'
CONFIG = ROOT / 'Templates/cover-letter-anchors.json'
SECTIONS = ('Sender', 'Date', 'Recipient', 'Subject', 'Salutation', 'Body', 'Closing', 'Signature')


def load_anchors(path=None):
    config_path = Path(path) if path else CONFIG
    try:
        config = json.loads(config_path.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise ValueError('Anchor configuration not found in the private vault.') from error
    anchors = config.get('anchors')
    if not isinstance(anchors, dict):
        raise ValueError('Anchor configuration must contain an "anchors" object.')
    unknown = set(anchors) - set(SECTIONS)
    missing = set(SECTIONS) - set(anchors)
    if unknown or missing:
        raise ValueError('Anchor configuration sections mismatch: '
                         f'unknown={sorted(unknown)}, missing={sorted(missing)}.')
    parsed = {}
    for name, entry in anchors.items():
        try:
            index, count = int(entry['index']), int(entry['count'])
            text = entry['text']
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f'Invalid anchor entry for {name}.') from error
        if index < 0 or count < 1 or not isinstance(text, str):
            raise ValueError(f'Invalid anchor entry for {name}.')
        parsed[name] = (index, count, text)
    paragraph_count = config.get('paragraph_count')
    spacer = config.get('body_spacer_index')
    if not isinstance(paragraph_count, int) or paragraph_count < 1:
        raise ValueError('Anchor configuration must contain a positive "paragraph_count".')
    if spacer is not None and (not isinstance(spacer, int) or spacer < 0):
        raise ValueError('Anchor configuration "body_spacer_index" must be a non-negative integer or null.')
    return parsed, paragraph_count, spacer


def load_identity(path):
    try:
        fields = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('Cannot read local identity JSON.') from None
    if not isinstance(fields, dict) or set(fields) != {'Sender', 'Signature'}:
        raise ValueError('Local identity requires Sender and Signature arrays.')
    for lines in fields.values():
        if not isinstance(lines, list) or not lines or any(not isinstance(v, str) or not v.strip() or '\n' in v or '\r' in v for v in lines):
            raise ValueError('Identity fields must contain nonempty single-line strings.')
    signature = fields['Signature']
    if (len(signature) < 3 or any('{{' in v or '}}' in v for lines in fields.values() for v in lines)
            or not any(re.fullmatch(r'\+?[\d ()-]{7,}', line) for line in signature[1:])
            or not any(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', line) for line in signature[1:])):
        raise ValueError('Signature must retain the name, phone number and email address, with contacts below the name.')
    return fields


def read_markdown(path, identity=None):
    """No hidden markers, frontmatter, or silently discarded text."""
    text = Path(path).read_text(encoding='utf-8-sig')
    if identity is not None:
        for name, lines in load_identity(identity).items():
            pattern = r'(?m)(^## ' + name + r'\s*\n)(.*?)(?=^## |\Z)'
            text, count = re.subn(pattern, lambda m: m[1] + '\n' + '\n'.join(lines) + '\n\n', text, flags=re.S)
            if count != 1:
                raise ValueError('Identity section is missing or duplicated.')
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith('## '):
            current = line[3:].strip()
            if current not in SECTIONS or current in sections:
                raise ValueError('Unknown or duplicate letter section.')
            sections[current] = []
        elif current is None:
            if line.strip():
                raise ValueError('Text before the first section would not be rendered.')
        else:
            sections[current].append(line)
    if set(sections) != set(SECTIONS):
        raise ValueError('Required sections: ' + ', '.join(SECTIONS))
    values = {}
    for name, lines in sections.items():
        value = '\n'.join(lines).strip()
        if not value or '{{' in value or '}}' in value:
            raise ValueError(f'Fill in the {name} section before rendering.')
        # This intentionally supports prose, not arbitrary Markdown formatting.
        if re.search(r'(?m)^\s*(?:#|>|[-+*] |\d+[.)] |---\s*$|\|)', value) or re.search(
                r'[`*_<>\[\]]', value):
            raise ValueError(f'Unsupported Markdown in {name}; use plain prose and blank lines.')
        if name in ('Date', 'Subject', 'Salutation', 'Closing'):
            if '\n' in value:
                raise ValueError(f'{name} must be a single line.')
            values[name] = [value]
        elif name == 'Body':
            # Soft wraps join; Markdown two-space hard breaks remain explicit.
            values[name] = [re.sub(r'(?<!\n)\n(?!\n)', ' ', p.replace('  \n', '\x00'))
                            .replace('\x00', '\n') for p in re.split(r'\n\s*\n', value)]
        else:
            values[name] = [line.strip() for line in value.splitlines() if line.strip()]
    signature = values['Signature']
    if (len(signature) < 3
            or not any(re.fullmatch(r'\+?[\d ()-]{7,}', line) for line in signature[1:])
            or not any(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', line) for line in signature[1:])):
        raise ValueError('Signature must retain the name, phone number and email address, with contacts below the name.')
    return values


def visible(paragraph):
    return ''.join(s for _, s in cv.visible_leaves(paragraph))


def render(markdown, template, output, anchors=None, config_path=None, identity=None,
           compact_title_gap=False):
    if Path(output).suffix.lower() != '.odt':
        raise ValueError('Output must have the .odt extension.')
    if Path(output).resolve() in (Path(markdown).resolve(), Path(template).resolve()):
        raise ValueError('Output must not overwrite the Markdown or template.')
    check_output(output, markdown, template, *([identity] if identity else []))
    anchors, paragraph_count, spacer = load_anchors(config_path)
    values = read_markdown(markdown, identity)
    with zipfile.ZipFile(template) as z:
        doc = D.parseString(z.read('content.xml'))
        mf = cv.manifest(z.read('META-INF/manifest.xml'))
    ps = cv.paragraphs(doc)
    if len(ps) != paragraph_count or any(visible(ps[i]) != expected for i, _, expected in anchors.values()):
        raise ValueError('Template structure changed; update and verify the cover-letter anchors first.')
    if compact_title_gap:
        subject_end = anchors['Subject'][0] + anchors['Subject'][1]
        salutation_start = anchors['Salutation'][0]
        gap = ps[subject_end:salutation_start]
        if len(gap) != 1 or visible(gap[0]).strip() or gap[0].parentNode is not ps[subject_end - 1].parentNode:
            raise ValueError('Expected one blank paragraph between subject and salutation; no layout changed.')
    for name, (index, count, _) in anchors.items():
        originals = ps[index:index + count]
        anchor = originals[0]
        parent = anchor.parentNode
        field_values = values[name]
        if name in ('Sender', 'Recipient') and count == 1:
            field_values = ['\n'.join(field_values)]
        elif name == 'Signature' and count == 2 and len(field_values) > 2:
            field_values = [field_values[0], '\n'.join(field_values[1:])]
        for n, value in enumerate(field_values):
            prototype = originals[min(n, count - 1)]
            paragraph = prototype.cloneNode(True)
            if visible(prototype) != value:
                linked_icons = ([child.cloneNode(True) for child in paragraph.childNodes
                                 if child.nodeType == child.ELEMENT_NODE and child.tagName == 'draw:a']
                                if name == 'Signature' else [])
                for child in list(paragraph.childNodes):
                    paragraph.removeChild(child)
                for child in cv.fragment(doc, value):
                    paragraph.appendChild(child)
                for icon in linked_icons:
                    paragraph.appendChild(icon)
            parent.insertBefore(paragraph, anchor)
            if name == 'Body' and n < len(field_values) - 1:
                if spacer is not None:
                    parent.insertBefore(ps[spacer].cloneNode(True), anchor)
        for original in originals:
            parent.removeChild(original)
    if compact_title_gap:
        gap[0].parentNode.removeChild(gap[0])
    cv.pack(template, output, {'content.xml': doc.toxml(encoding='UTF-8'),
                              'META-INF/manifest.xml': mf}, excluded=('Thumbnails/thumbnail.png',))
    return values


def pdf_page_count(path):
    data = Path(path).read_bytes()
    if not data.startswith(b'%PDF-'):
        raise ValueError('PDF export is not a valid PDF document.')
    # LibreOffice emits explicit page dictionaries. Fail closed for other
    # structures rather than accepting a document whose pages we cannot count.
    pages = len(re.findall(rb'/Type\s*/Page\b', data))
    if not pages:
        raise ValueError('Cannot determine PDF page count; no final PDF written.')
    return pages


def export_pdf(odt, output):
    odt, output = Path(odt), Path(output)
    check_output(output, odt)
    if output.suffix.lower() != '.pdf' or odt.resolve() == output.resolve():
        raise ValueError('Export requires a distinct .pdf output path.')
    if output.exists():
        raise ValueError('Final PDF already exists; review or version it before replacing.')
    soffice = shutil.which('soffice') or '/Applications/LibreOffice.app/Contents/MacOS/soffice'
    if not Path(soffice).is_file():
        raise ValueError('LibreOffice is unavailable; no final PDF written.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='letter-export-', dir=output.parent) as temporary:
        result = subprocess.run([soffice, '--headless', '--convert-to', 'pdf',
                                 '--outdir', temporary, str(odt)], capture_output=True)
        rendered = Path(temporary) / (odt.stem + '.pdf')
        if result.returncode or not rendered.is_file():
            raise ValueError('LibreOffice PDF export failed; no final PDF written.')
        pages = pdf_page_count(rendered)
        if pages != 1:
            raise ValueError(f'Cover letter has {pages} pages; no final PDF written. Retry once with --compact-title-gap, then ask the user if it still overflows.')
        rendered.replace(output)
    return pages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='Create a readable Markdown draft to fill in.')
    init.add_argument('markdown', type=Path)
    merge = commands.add_parser('render', help='Merge reviewed Markdown into an editable ODT.')
    merge.add_argument('markdown', type=Path)
    merge.add_argument('output', type=Path)
    merge.add_argument('--identity', type=Path, help='local-only Sender/Signature JSON; never send to a model')
    merge.add_argument('--compact-title-gap', action='store_true',
                       help='one-time overflow retry: remove only the blank paragraph before the salutation')
    hydrate = commands.add_parser('hydrate-identity', help='Create a complete private draft with locally inserted contacts.')
    hydrate.add_argument('markdown', type=Path)
    hydrate.add_argument('identity', type=Path)
    hydrate.add_argument('output', type=Path)
    check_identity = commands.add_parser('check-identity', help='Validate private contacts without printing them.')
    check_identity.add_argument('identity', type=Path)
    export = commands.add_parser('export-pdf', help='Export a final PDF only if the letter is exactly one page.')
    export.add_argument('odt', type=Path)
    export.add_argument('output', type=Path)
    merge.add_argument('--template', type=Path, default=TEMPLATE)
    merge.add_argument('--config', type=Path, help='anchor configuration JSON (default: CV/Templates/cover-letter-anchors.json)')
    args = parser.parse_args()
    try:
        if args.command == 'check-identity':
            load_identity(args.identity)
            print('Local letter identity complete: sender, name, phone and email.')
        elif args.command == 'export-pdf':
            export_pdf(args.odt, args.output)
            print('One-page letter PDF exported; inspect layout locally before use.')
        elif args.command == 'init':
            check_output(args.markdown)
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            with args.markdown.open('x', encoding='utf-8') as f:
                f.write((ROOT / 'Templates/Cover-Letter.md').read_text(encoding='utf-8'))
            print('Private letter draft created.')
        elif args.command == 'hydrate-identity':
            check_output(args.output, args.markdown, args.identity)
            values = read_markdown(args.markdown, args.identity)
            text = '\n\n'.join('## ' + name + '\n\n' + ('\n\n' if name == 'Body' else '\n').join(values[name])
                                 for name in SECTIONS) + '\n'
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(text)
            print('Complete private draft created; identity contents withheld.')
        else:
            values = render(args.markdown, args.template, args.output,
                            config_path=args.config, identity=args.identity,
                            compact_title_gap=args.compact_title_gap)
            print(f'Rendered {len(values["Body"])} body paragraphs locally.')
    except OSError:
        parser.exit(1, 'Error: Cannot read or write private letter files.\n')
    except (ValueError, zipfile.BadZipFile, KeyError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
