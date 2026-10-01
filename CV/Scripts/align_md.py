#!/usr/bin/env python3
"""Align a plain Markdown CV to a template's cv:pNNN block layout.

`cv.py render` expects a file whose `<!-- cv:pNNN -->` blocks match a template's
blocks exactly once, in order, with each block's heading/list prefix. That format
is convenient when copying a reference, but awkward when a CV starts as ordinary
Markdown prose.

This tool bridges the two. It reads a template's `cv-template.json`, reads a plain
Markdown CV, and aligns the two paragraph sequences with fuzzy text matching. The
number of source paragraphs and bullets does NOT have to equal the number of
template blocks: within a run of bullet blocks the source bullets are distributed
across the blocks (a block may hold several `- ` lines, or none), and unmatched
template blocks fall back to the reference baseline so nothing is silently lost.

Output is an intermediate block-marked Markdown file intended for review before
rendering:

    python3 CV/Scripts/align_md.py draft.md CV/Templates/Manager.odt out.md \
        --report out-report.json
    python3 CV/Scripts/cv.py render out.md CV/Templates/Manager.odt out.odt

Standard library only.
"""
import argparse
import difflib
import json
import re
import sys
import zipfile
from pathlib import Path
from output_paths import check_output

MAP = 'cv-template.json'
GAP = -0.30
MIN_TITLE = 0.20
MIN_H2 = 0.30
MIN_H3 = 0.26
MIN_PROSE = 0.12
YEAR = re.compile(r'\b(19|20)\d\d\b')
BLOCK = re.compile(r'<!-- cv:p\d+ -->')
HEADING = re.compile(r'(#{1,6})\s+(.*)$')


def strip_md(text):
    """Remove inline Markdown that the ODT renderer would print literally."""
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[*_`]+', '', text)
    return text.strip()


def norm(text):
    text = strip_md(text)
    text = text.replace('&', ' and ')
    text = text.casefold()
    text = re.sub(r'[^0-9a-zäöüß]+', ' ', text)
    return ' '.join(text.split())


def similar(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return max(ratio, jaccard)


def parse_source(text):
    """Parse ordinary Markdown into ordered units.

    Consecutive non-blank lines form one paragraph unless the line ends with a
    Markdown hard break (two spaces). A role/date line after an H3 is always a
    separate paragraph from the following location, with or without a blank
    line. The role/date paragraph folds into the reference's employer heading.
    """
    units, buffer = [], []

    def flush():
        if buffer:
            units.append(['para', ' '.join(buffer)])
            buffer.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        match = HEADING.match(line)
        if match:
            flush()
            units.append([f'h{len(match.group(1))}', strip_md(match.group(2))])
            continue
        if line.startswith('- '):
            flush()
            units.append(['bullet', strip_md(line[2:])])
            continue
        if (len(buffer) == 1 and units and units[-1][0] == 'h3'
                and YEAR.search(buffer[0]) and re.search(r'\s[\|–—]\s|\t', buffer[0])):
            flush()
        buffer.append(strip_md(line))
        if raw.endswith('  '):
            flush()
    flush()

    folded = []
    i = 0
    while i < len(units):
        kind, value = units[i]
        if kind == 'h3' and i + 1 < len(units) and units[i + 1][0] == 'para':
            nxt = units[i + 1][1]
            if YEAR.search(nxt) and re.search(r'\s[\|–—]\s|\t', nxt):
                value = '\t'.join([value] + [p.strip() for p in re.split(r'\s*\|\s*', nxt)])
                folded.append(['h3', value])
                i += 2
                continue
        folded.append([kind, value])
        i += 1

    units = []
    for kind, value in folded:
        if kind == 'bullet' and units and units[-1][0] == 'bullets':
            units[-1][1].append(value)
        elif kind == 'bullet':
            units.append(['bullets', [value]])
        else:
            units.append([kind, value])
    return units


def load_template(template):
    with zipfile.ZipFile(template) as z:
        mapping = json.loads(z.read(MAP))
    blocks = []
    for item in mapping['blocks']:
        text = ''.join(s['text'] for s in item['slots']).strip()
        prefix = item['prefix']
        kind = {'- ': 'bullet', '# ': 'title', '## ': 'h2', '### ': 'h3'}.get(prefix, 'prose')
        blocks.append({'id': item['id'], 'prefix': prefix, 'kind': kind,
                       'text': text, 'multi': '\n' in text})
    units = []
    for block in blocks:
        if block['kind'] == 'bullet' and units and units[-1]['kind'] == 'bullets':
            units[-1]['ids'].append(block['id'])
            units[-1]['texts'].append(block['text'])
        elif block['kind'] == 'bullet':
            units.append({'kind': 'bullets', 'ids': [block['id']], 'texts': [block['text']]})
        else:
            units.append(dict(block))
    return mapping, units


COMPAT = {('title', 'h1'), ('h2', 'h2'), ('h3', 'h3'),
          ('prose', 'para'), ('bullets', 'bullets')}
MINIMUM = {'title': MIN_TITLE, 'h2': MIN_H2, 'h3': MIN_H3,
           'prose': MIN_PROSE, 'bullets': 0.0}


def pair_score(tunit, sunit):
    tk, sk = tunit['kind'], sunit[0]
    if (tk, sk) not in COMPAT:
        return None
    if tk == 'bullets':
        return 1.0
    if tk == 'title':
        return 1.0
    score = similar(tunit['text'], sunit[1])
    return score if score >= MINIMUM[tk] else None


def align(tunits, sunits):
    """Global order-preserving alignment maximising fuzzy similarity."""
    n, m = len(tunits), len(sunits)
    neg = float('-inf')
    dp = [[neg] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            best, step = neg, None
            if i and j:
                score = pair_score(tunits[i - 1], sunits[j - 1])
                if score is not None and dp[i - 1][j - 1] + score > best:
                    best, step = dp[i - 1][j - 1] + score, ('pair', i - 1, j - 1)
            if i and dp[i - 1][j] + GAP > best:
                best, step = dp[i - 1][j] + GAP, ('skip-t', i - 1, j)
            if j and dp[i][j - 1] + GAP > best:
                best, step = dp[i][j - 1] + GAP, ('skip-s', i, j - 1)
            dp[i][j], back[i][j] = best, step
    pairs, dropped, fallback = [], [], []
    i, j = n, m
    while i or j:
        step = back[i][j]
        if step is None:
            break
        action, pi, pj = step
        if action == 'pair':
            pairs.append((pi, pj))
            i, j = pi, pj
        elif action == 'skip-t':
            fallback.append(pi)
            i = pi
        else:
            dropped.append(pj)
            j = pj
    pairs.reverse(), dropped.reverse(), fallback.reverse()
    return pairs, dropped, fallback


def distribute(ids, lines):
    """Spread N source bullets across M blocks; extra lines join earlier blocks."""
    counts = {block_id: [] for block_id in ids}
    if not lines:
        return counts
    base, extra = divmod(len(lines), len(ids))
    cursor = 0
    for position, block_id in enumerate(ids):
        take = base + (1 if position < extra else 0)
        counts[block_id] = lines[cursor:cursor + take]
        cursor += take
    return counts


def title_text(value):
    """Drop an editorial subtitle such as 'Name — CV draft for Role'."""
    return re.split(r'\s+[—–-]\s+', value, maxsplit=1)[0].strip() or value


def line(value):
    if '\n' in value:
        raise ValueError('internal error: newline in a non-bullet block')
    return value


def build_markdown(mapping, tunits, sunits, pairs, dropped, fallback):
    # A template block whose baseline holds several lines absorbs the whole run of
    # consecutive source paragraphs, even if the aligner paired some of them with
    # neighbouring short blocks. Those neighbours revert to the baseline.
    absorbed, multi = set(), {}
    for pi, pj in pairs:
        if tunits[pi]['kind'] == 'prose' and tunits[pi]['multi']:
            start = pj
            while start > 0 and sunits[start - 1][0] == 'para':
                start -= 1
            end = pj
            while end + 1 < len(sunits) and sunits[end + 1][0] == 'para':
                end += 1
            group = [sunits[k][1] for k in range(start, end + 1)]
            for k in range(start, end + 1):
                if k != pj:
                    absorbed.add(k)
            multi[pi] = group

    fallback = list(fallback)
    values, decisions = {}, []
    bullet_values = {}
    for pi, pj in pairs:
        tunit = tunits[pi]
        if tunit['kind'] != 'bullets' and pj in absorbed:
            fallback.append(pi)
            continue
        if tunit['kind'] == 'bullets':
            bullet_values.update(distribute(tunit['ids'], sunits[pj][1]))
            decisions.append({'id': ','.join(tunit['ids']), 'decision': 'bullets',
                              'source_bullets': len(sunits[pj][1])})
        elif tunit['kind'] == 'title':
            values[tunit['id']] = tunit['prefix'] + line(title_text(sunits[pj][1]))
            decisions.append({'id': tunit['id'], 'decision': 'matched',
                              'source': sunits[pj][1]})
        elif pi in multi:
            values[tunit['id']] = tunit['prefix'] + '<br>'.join(line(x) for x in multi[pi])
            decisions.append({'id': tunit['id'], 'decision': 'matched-run',
                              'source_paragraphs': len(multi[pi])})
        else:
            values[tunit['id']] = tunit['prefix'] + line(sunits[pj][1])
            decisions.append({'id': tunit['id'], 'decision': 'matched',
                              'source': sunits[pj][1]})
    fallback = list(dict.fromkeys(fallback))
    for pi in fallback:
        tunit = tunits[pi]
        if tunit['kind'] == 'bullets':
            for block_id, text in zip(tunit['ids'], tunit['texts']):
                bullet_values[block_id] = [text.replace('\n', '<br>')]
            decisions.append({'id': ','.join(tunit['ids']), 'decision': 'baseline'})
        else:
            values[tunit['id']] = tunit['prefix'] + line(tunit['text'].replace('\n', '<br>'))
            decisions.append({'id': tunit['id'], 'decision': 'baseline'})
    for block_id, lines in bullet_values.items():
        values[block_id] = [line(text) for text in lines]

    order = [b['id'] for b in mapping['blocks']]
    out = ['---', 'type: cv-reference', f"variant: {mapping['variant']}",
           f"source_file: {json.dumps(mapping.get('source_name', ''))}", '---', '',
           '<!-- Generated by CV/Scripts/align_md.py; review before rendering.',
           'Edit text inside cv blocks; preserve IDs, headings and list prefixes.',
           'Use <br> for a line break. Formatting comes from the ODT template. -->', '']
    for block in mapping['blocks']:
        value = values.get(block['id'], '')
        if isinstance(value, list):
            body = '\n'.join('- ' + item for item in value)
        else:
            body = value
        out += [f"<!-- cv:{block['id']} -->", body, f"<!-- /cv:{block['id']} -->", '']
    report = {
        'template_variant': mapping['variant'],
        'template_blocks': len(mapping['blocks']),
        'source_units': len(sunits),
        'pairs': len(pairs),
        'fallback_blocks': [tunits[pi]['id'] if 'id' in tunits[pi] else ','.join(tunits[pi]['ids'])
                            for pi in fallback],
        'dropped_source': [{'kind': sunits[pj][0],
                            'text': sunits[pj][1] if sunits[pj][0] != 'bullets' else sunits[pj][1][:3]}
                           for pj in dropped if pj not in absorbed],
        'blocks': sorted(decisions, key=lambda d: order.index(d['id'].split(',')[0])),
    }
    return '\n'.join(out).rstrip() + '\n', report


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('markdown', help='plain Markdown CV without cv:pNNN markers')
    parser.add_argument('template', help='template ODT containing cv-template.json')
    parser.add_argument('output', help='intermediate block-marked Markdown to write')
    parser.add_argument('--report', help='optional JSON alignment report path')
    args = parser.parse_args()
    try:
        check_output(args.output, args.markdown, args.template)
        if args.report:
            check_output(args.report, args.markdown, args.template)
        source = Path(args.markdown).read_text(encoding='utf-8')
        if BLOCK.search(source):
            raise ValueError('Input already contains cv:pNNN markers; expected plain Markdown.')
        mapping, tunits = load_template(args.template)
        sunits = parse_source(source)
        pairs, dropped, fallback = align(tunits, sunits)
        markdown, report = build_markdown(mapping, tunits, sunits, pairs, dropped, fallback)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(markdown, encoding='utf-8')
        if args.report:
            Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding='utf-8')
        print(f"Aligned {report['source_units']} source units to "
              f"{report['template_blocks']} blocks: {report['pairs']} matched, "
              f"{len(report['fallback_blocks'])} baseline fallbacks, "
              f"{len(report['dropped_source'])} source units dropped.")
    except OSError:
        sys.exit('Error: Cannot read or write private CV files.')
    except (ValueError, KeyError, zipfile.BadZipFile) as exc:
        sys.exit(f'Error: {exc}')


if __name__ == '__main__':
    main()
