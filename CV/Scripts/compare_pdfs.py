#!/usr/bin/env python3
"""Compare original/rendered PDFs page by page; optional dependency: PyMuPDF."""
import argparse
import hashlib
import json
from pathlib import Path
from output_paths import check_output
import sys

try:
    import pymupdf as fitz
except ImportError:
    raise SystemExit('PDF comparison needs PyMuPDF; run with APPMAN_PY_WITH="pymupdf" tools/py, '
                     'or uv run --no-project --with pymupdf python. ODT extraction/rendering uses '
                     'only the standard library. Do not create an in-tree .venv.')


def compare(original, rendered):
    with fitz.open(original) as a, fitz.open(rendered) as b:
        if len(a) != len(b):
            raise ValueError(f'Page count differs: {len(a)} vs {len(b)}')
        pages = []
        for index, (p, q) in enumerate(zip(a,b), 1):
            x, y = p.get_pixmap(matrix=fitz.Matrix(2,2), alpha=False), q.get_pixmap(matrix=fitz.Matrix(2,2), alpha=False)
            pages.append({'page': index, 'same_page_size': p.rect == q.rect,
                          'same_extracted_text': p.get_text() == q.get_text(),
                          'identical_pixels_at_144dpi': (x.width,x.height,x.samples) == (y.width,y.height,y.samples),
                          'original_pixel_sha256': hashlib.sha256(x.samples).hexdigest(),
                          'rendered_pixel_sha256': hashlib.sha256(y.samples).hexdigest()})
        return {'original':str(original),'rendered':str(rendered),'page_count':len(a),'pages':pages,
                'passed':all(p['same_page_size'] and p['same_extracted_text'] and p['identical_pixels_at_144dpi'] for p in pages)}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original'); parser.add_argument('rendered'); parser.add_argument('--report')
    args=parser.parse_args()
    report=compare(args.original,args.rendered)
    text=json.dumps(report,indent=2)+'\n'
    if args.report:
        check_output(args.report, args.original, args.rendered)
        Path(args.report).write_text(text)
    print(text)
    sys.exit(0 if report['passed'] else 1)
