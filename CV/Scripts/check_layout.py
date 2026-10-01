#!/usr/bin/env python3
"""Check the CV page allocation and approximate bottom whitespace.

The expected page allocation is read from a JSON config (default:
CV/Templates/layout-pages.json, overridable with --config): for each page, the
ordered section and employer headings that must appear on that page and nowhere
else.

Requires PyMuPDF. This is a measurable preflight, not a substitute for visual
review of density, typography or editorial repetition.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from output_paths import check_output
import statistics
import sys
try:
    import pymupdf as pdf
except ImportError:
    raise SystemExit('Layout checks need PyMuPDF; run with JOBJIMMY_PY_WITH="pymupdf" tools/py, '
                     'or uv run --no-project --with pymupdf python. Do not create an in-tree .venv.')

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / 'Templates/layout-pages.json'


def load_config(path=None):
    config_path = Path(path) if path else DEFAULT_CONFIG
    try:
        config = json.loads(config_path.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise ValueError('Layout config not found; pass --config with a private profile.') from error
    pages = config.get('pages')
    if not isinstance(pages, dict) or not pages:
        raise ValueError('Layout config must contain a non-empty "pages" object.')
    expected = {}
    for page, headings in pages.items():
        try:
            index = int(page)
        except (TypeError, ValueError) as error:
            raise ValueError('Layout config page keys must be integers.') from error
        if index < 1 or not isinstance(headings, list) or not headings or \
                any(not isinstance(h, str) or not h for h in headings):
            raise ValueError(f'Layout config page {page} must list non-empty heading strings.')
        expected[index] = headings
    return expected


def check(path, expected, bottom_margin_mm=10, line_height_pt=None):
    with pdf.open(path) as doc:
        texts = [' '.join(p.get_text().split()) for p in doc]
        errors = []
        page_count = max(expected)
        if len(doc) != page_count:
            errors.append(f'Expected exactly {page_count} pages; found {len(doc)}.')
        for page, headings in expected.items():
            if page > len(doc):
                errors.append(f'Missing page {page}.')
                continue
            offsets = [texts[page-1].find(h) for h in headings]
            if any(i < 0 for i in offsets) or offsets != sorted(offsets):
                errors.append(f'Page {page}: expected sections absent or out of order.')
        for page, headings in expected.items():
            # Full organisation names distinguish job headings from overview mentions.
            for heading in headings:
                for i, text in enumerate(texts,1):
                    if i != page and heading in text:
                        errors.append(f'{heading} appears on page {i}; expected page {page}.')
        pages = []
        for index, page in enumerate(doc,1):
            blocks = [b for b in page.get_text('dict')['blocks'] if b['type'] == 0]
            spans = [s for b in blocks for l in b['lines'] for s in l['spans'] if s['text'].strip()]
            if not spans:
                errors.append(f'Page {index} has no text.')
                continue
            typical_size = Counter(round(s['size'],1) for s in spans).most_common(1)[0][0]
            steps = []
            for b in blocks:
                ys = [l['spans'][0]['origin'][1] for l in b['lines'] if l['spans']]
                steps += [y-x for x,y in zip(ys,ys[1:]) if typical_size*.8 <= y-x <= typical_size*1.8]
            line_height = line_height_pt or (statistics.median(steps) if steps else typical_size*1.2)
            content_bottom = max(s['bbox'][3] for s in spans)
            usable_bottom = page.rect.height-bottom_margin_mm*72/25.4
            blank_lines = max(0,usable_bottom-content_bottom)/line_height
            pages.append({'page':index,'estimated_line_height_pt':round(line_height,2),
                          'bottom_blank_lines':round(blank_lines,2),
                          'within_five_lines':blank_lines <= 5,
                          'text_within_bottom_margin':content_bottom <= usable_bottom})
            if blank_lines > 5:
                errors.append(f'Page {index}: approximately {blank_lines:.1f} blank lines at bottom (maximum 5).')
            if content_bottom > usable_bottom:
                errors.append(f'Page {index}: text extends into the bottom margin.')
        return {'pdf':str(path),'bottom_margin_mm':bottom_margin_mm,'pages':pages,
                'errors':errors,'passed':not errors,
                'manual_review':['Readability and crowding','Repeated claims','All text stays in its assigned page section']}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf');p.add_argument('--config', help='page-allocation JSON (default: CV/Templates/layout-pages.json)')
    p.add_argument('--bottom-margin-mm',type=float,default=10)
    p.add_argument('--line-height-pt',type=float);p.add_argument('--report')
    args=p.parse_args()
    if args.bottom_margin_mm < 0 or (args.line_height_pt is not None and args.line_height_pt <= 0):
        p.error('Margins must be non-negative and line height positive.')
    try:
        expected = load_config(args.config)
    except ValueError as error:
        p.error(str(error))
    try:
        result=check(args.pdf,expected,args.bottom_margin_mm,args.line_height_pt)
    except (OSError, RuntimeError, ValueError):
        p.exit(1, 'Error: Cannot inspect private PDF; no layout result available.\n')
    text=json.dumps(result,indent=2)+'\n'
    if args.report:
        check_output(args.report, args.pdf)
        Path(args.report).write_text(text)
    # Detailed reports can include private employer headings and document paths.
    # Only numeric, path-free status belongs in hosted-agent tool output.
    print(json.dumps({'passed':result['passed'], 'page_count':len(result['pages']),
                      'bottom_blank_lines':[{'page':page['page'],
                                             'estimated':page['bottom_blank_lines']}
                                            for page in result['pages']],
                      'error_count':len(result['errors'])}))
    sys.exit(0 if result['passed'] else 1)
