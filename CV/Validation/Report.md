# CV reconstruction validation

Record validation runs here with dates and the exact commands used. Validation
is only complete when the claimed checks were actually run.

Typical checks after extracting a reference/template pair from a supplied
source document:

| Check | Reference | Command |
| --- | --- | --- |
| Editable Markdown blocks | block count from extraction output | `python3 CV/Scripts/cv.py extract ...` |
| Recreated ODT opens and exports in LibreOffice | visual/manual | LibreOffice export |
| Document XML structure, attributes and text match source | structural | `python3 CV/Scripts/cv.py validate source.odt CV/Rendered/recreated.odt` |
| Retained package entries (styles, images) | structural | included in `cv.py validate` |
| Original / recreated page count | PDF | `CV/Scripts/compare_pdfs.py` |
| PDF text and page sizes | PDF | `CV/Scripts/compare_pdfs.py` |
| PDF pixels at 144 dpi | PDF | `CV/Scripts/compare_pdfs.py` |

Notes to record for each validation run:

- The tool versions used (LibreOffice, PyMuPDF) and the environment.
- The generated files were rendered from their extracted Markdown using their
  matching templates; originals were not modified. Package bytes are not
  expected to be identical: XML serialization, ZIP metadata, thumbnail removal
  and manifest changes differ. Document content, formatting, image assets and
  rendered pages are checked separately.
- Renderer regression test results (`python3 -m unittest discover -s CV/Scripts
  -p 'test_*.py' -v`), including any optional tests skipped because PyMuPDF is
  unavailable.
- Baseline layout preflight results, if run
  (`CV/Scripts/check_layout.py <pdf> --report <file>`); source fidelity alone
  does not establish compliance with `CV/Style-guide.md`.

Artifacts (PDFs, comparison reports) belong in this folder; PDFs and JSON
reports are ignored by Git, so record their summary here.
