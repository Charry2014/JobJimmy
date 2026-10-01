#!/usr/bin/env python3
"""Populate a per-application CV from a plain body Markdown file.

Implements the token/bookmark contract in
CV/Templates/CV-Template-Population-Agent-Instructions.md: the personal master
.odt supplies the identity header, contact row, photograph, LinkedIn link and
the permanent Education, Languages and Sports and Hobbies sections. This script
copies the master and fills the tailored sections - taglines, Profile, Expertise
and Achievements, and Work Experience - from plain Markdown, then writes the
editable .odt. Export to PDF with LibreOffice (--pdf) or manually.

Standard library only; PyMuPDF is optional for the page-count check with --pdf.
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path
from output_paths import check_output
from xml.dom import minidom as D

import cv

PARAGRAPH_TAGS = ('text:p', 'text:h')
BOOKMARK_TAGS = ('text:bookmark', 'text:bookmark-start', 'text:bookmark-end')
SECTION_NAMES = ('Profile', 'Expertise and Achievements', 'Work Experience')
ROLE_FIELD_LABELS = ('Company', 'Title', 'Dates', 'Location')
IDENTITY_TOKENS = ('FULL_NAME', 'EMAIL', 'PHONE', 'LOCATION', 'NATIONALITIES',
                   'EDUCATION_ENTRIES', 'LANGUAGES', 'SPORTS_AND_HOBBIES')
AUTOMATION_TOKENS = ('TAGLINES', 'PROFILE_PARAGRAPHS', 'EXPERTISE_1_TITLE',
                     'EXPERTISE_1_BULLET', 'EXPERTISE_2_TITLE', 'EXPERTISE_2_BULLET',
                     'ROLE_FIRST_COMPANY', 'ROLE_FIRST_TITLE', 'ROLE_FIRST_DATES',
                     'ROLE_FIRST_LOCATION', 'ROLE_FIRST_BULLET',
                     'ROLE_REPEAT_COMPANY', 'ROLE_REPEAT_TITLE', 'ROLE_REPEAT_DATES',
                     'ROLE_REPEAT_LOCATION', 'ROLE_REPEAT_BULLET')
HEADING = re.compile(r'(#{1,6})\s+(.*)$')
FRONT_MATTER = re.compile(r'\A---\s*\n(.*?)\n---\s*\n', re.S)
FIELD = re.compile(r'([A-Za-z][A-Za-z ]*):\s*(.*)$')
TAGLINE_LINE_LIMIT = 50


def text_nodes(node):
    """All descendant text nodes in document order."""
    out = []
    for child in node.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            out.extend(text_nodes(child))
        elif child.nodeType == child.TEXT_NODE:
            out.append(child)
    return out


def paragraph_text(paragraph):
    """Visible text with text:s collapsed to spaces, tabs kept explicit."""
    parts = []
    for child in paragraph.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            if child.tagName == 'text:s':
                parts.append(' ')
            elif child.tagName == 'text:tab':
                parts.append('\t')
            elif child.tagName == 'text:line-break':
                parts.append('\n')
            else:
                parts.append(paragraph_text(child))
        elif child.nodeType == child.TEXT_NODE:
            parts.append(child.data)
    return ''.join(parts)


def find_anchor(doc, name):
    """The paragraph containing the point bookmark `name`."""
    for tag in BOOKMARK_TAGS:
        for bookmark in doc.getElementsByTagName(tag):
            if bookmark.getAttribute('text:name') != name:
                continue
            node = bookmark
            while node is not None and getattr(node, 'tagName', '') not in PARAGRAPH_TAGS:
                node = node.parentNode
            if node is not None:
                return node
            raise ValueError(f'Bookmark {name} is not inside a paragraph.')
    raise ValueError(f'Bookmark {name} not found in the template.')


def replace_token(paragraph, token, value):
    """Replace the first `{{TOKEN}}` occurrence, even if split across style runs."""
    needle = '{{' + token + '}}'
    nodes = text_nodes(paragraph)
    full = ''.join(node.data for node in nodes)
    start = full.find(needle)
    if start < 0:
        raise ValueError(f'Token {needle} not found in {paragraph_text(paragraph)!r}.')
    end = start + len(needle)
    cursor = 0
    replaced = False
    for node in nodes:
        node_start, node_end = cursor, cursor + len(node.data)
        cursor = node_end
        if node_end <= start or node_start >= end:
            continue
        local_start = max(start - node_start, 0)
        local_end = min(end - node_start, len(node.data))
        if not replaced:
            node.data = node.data[:local_start] + value + node.data[local_end:]
            replaced = True
        else:
            node.data = node.data[:local_start] + node.data[local_end:]
    if not replaced:
        raise ValueError(f'Token {needle} could not be replaced.')


def pack_taglines(taglines, limit=TAGLINE_LINE_LIMIT):
    """Greedy tag-boundary packing: tags stay intact, in order, one or more per line.

    A tag is never reworded or split. A line is broken after a tag when adding
    the next tag would exceed the limit.
    """
    lines, current = [], ''
    for tag in taglines:
        candidate = f'{current} | {tag}' if current else tag
        if current and len(candidate) > limit:
            lines.append(current)
            current = tag
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def replace_token_with_fragment(paragraph, token, doc, value):
    """Replace `{{TOKEN}}` with text that may contain explicit line breaks.

    Keeps the surrounding style runs: only the token characters are removed,
    and the fragment (with `\\n` encoded as text:line-break) is inserted at the
    position where the token started.
    """
    needle = '{{' + token + '}}'
    nodes = text_nodes(paragraph)
    full = ''.join(node.data for node in nodes)
    start = full.find(needle)
    if start < 0:
        raise ValueError(f'Token {needle} not found in {paragraph_text(paragraph)!r}.')
    end = start + len(needle)
    cursor = 0
    holder, holder_offset = None, None
    for node in nodes:
        node_start, node_end = cursor, cursor + len(node.data)
        cursor = node_end
        if node_start <= start < node_end:
            holder, holder_offset = node, start - node_start
            break
    if holder is None:
        raise ValueError(f'Token {needle} could not be located in its paragraph.')
    cursor = 0
    for node in nodes:
        node_start, node_end = cursor, cursor + len(node.data)
        cursor = node_end
        if node_end <= start or node_start >= end:
            continue
        local_start = max(start - node_start, 0)
        local_end = min(end - node_start, len(node.data))
        node.data = node.data[:local_start] + node.data[local_end:]
    prefix, suffix = holder.data[:holder_offset], holder.data[holder_offset:]
    holder.data = prefix
    insert_before = holder.nextSibling
    parent = holder.parentNode
    for element in cv.fragment(doc, value):
        parent.insertBefore(element, insert_before)
    if suffix:
        parent.insertBefore(doc.createTextNode(suffix), insert_before)


def strip_bookmarks(element):
    for tag in BOOKMARK_TAGS:
        for bookmark in list(element.getElementsByTagName(tag)):
            bookmark.parentNode.removeChild(bookmark)


def clone(elements):
    clones = [element.cloneNode(True) for element in elements]
    for clone_node in clones:
        strip_bookmarks(clone_node)
    return clones


def is_empty_paragraph(paragraph):
    return not paragraph_text(paragraph).strip()


def expand_bullets(list_element, prototype_item, texts):
    """Replace the prototype list item with one styled item per bullet text."""
    for text in texts:
        item = prototype_item.cloneNode(True)
        strip_bookmarks(item)
        paragraph = next(child for child in item.childNodes
                         if child.nodeType == child.ELEMENT_NODE
                         and child.tagName in PARAGRAPH_TAGS)
        replace_token(paragraph, next_token(paragraph), text)
        prototype_item.parentNode.insertBefore(item, prototype_item)
    prototype_item.parentNode.removeChild(prototype_item)
    if not texts:
        list_element.parentNode.removeChild(list_element)


def next_token(paragraph):
    match = re.search(r'\{\{([A-Z_0-9]+)\}\}', paragraph_text(paragraph))
    if not match:
        raise ValueError('Prototype paragraph contains no token.')
    return match.group(1)


def element_siblings(node):
    return [child for child in node.parentNode.childNodes
            if child.nodeType == child.ELEMENT_NODE]


def repeat_block_elements(doc, start_paragraph):
    """Heading, location and bullet-list elements of the repeat-role prototype.

    Extends from the paragraph carrying ROLE_REPEAT_START up to (excluding) the
    paragraph with the EDUCATION_PAGE_BREAK bookmark or the next section
    heading, with trailing empty spacer paragraphs excluded.
    """
    siblings = element_siblings(start_paragraph)
    begin = siblings.index(start_paragraph)
    boundary = len(siblings)
    for index in range(begin + 1, len(siblings)):
        element = siblings[index]
        if element.tagName in PARAGRAPH_TAGS:
            if element.getElementsByTagName('text:bookmark-start') or \
                    element.getElementsByTagName('text:bookmark'):
                names = {bookmark.getAttribute('text:name')
                         for tag in BOOKMARK_TAGS
                         for bookmark in element.getElementsByTagName(tag)}
                if 'EDUCATION_PAGE_BREAK' in names:
                    boundary = index
                    break
            if element.tagName == 'text:h':
                boundary = index
                break
    block = siblings[begin:boundary]
    while block and block[-1].tagName in PARAGRAPH_TAGS and is_empty_paragraph(block[-1]):
        block.pop()
    lists = [element for element in block if element.tagName == 'text:list']
    if not lists:
        raise ValueError('Repeat-role prototype contains no bullet list.')
    return block, siblings[boundary]


def suppress_page_break(doc, break_paragraph):
    """Give the break paragraph a copy of its style without the page break."""
    automatic = doc.getElementsByTagName('office:automatic-styles')[0]
    style_name = break_paragraph.getAttribute('text:style-name')
    source = next((style for style in automatic.getElementsByTagName('style:style')
                   if style.getAttribute('style:name') == style_name
                   and style.getAttribute('style:family') == 'paragraph'), None)
    if source is None:
        raise ValueError(f'Style {style_name} of the Education page break not found.')
    existing = {style.getAttribute('style:name')
                for style in automatic.getElementsByTagName('style:style')}
    number = 1
    while f'EDPB{number}' in existing:
        number += 1
    clone_style = source.cloneNode(True)
    clone_style.setAttribute('style:name', f'EDPB{number}')
    for properties in clone_style.getElementsByTagName('style:paragraph-properties'):
        for attribute in ('fo:break-before', 'fo:break-after'):
            if properties.hasAttribute(attribute):
                properties.removeAttribute(attribute)
    automatic.appendChild(clone_style)
    break_paragraph.setAttribute('text:style-name', f'EDPB{number}')


def parse_markdown(path):
    """Parse and validate the body Markdown per the population contract."""
    text = Path(path).read_text(encoding='utf-8-sig')
    warnings = []
    taglines = []
    remainder = FRONT_MATTER.sub('', text, count=1) if FRONT_MATTER.match(text) else text
    front = FRONT_MATTER.match(text)
    if front:
        keys = []
        list_items = []
        in_list = False
        for line in front.group(1).splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('- '):
                if not keys or keys[-1] != 'taglines' or not in_list:
                    raise ValueError('List items are only allowed under the taglines front-matter key.')
                item = stripped[2:].strip()
                if len(item) >= 2 and item[0] == item[-1] and item[0] in ('"', "'"):
                    item = item[1:-1]
                list_items.append(item)
                continue
            if ':' in stripped:
                key, _, value = stripped.partition(':')
                key = key.strip()
                if key not in ('taglines',):
                    raise ValueError(f'Unknown front-matter key: {key}')
                if value.strip():
                    raise ValueError('The taglines front-matter key must be a list.')
                keys.append(key)
                in_list = True
            else:
                raise ValueError(f'Unsupported front-matter line: {stripped!r}')
        if keys and keys != ['taglines']:
            raise ValueError('Only the optional taglines front-matter key is supported.')
        taglines = list_items
    if '{{' in remainder or '}}' in remainder:
        raise ValueError('The body Markdown must not contain merge tokens.')
    if re.search(r'[*_`]|\bhttps?://', remainder):
        raise ValueError('Inline Markdown formatting and links are not supported; use plain text.')

    sections, current = {}, None
    blocks = []
    for raw in remainder.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if blocks and blocks[-1][0] == 'para':
                blocks.append(('blank', ''))
            continue
        match = HEADING.match(line.strip())
        if match:
            level, title = len(match.group(1)), match.group(2).strip()
            if level == 1:
                if title not in SECTION_NAMES:
                    raise ValueError(f'Unknown section heading: {title!r}. '
                                     f'Required sections: {", ".join(SECTION_NAMES)}.')
                if title in sections:
                    raise ValueError(f'Duplicate section: {title}')
                sections[title] = []
                current = title
                blocks.append(('h1', title))
                continue
            if current is None:
                raise ValueError('A level-2 heading appears before any section heading.')
            blocks.append((f'h{level}', title))
            continue
        if line.strip().startswith('- '):
            blocks.append(('bullet', line.strip()[2:].strip()))
            continue
        if re.match(r'^\s*\d+[.)] ', line.strip()):
            raise ValueError('Numbered lists are not supported.')
        blocks.append(('para', line.strip()))
    for name in SECTION_NAMES:
        if name not in sections:
            raise ValueError(f'Missing section: {name}')
    if list(sections) != list(SECTION_NAMES):
        raise ValueError('Sections must appear in the order: ' + ', '.join(SECTION_NAMES))

    profile = profile_paragraphs(blocks)
    expertise = expertise_groups(blocks)
    roles = work_experience(blocks, warnings)

    if not taglines:
        raise ValueError('The taglines front-matter key is required (list of 2-3 short phrases).')
    if not 2 <= len(taglines) <= 3:
        warnings.append(f'Taglines should contain 2-3 phrases; found {len(taglines)}.')
    for line in pack_taglines(taglines):
        if len(line) > TAGLINE_LINE_LIMIT:
            warnings.append(f'Tagline line is {len(line)} characters (limit: {TAGLINE_LINE_LIMIT}); '
                            'shorten that tag, since tags are never split or reworded automatically.')

    if not 3 <= len(profile) <= 4:
        warnings.append(f'Profile should contain 3-4 paragraphs; found {len(profile)}.')
    words = sum(len(paragraph.split()) for paragraph in profile)
    if not 130 <= words <= 190:
        warnings.append(f'Profile word count is {words} (target: 130-190).')
    for index, paragraph in enumerate(profile, 1):
        count = len(paragraph.split())
        if not 30 <= count <= 55:
            warnings.append(f'Profile paragraph {index} has {count} words (target: 30-55).')
    for index, (title, bullets) in enumerate(expertise, 1):
        if len(title) > 30:
            warnings.append(f'Expertise subgroup {index} title is {len(title)} characters (target: at most 30).')
        if not 3 <= len(bullets) <= 5:
            warnings.append(f'Expertise subgroup {index} has {len(bullets)} bullets (target: 3-5).')
        group_words = sum(len(bullet.split()) for bullet in bullets)
        if not 15 <= group_words <= 110:
            warnings.append(f'Expertise subgroup {index} has {group_words} words (target: 15-28 per bullet).')
    for index, role in enumerate(roles, 1):
        if not 1 <= len(role['bullets']) <= 5:
            warnings.append(f'Role {index} has {len(role["bullets"])} bullets (target: 1-5).')
        for bullet in role['bullets']:
            count = len(bullet.split())
            if not 15 <= count <= 30:
                warnings.append(f'Role {index} bullet has {count} words (target: 15-30).')

    return {'taglines': taglines, 'profile': profile,
            'expertise': expertise, 'roles': roles}, warnings


def profile_paragraphs(blocks):
    """Paragraphs between the Profile and Expertise headings."""
    start = blocks.index(('h1', 'Profile'))
    end = blocks.index(('h1', 'Expertise and Achievements'))
    collected, buffer = [], []
    for kind, value in blocks[start + 1:end]:
        if kind == 'para':
            buffer.append(value)
            continue
        if buffer:
            collected.append(' '.join(buffer))
            buffer = []
        if kind == 'h1':
            raise ValueError('Unexpected heading inside the Profile section.')
        if kind == 'h2':
            raise ValueError('The Profile section must contain plain paragraphs only.')
        if kind == 'bullet':
            raise ValueError('The Profile section must contain plain paragraphs, not bullets.')
    if buffer:
        collected.append(' '.join(buffer))
    if not collected:
        raise ValueError('The Profile section is empty.')
    return collected


def expertise_groups(blocks):
    """Exactly two subgroups with bullets between the Expertise and Work headings."""
    start = blocks.index(('h1', 'Expertise and Achievements'))
    end = blocks.index(('h1', 'Work Experience'))
    groups, current = [], None
    for kind, value in blocks[start + 1:end]:
        if kind == 'h1':
            raise ValueError('Unexpected heading inside the Expertise section.')
        if kind == 'h2':
            if current is not None:
                groups.append(current)
            current = [value, []]
        elif kind == 'bullet':
            if current is None:
                raise ValueError('Expertise bullets must follow a subgroup heading.')
            current[1].append(value)
        elif kind == 'para':
            raise ValueError(f'Prose is not allowed in the Expertise section: {value!r}')
    if current is not None:
        groups.append(current)
    if len(groups) != 2:
        raise ValueError(f'The Expertise section requires exactly two subgroups; found {len(groups)}.')
    for title, bullets in groups:
        if not bullets:
            raise ValueError(f'Expertise subgroup {title!r} has no bullets.')
    return groups


def work_experience(blocks, warnings):
    """Numbered roles with the four labelled fields and a bullet list."""
    start = blocks.index(('h1', 'Work Experience'))
    roles, current = [], None
    for kind, value in blocks[start + 1:]:
        if kind == 'h1':
            raise ValueError('Unexpected heading inside the Work Experience section.')
        if kind == 'h2':
            match = re.fullmatch(r'Role (\d+)', value)
            if not match:
                raise ValueError(f'Work-experience headings must be "Role NN"; found {value!r}.')
            if current is not None:
                roles.append(current)
            current = {'number': int(match.group(1)), 'fields': {}, 'bullets': []}
        elif kind == 'bullet':
            if current is None:
                raise ValueError('A bullet appears before the first Role heading.')
            current['bullets'].append(value)
        elif kind == 'para':
            if current is None:
                raise ValueError('Prose appears before the first Role heading.')
            match = FIELD.match(value)
            if not match or match.group(1).strip() not in ROLE_FIELD_LABELS:
                raise ValueError(f'Role content must use the labelled fields '
                                 f'{", ".join(ROLE_FIELD_LABELS)}; found {value!r}')
            label = match.group(1).strip()
            if label in current['fields']:
                raise ValueError(f'Duplicate field in a role: {label}')
            if not match.group(2).strip():
                raise ValueError(f'Empty role field: {label}')
            current['fields'][label] = match.group(2).strip()
    if current is not None:
        roles.append(current)
    if not roles:
        raise ValueError('The Work Experience section is empty.')
    numbers = [role['number'] for role in roles]
    if numbers != list(range(1, len(roles) + 1)):
        raise ValueError(f'Role headings must be numbered consecutively from 01; found {numbers}.')
    for role in roles:
        missing = [label for label in ROLE_FIELD_LABELS if label not in role['fields']]
        if missing:
            raise ValueError(f'Role {role["number"]} is missing fields: {", ".join(missing)}.')
        if not role['bullets']:
            warnings.append(f'Role {role["number"]} has no bullets.')
    return roles


def populate(markdown, master, output, education_break='keep', strict=False):
    """Copy the master, fill the tailored sections, write the output .odt."""
    check_output(output, markdown, master)
    body, warnings = parse_markdown(markdown)
    if strict and warnings:
        raise ValueError('Strict validation failed:\n- ' + '\n- '.join(warnings))
    master = Path(master)
    output = Path(output)
    if output.suffix.lower() != '.odt':
        raise ValueError('Output must have the .odt extension.')
    if output.resolve() in (master.resolve(), Path(markdown).resolve()):
        raise ValueError('Output must not overwrite the master or the Markdown.')
    master_bytes = master.read_bytes()
    with zipfile.ZipFile(master) as z:
        doc = D.parseString(z.read('content.xml'))
        mf = cv.manifest(z.read('META-INF/manifest.xml'))

    present = set(re.findall(r'\{\{([A-Z_0-9]+)\}\}', doc.toxml()))
    identity_left = sorted(present & set(IDENTITY_TOKENS))
    if identity_left:
        raise ValueError('The master is not personalised; identity tokens still present: '
                         + ', '.join('{{%s}}' % token for token in identity_left) + '.')
    unknown = sorted(present - set(AUTOMATION_TOKENS))
    if unknown:
        raise ValueError('Unknown template tokens: ' + ', '.join('{{%s}}' % token for token in unknown))

    taglines_paragraph = find_anchor(doc, 'TAGLINES')
    replace_token_with_fragment(taglines_paragraph, 'TAGLINES', doc,
                                '\n'.join(pack_taglines(body['taglines'])))

    profile_paragraph = find_anchor(doc, 'PROFILE_CONTENT')
    for text in body['profile']:
        clone_paragraph = clone([profile_paragraph])[0]
        replace_token(clone_paragraph, next_token(clone_paragraph), text)
        profile_paragraph.parentNode.insertBefore(clone_paragraph, profile_paragraph)
    profile_paragraph.parentNode.removeChild(profile_paragraph)

    for anchor_title, anchor_bullets, (title, bullets) in zip(
            ('EXPERTISE_1_TITLE', 'EXPERTISE_2_TITLE'),
            ('EXPERTISE_1_BULLETS', 'EXPERTISE_2_BULLETS'), body['expertise']):
        replace_token(find_anchor(doc, anchor_title), anchor_title, title)
        bullet_paragraph = find_anchor(doc, anchor_bullets)
        list_element = bullet_paragraph.parentNode
        while list_element.tagName != 'text:list':
            list_element = list_element.parentNode
        item = bullet_paragraph.parentNode
        expand_bullets(list_element, item, bullets)

    first_heading = find_anchor(doc, 'ROLE_FIRST_START')
    first_location = find_anchor(doc, 'ROLE_FIRST_LOCATION')
    first_bullet = find_anchor(doc, 'ROLE_FIRST_BULLETS')
    role = body['roles'][0]
    replace_token(first_heading, 'ROLE_FIRST_COMPANY', role['fields']['Company'])
    replace_token(first_heading, 'ROLE_FIRST_TITLE', role['fields']['Title'])
    replace_token(first_heading, 'ROLE_FIRST_DATES', role['fields']['Dates'])
    replace_token(first_location, 'ROLE_FIRST_LOCATION', role['fields']['Location'])
    first_list = first_bullet.parentNode
    while first_list.tagName != 'text:list':
        first_list = first_list.parentNode
    expand_bullets(first_list, first_bullet.parentNode, role['bullets'])

    repeat_heading = find_anchor(doc, 'ROLE_REPEAT_START')
    block, boundary = repeat_block_elements(doc, repeat_heading)

    def fill_role_block(elements, role):
        heading = elements[0]
        replace_token(heading, 'ROLE_REPEAT_COMPANY', role['fields']['Company'])
        replace_token(heading, 'ROLE_REPEAT_TITLE', role['fields']['Title'])
        replace_token(heading, 'ROLE_REPEAT_DATES', role['fields']['Dates'])
        location = next(element for element in elements
                        if element.tagName in PARAGRAPH_TAGS
                        and '{{ROLE_REPEAT_LOCATION}}' in paragraph_text(element))
        replace_token(location, 'ROLE_REPEAT_LOCATION', role['fields']['Location'])
        list_element = next(element for element in elements if element.tagName == 'text:list')
        item = next(child for child in list_element.childNodes
                    if child.nodeType == child.ELEMENT_NODE)
        expand_bullets(list_element, item, role['bullets'])

    remaining = body['roles'][1:]
    anchor = block[-1].nextSibling
    while anchor is not None and anchor.nodeType != anchor.ELEMENT_NODE:
        anchor = anchor.nextSibling
    if anchor is None:
        anchor = boundary
    extra_copies = []
    for role in remaining[1:]:
        clones = clone(block)
        for element in clones:
            anchor.parentNode.insertBefore(element, anchor)
        extra_copies.append(clones)
    if remaining:
        fill_role_block(block, remaining[0])
        for role, elements in zip(remaining[1:], extra_copies):
            fill_role_block(elements, role)
    else:
        for element in block:
            element.parentNode.removeChild(element)

    break_paragraph = find_anchor(doc, 'EDUCATION_PAGE_BREAK')
    if education_break == 'suppress':
        suppress_page_break(doc, break_paragraph)

    full_text = ' '.join(paragraph_text(paragraph)
                         for paragraph in doc.getElementsByTagName('text:p'))
    full_text += ' ' + ' '.join(paragraph_text(paragraph)
                                for paragraph in doc.getElementsByTagName('text:h'))
    leftover = sorted(set(re.findall(r'\{\{([A-Z_0-9]+)\}\}', full_text)))
    if leftover:
        raise ValueError('Merge tokens remain after population: '
                         + ', '.join('{{%s}}' % token for token in leftover))

    cv.pack(master, output, {'content.xml': doc.toxml(encoding='UTF-8'),
                             'META-INF/manifest.xml': mf},
            excluded=('Thumbnails/thumbnail.png',))
    if master.read_bytes() != master_bytes:
        raise ValueError('The personal master was modified; refusing to continue.')
    return body, warnings


def render_pdf(output, outdir):
    import subprocess
    import tempfile
    candidates = [Path('/Applications/LibreOffice.app/Contents/MacOS/soffice')]
    for candidate in candidates + [Path('soffice')]:
        if candidate.exists() or candidate.name == 'soffice':
            soffice = candidate
            break
    else:
        raise ValueError('LibreOffice (soffice) not found; export the PDF manually.')
    check_output(outdir / (output.stem + ".pdf"), output)
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.lo_profile_', dir=outdir) as profile:
        result = subprocess.run(
            [str(soffice), '--headless', f'-env:UserInstallation=file://{profile}',
             '--convert-to', 'pdf', '--outdir', str(outdir), str(output)],
            capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise ValueError('PDF export failed; renderer diagnostics withheld to protect document data.')
    pdf = outdir / (output.stem + '.pdf')
    if not pdf.exists():
        raise ValueError(f'PDF export produced no file: {pdf}')
    return pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('markdown', type=Path, help='plain body Markdown (Profile, Expertise and Achievements, Work Experience)')
    parser.add_argument('master', type=Path, help='personal master .odt (not the .ott)')
    parser.add_argument('output', type=Path, help='per-application .odt to write')
    parser.add_argument('--education-break', choices=('keep', 'suppress'), default='keep',
                        help='keep or suppress the forced page break before Education '
                             '(suppress when Work Experience flows onto page 3)')
    parser.add_argument('--pdf', action='store_true', help='also export a PDF with LibreOffice')
    parser.add_argument('--strict', action='store_true', help='treat length-budget warnings as errors')
    parser.add_argument('--outdir', type=Path, help='directory for the --pdf export (default: alongside the output)')
    args = parser.parse_args()
    try:
        body, warnings = populate(args.markdown, args.master, args.output,
                                  args.education_break, args.strict)
        print(f"Populated {args.output}: {len(body['profile'])} profile paragraphs, "
              f"{len(body['expertise'])} expertise subgroups, {len(body['roles'])} roles.")
        for warning in warnings:
            print(f'Warning: {warning}')
        if args.pdf:
            pdf = render_pdf(args.output, args.outdir or args.output.parent)
            print(f'PDF exported: {pdf}')
            try:
                import pymupdf
                with pymupdf.open(pdf) as document:
                    pages = len(document)
                print(f'PDF pages: {pages}' + ('' if pages == 3 else ' (expected exactly 3; '
                      'consider --education-break suppress or shorter body text)'))
            except ImportError:
                print('PyMuPDF not installed; page count not checked.')
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
