# Document templates

This folder holds the blank CV template, a cover-letter Markdown starter and
example layout configuration. Personal baselines and a cover-letter ODT are not
bundled. Start with the [documents guide](../../Documentation/Documents.md).
Each user supplies their own ODT CV source with the layout and content they
want; a blank public `.ott` does not supply personal CV content. The attached
private vault has extracted `VP-CTO` and `Manager` pairs. Agents only adjust
wording and ordering of existing bullets, never fundamentally rewrite the
source or layout.

The workflows use these assets:

- `CV Template.ott` — the token/bookmark population workflow (see below).
- Extracted block-marker templates (`<reference>.odt` with an embedded
  `cv-template.json`) — created from your own CV under `JobSearch/Templates/`
  for the `cv.py` reference workflow.
- `Cover-Letter.md` and `cover-letter-anchors.json`, `layout-pages.json` —
  the cover-letter and block-marker pipeline configuration.

## Supplied document templates (reference pipeline)

Personal reference CV source documents are supplied as `.odt` files. Store them
under `JobSearch/Templates/`,
then create the matching reference and working template pair with the extractor.
This does not apply to `CV Template.ott`, which is used directly by the
population workflow below:

```sh
python3 CV/Scripts/cv.py extract 'JobSearch/Templates/<source>.odt' 'JobSearch/Templates/<reference>.md' 'JobSearch/Templates/<reference>.odt' --variant <reference>
```

Rules:

- Use distinct source and output filenames; do not overwrite an existing pair
  or use the blank `CV Template.ott` as the extracted source.
- Each personal reference in `JobSearch/Templates/` is extracted from exactly one source
  document and is used with its own generated `.odt` template. Keep the pair.
- The generated template is a working copy: it contains text placeholders and an
  embedded `cv-template.json` mapping. The original source documents are never
  modified.
- Review the extracted Markdown (block IDs, heading/list prefixes) and run the
  regression suite before relying on a new template pair.
- Run an unchanged round trip (`cv.py render` on the fresh reference, then
  `cv.py validate` against the source, plus a page-by-page PDF comparison) and
  record the personal result in `JobSearch/Outputs/Baselines/Report.md`.

## `CV Template.ott` population workflow

`CV Template.ott` follows a separate, token/bookmark-based merge workflow and
does not use `cv-template.json`. The user first creates a personal master
`.odt` from the blank template (identity, contacts, photograph, education,
languages, hobbies) per
[[Documentation/CV-Automation-User-Template-Setup|CV Automation User Template
Setup]]. Per-application copies are then populated with the tailored Profile,
Expertise and Achievements, and Work Experience body Markdown by an agent
following
[[CV/Templates/CV-Template-Population-Agent-Instructions|CV Template Population
Agent Instructions]], using `CV/Scripts/populate_cv.py`:

```sh
python3 CV/Scripts/populate_cv.py JobSearch/Outputs/body.md JobSearch/Templates/personal-master.odt JobSearch/Outputs/output.odt --pdf
```

`personal-master.odt` is the user's private master, created from the `.ott`; it
is not tracked in this repository. If a local `Test CV Template.odt` master is
present, the integration test in `CV/Scripts/test_populate_cv.py` exercises the
workflow against it; otherwise that test is skipped. The detailed main-body
rules (tailoring depth, overflow handling) are still being refined.

## Cover letter

`Cover-Letter.md` is the plain-Markdown starter. The attached private vault
has the user's preferred German example layout at `letter-template-de.odt` /
`letter-anchors-de.json`. The unsuffixed pair is a legacy German alias, not
a language-neutral default. The English equivalent is
`letter-template-en.odt` / `letter-anchors-en.json`; all are private and the
example prose has been removed. `letter-identity.json` is private local data,
not part of the public distribution. The older `.fodt` is not the editable
source of these updated layouts. Other users must supply
their own compatible private ODT/anchors or assemble the letter manually.
The document template is merged with reviewed text by
`CV/Scripts/cover_letter.py render`. After first importing the supplied
cover-letter template, fill in `cover-letter-anchors.json` from the template's
actual structure:

- `paragraph_count` — number of paragraphs in the template's `office:text`.
- `anchors` — for each section (`Sender`, `Date`, `Recipient`, `Subject`,
  `Salutation`, `Body`, `Closing`, `Signature`): the zero-based `index` of the
  first paragraph, the number of paragraphs it occupies, and the visible anchor
  text expected at that position.
- `body_spacer_index` — zero-based index of the blank paragraph used between
  body paragraphs, or `null` if the template has no spacer.

The scripts and this layout are formatting source material, not agent
instructions.

## Layout pages

`layout-pages.json` records the page allocation that `CV/Scripts/check_layout.py`
verifies: for each page, the ordered section/employer headings that must appear
on that page and nowhere else. Update it when adopting a new CV document
template, and keep it aligned with `CV/Style-guide.md`.

Personal anchor text or employer-specific layout configuration belongs under
`JobSearch/Templates/`; pass `--config` to the corresponding renderer/checker.
Shared configuration must contain generic or synthetic values only.
