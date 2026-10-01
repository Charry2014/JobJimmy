# CV tooling reference

New here? Start with the [user documents guide](../Documentation/Documents.md).
This page is the detailed command and format reference. Personal baselines and
a compatible cover-letter ODT are not bundled with the public project.
Follow `.kilo/skills/tailor-cv/SKILL.md` or
`.kilo/skills/write-cover-letter/SKILL.md` for the ordered agent workflows.
Each user supplies their own ODT CVs containing the desired substantive
content and layout; this private vault has separate VP/CTO/Director and
engineering manager/team lead variants, not public defaults.

The reference CVs retain the source documents' section order, headings and
wording. Start with the reference closest to the role:

- The extracted personal baselines live in the private repository's
  `JobSearch/Templates/`, each as a reference Markdown plus its matching
  document template ODT (currently `VP-CTO` and `Manager`). `CV/References/`
  in this workspace is reserved for non-personal reference copies and its index
  may be empty.

A second workflow builds the complete document from the `CV Template.ott` token
template: the user's personal master `.odt` supplies identity, contacts,
photograph, LinkedIn link, education, languages and hobbies, and
`CV/Scripts/populate_cv.py` fills only the tailored body. See
[[CV/Templates/CV-Template-Population-Agent-Instructions]] and
[[Documentation/CV-Automation-User-Template-Setup]].

## Professional knowledge base

Start with [[Knowledge/Overview|the professional personality and working profile]]
when tailoring a CV. It connects working style and career direction to supported
experience, with [[Knowledge/CV-positioning|guidance for executive and managerial positioning]].
Use [[Knowledge/Writing-guide|the character writing guide]] for CV bullets
and cover letters, with [[Knowledge/Reasoning-profile|analytical habits]] as
additional context. Original supplied reflections are preserved under
`JobSearch/Knowledge/Sources`.
Maintain [[Knowledge/Gaps-and-mitigations|skill gaps and mitigating experience]]
as new facts emerge; this is a learning resource used across applications.
Read [[Knowledge/Evidence-and-sources|the evidence boundaries]] before expanding
claims; the knowledge base informs drafting and is not inserted automatically.

## Files

| Folder | Contents |
| --- | --- |
| `References` | Extracted, editable Markdown reference CVs |
| `Knowledge` | *Moved* — the personal knowledge base lives in the private repository at `JobSearch/Knowledge/` (curated profile, career evidence, role preferences and source snapshots) |
| `Templates` | Matching CV document templates and the cover-letter template/Markdown starter |
| `Rendered` | Non-personal documentation only; personal recreations belong in `JobSearch/Outputs/Baselines/` |
| `Scripts` | Extraction, rendering, alignment, layout and PDF comparison tools |
| `Validation` | Non-personal documentation only; personal validation belongs in `JobSearch/Outputs/Baselines/` |

After initial extraction from a supplied source document, rendering needs only
the Markdown file and matching template.

All references share the same main sections: Profile, Expertise & Achievements,
Work Experience, Education, Languages, and Sports & Hobbies, preceded by the name,
positioning statement and contact details. Existing job titles, dates, wording
and numbers are retained without editorial corrections.

## Layout rules

Follow [[CV/Style-guide|the CV layout and style guide]] for every tuned version.
The per-template page allocation is recorded in `CV/Templates/layout-pages.json`.
Bullet counts and text length may vary within that structure. Avoid repetition,
crowding and more than five empty body-text lines at the bottom.

## Edit and render

Review and correct the Markdown text with the user first. Do not render ODT/PDF
for each wording revision. Render only once the user confirms the text is correct
or requests rendering, then validate layout. Existing previews become outdated
when the Markdown changes.

New CVs follow a two-phase workflow. **Draft first in plain Markdown:** write and
review the text in `JobSearch/Applications/<application-slug>/CV/<application>-cv-draft.md`,
with no `cv:pNNN` markers and no ODT/PDF. **Fold second:** once the text is agreed,
run `align_md.py` to produce the block-marked intermediate
`JobSearch/Applications/<application-slug>/CV/<application>-blocks.md`, review its alignment
report and text, and render that. The draft's structural Markdown (headings,
paragraph breaks, bullet lists, line grouping) is the mapping guide onto the
template paragraphs. Older records instead copy the chosen reference straight into
`JobSearch/Applications/<application-slug>/CV/<application>.md` and edit its `cv:pNNN` blocks
in place; that file is the render-ready equivalent of the folded `<application>-blocks.md`.

Never write a CV from scratch: always start from the closest reference. For the
two-phase path, base the plain draft on that reference; for the direct path, copy
it into `JobSearch/Applications/<application-slug>/CV/<application>.md`. Choose exactly one
reference and use its text as well as its matching formatting template. Do not
start from another application's draft or blend references. Preserve the vast
majority of the original wording and detail, making small changes only to
specific points supported by the job description. Leave unrelated text alone.
Do not rewrite the profile, systematically reword bullets, add/remove substantive
content, change layout or replace sections. Ordinary tailoring permits small
wording edits and reordering existing bullets within their sections.
A request for a tailored draft does not authorise substantial rewriting.

Follow the minimal-edit rules in [[CV/Style-guide]]. Apply required voice/tense
corrections minimally. Keep the lightly tailored source Markdown before translation,
and translate it faithfully without reframing or substantial shortening. Review
every changed block against the chosen reference and record the baseline and
specific tailoring changes in the activity note. Preserved block IDs alone do
not prove fidelity to the reference.

Before drafting, identify the language of the job description and the
application instructions. If the main advert is in a foreign language, prepare the
CV and cover letter in that language. For mixed-language adverts, use the
application instructions and explicit document requirements to decide. Record
the code in the linked research note's `document_language` property and the
evidence under **Research notes**; CV and letter steps reuse it. Resolve
genuinely conflicting instructions before drafting. Preserve the reference as the baseline
and make targeted, surgical changes in the copy, then render it with the matching
template:

```sh
python3 CV/Scripts/cv.py render JobSearch/Templates/<baseline>.md JobSearch/Templates/<baseline>.odt JobSearch/Outputs/Baselines/<baseline>.odt
```

Replace the input/output paths for tailored drafts with paths inside the
relevant application folder, for example:

```sh
python3 CV/Scripts/cv.py render JobSearch/Applications/<application-slug>/CV/<application>.md JobSearch/Templates/<template>.odt JobSearch/Applications/<application-slug>/CV/<output>.odt
```

The render command creates the editable ODT and must retain it in the application's
flat `CV/` folder. Export that ODT to PDF into the same application `CV/` folder;
do not delete the ODT after PDF conversion. Link both outputs from the application
activity when recording the prepared CV.

The output-path guard rejects generated documents in the public workspace and
prevents private-input outputs escaping `JobSearch/`, including through symlinks.
Keep personal layout configuration under `JobSearch/Templates/` and pass
`check_layout.py --config` explicitly. Never add real employer headings to the
shared `CV/Templates/layout-pages.json`.

### Application CV filenames

Keep application CV folders easy to scan by using a compact slug for every artifact:
`YYYY-MM-company-position`, including the date, company and meaningful position
abbreviation. Aim for a base slug of about 30 characters, then append a short
artifact suffix such as `-draft`, `-blocks`, `-de`, `-proposed`, `-review` or
`-layout`. The final submission PDF is the deliberate exception: `<Your Name> - CV.pdf`.

### Application CV source control

In each application's flat `CV/` folder, commit the source Markdown and the final
ODT/PDF documents (including the final `<Your Name> - CV.pdf`). Generated JSON
reports (`*-blocks-report.json`, `*-layout.json`) and intermediate/test renders
carrying `-proposed`, `-preview`, `-review` or `-test` are ignored by Git and
should be regenerated rather than committed. Personal baseline renders and reports belong under `JobSearch/Outputs/Baselines/`.
Public `CV/Rendered/` and `CV/Validation/` may contain only non-personal
documentation; public templates and references must be genuinely blank or synthetic.
Commands run from the AppMan project root and need Python 3; extraction and
rendering use no third-party libraries. Existing output files are replaced, so
use a new filename for versions you want to retain. The renderer refuses to
overwrite its template.

## Cover letters: plain Markdown to ODT/PDF

Supply a compatible private cover-letter ODT plus its matching anchor JSON,
then pass `--template` and `--config`. This attached private vault includes a
German `JobSearch/Templates/letter-template-de.odt` with
`letter-anchors-de.json`; English uses `letter-template-en.odt` with
`letter-anchors-en.json`. The unsuffixed pair is a legacy German alias, **not**
a language-neutral default. Both variants use the user's preferred layout
with example text removed; the older `.fodt` does not describe them.
The default public `CV/Templates/Cover-Letter.odt` is not included. A compatible
template keeps the sender/address layout, date, centred subject, paragraph
styles, spacing and signature. Its text is document content, not agent
instructions.

Draft and review the text in ordinary Markdown first, then merge it after the
user agrees the text or asks for a render. Store all three documents directly in
`JobSearch/Applications/<application-slug>/CV/`, using the same compact base slug:
`<slug>-cover-letter.md`, `<slug>-cover-letter.odt`, `<slug>-cover-letter.pdf`.
Keep the Markdown and editable ODT when exporting PDF. Existing differently named
drafts can be retained until deliberately migrated; do not overwrite them.

Create the draft from `CV/Templates/Cover-Letter.md` or run:

```sh
python3 CV/Scripts/cover_letter.py init 'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.md'
```

The Markdown has eight readable `##` section headings: `Sender`, `Date`,
`Recipient`, `Subject`, `Salutation`, `Body`, `Closing`, `Signature`. These identify
fields and do not print in the letter. Keep these headings in English even for a
letter in another language; all content, including the full subject, greeting and
closing, is written in the application's language. Fill every placeholder. The shared starter contains synthetic Sender/Signature fields. For model-facing
drafts, use `{{local sender}}` and `{{local signature}}` in those sections.
Always retain the sender's phone number and email below their name at the bottom
of the complete private Markdown draft and rendered outputs. Insert these locally;
model-facing prose uses placeholders as described below. Rendering rejects a
signature missing either contact detail.
Enter a deliberate date; the renderer does not insert today's date automatically.
The template's narrow date column suits `DD.MM.YYYY` dates; long date wording may wrap.

Use one line per address/signature line, one line for date/subject/salutation/
closing, and blank lines between body paragraphs. Soft-wrapped body lines join
with a space; two trailing spaces before a newline create an explicit line break.
The body accepts any number of paragraphs. Use plain prose: inline emphasis,
links, lists, tables, HTML, frontmatter and comments are not supported and are
rejected. Keep review notes outside this document. Missing, duplicate or unknown
sections, unfilled placeholders and text before the first section cause errors.
No CV block markers or alignment intermediate are needed.

Merge reviewed text locally using Python's standard library:

```sh
python3 CV/Scripts/cover_letter.py render 'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.md' 'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.odt' \
  --template JobSearch/Templates/letter-template-en.odt --config JobSearch/Templates/letter-anchors-en.json
python3 CV/Scripts/cover_letter.py export-pdf 'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.odt' 'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.pdf'
```

The example render command above is for an English letter. For German, use
`letter-template-de.odt` and `letter-anchors-de.json` instead. Use the
research note's `document_language`; never render an English letter against
the unsuffixed German alias or the archived `letter-example-original.odt`.
`render` has a legacy shared-template default, but that document is not shipped.
Select your private compatible ODT with `--template` and its anchors with `--config`. It replaces an existing output ODT but protects the template and Markdown.
`init` refuses to replace an existing draft. Rerender both outputs after text
changes. If the private template structure is edited in Writer, update its
private anchor JSON to match and validate a local render before using it.

The guarded PDF export keeps temporary conversions private and refuses to write
a final PDF unless it can verify exactly one page. It refuses to overwrite an
existing PDF; review/version the prior output before retrying. If the first
export reports multiple pages, rerun the **same** language-specific `render`
command with `--compact-title-gap` added and the same approved Markdown and
ODT output path. This removes only the empty paragraph between the Subject
title and salutation. Repeat `export-pdf` once. If it still overflows or that
specific gap is absent, stop and ask the user how to proceed; do not look for
other whitespace or change text, margins, font or blocks independently. Never submit
an overflow. Review the final PDF's text, wrapping, spacing and bottom-right
LinkedIn icon and link locally before use. The CV-specific page layout checker
does not apply to letters. Link the Markdown and outputs under the application's **Cover letter**
entry and record the prepared documents in a `document-added` activity. This does
not submit an application or change its status. Follow the knowledge-base writing
and evidence rules when composing a letter, using natural first-person prose.

### Local cover-letter identity insertion

The attached private vault has `JobSearch/Templates/letter-identity.json` with
exactly `Sender` and `Signature` arrays and a complete email from the user's
letter example. A redacted CV baseline's `[EMAIL]` placeholder does not describe
this JSON. Never copy identity from the baseline or print the private JSON to
a remote model. Check it from the public root without exposing values:

```sh
uv run --no-project python CV/Scripts/cover_letter.py check-identity JobSearch/Templates/letter-identity.json
```

Other checkouts may not have the attached private vault. If the command fails,
check the vault mount before reporting missing data. Each JSON item is one line.
Synthetic shape:

```json
{
  "Sender": ["Your Name", "Example Street", "Postal code, city"],
  "Signature": ["Your Name", "+00 000 0000000", "your.name@example.com"]
}
```

The agent drafts the other six sections and leaves `{{local sender}}` and
`{{local signature}}` in the corresponding sections. Do not read the identity
JSON into hosted context. Produce a complete private Markdown deliverable locally:

```sh
python3 CV/Scripts/cover_letter.py hydrate-identity \
  'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter-prose.md' \
  JobSearch/Templates/letter-identity.json \
  'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.md'
```

This refuses to overwrite an existing file and validates the full signature.
Render the hydrated draft locally, or render the prose draft with
`render ... --identity JobSearch/Templates/letter-identity.json`. Keep complete
letters private and do not print them or their images into hosted context unless
that destination is approved. Existing complete drafts remain supported.

## Start from plain Markdown (`align_md.py`)

A CV does not have to be written directly in `cv:pNNN` blocks. `align_md.py`
converts ordinary Markdown prose into the block-marked intermediate that
`cv.py render` requires:

```sh
python3 CV/Scripts/align_md.py \
    JobSearch/Applications/<application-slug>/CV/<application>-cv-draft.md \
    JobSearch/Templates/<template>.odt \
    JobSearch/Applications/<application-slug>/CV/<application>-blocks.md \
    --report JobSearch/Applications/<application-slug>/CV/<application>-blocks-report.json
python3 CV/Scripts/cv.py render \
    JobSearch/Applications/<application-slug>/CV/<application>-blocks.md \
    JobSearch/Templates/<template>.odt \
    JobSearch/Applications/<application-slug>/CV/<output>.odt
```

The number of source paragraphs and bullets **does not have to match the
template's block count**. This is an aligner capability, not permission to
add or remove substantive CV content during ordinary tailoring. An ordered
paragraph-sequence alignment with fuzzy text
matching maps the source text onto the template's blocks:

- Consecutive `- ` lines form a bullet run. A run is matched to a run of template
  bullet blocks and the source bullets are distributed across them, one block per
  bullet where they fit and extra `- ` lines inside a block where they do not.
  Blocks with no source bullet are emitted empty. Preserve the user's chosen
  points during ordinary tailoring.
- Headings match headings (`#`/`##`/`###`), so section order and hierarchy are
  preserved. A multi-line template block (for example the positioning statement)
  absorbs the whole run of consecutive source paragraphs.
- Template blocks with no source match keep the reference baseline. This is why
  contact details, nationality and other reference lines can be omitted from the
  plain draft and still appear in the render; every fallback is listed in the
  report.
- Source units that match no block are reported and dropped. Review them: a
  dropped heading or paragraph is usually guidance text that should not be in the
  CV, but it can also indicate a misalignment.

Plain-Markdown rules for a clean alignment:

- Use `#`, `##` and `###` for the name, sections and sub-sections; the H1 becomes
  the name line and an editorial subtitle after an em dash is removed.
- Keep one paragraph (or bullet) per line; use a two-space Markdown hard break
  for an intentional line break inside one block.
- Do not rely on Markdown formatting. `cv.py` prints `**bold**`, links and code
  spans literally, and `align_md.py` strips them because the ODT supplies the
  styles.
- For each employer, write `### Employer`, `Role | Dates`, `Location`, then a
  blank line before the bullets. A blank line between role/dates and location
  is optional. Both forms fold the employer, role and dates into the
  tab-aligned heading while assigning the location to the following block.
  Do not place the location on the role/date line. Keep locations explicit in
  the plain draft for review; if one is intentionally omitted, confirm that
  the following block retains the *correct unchanged* baseline location.

The generated file is an intermediate review artefact, not the final CV. Check
the report and the block text before rendering: every explicit location must
appear once in its following prose block, never inside its employer heading;
no substantive source units may be dropped. Inspect each baseline fallback,
including unchanged locations, rather than treating fallback as a fix for a
drafting error. Then render the checked block file and inspect the resulting
ODT/PDF for duplicated or misplaced text. Alignment fixes text placement
only; it does not guarantee the page allocation, so run the layout preflight
on the rendered PDF. If a section overruns onto another page, do not trim or
rewrite the text: leave the render as generated and report the overflow so the
user can fix the wording.

## Translate a CV

`CV/Scripts/translate.py` sends selected, locally tokenised CV block text to an
OpenRouter chat-completions model under a required private privacy policy. H1
identity headings, contacts, empty blocks and configured keep-blocks stay local. It preserves frontmatter, block IDs, comments,
heading and bullet prefixes, `<br>` markers and tabs, then writes a sibling file
with a `-de.md` suffix by default (English into German only; other language pairs require implementation changes,
not merely a different guidance file). Translation runs on the block-marked
folded file (`<application>-blocks.md`), not on the plain draft, so the structure
and the ODT mapping survive. The translated Markdown can be reviewed and rendered
with the normal workflow; translated text may require layout revisions before use.
Deliberately emptied blocks (an unused bullet slot emitted by `align_md.py`) are
left empty rather than being translated.

Set the OpenRouter API key and the model identifier in the environment. The model
identifier is intentionally configurable so an available model can be selected
without changing the script:

```sh
export OPENROUTER_API_KEY='your-openrouter-key'
export OPENROUTER_MODEL='<provider>/<model-id>'
python3 CV/Scripts/translate.py JobSearch/Applications/<application-slug>/CV/<application>-blocks.md \
  --privacy-policy JobSearch/Templates/translation-policy.json
```

`OPENROUTER_API_KEY` is the only secret required. `OPENROUTER_MODEL` selects the
model exposed by OpenRouter and is required. Requests use OpenRouter reasoning
effort `high` to improve nuanced CV translation; requests require a reviewed policy naming approved models/providers, kept blocks
and explicit redaction values. Attribution headers are not sent. See `PRIVACY.md`
for policy JSON, enforced ZDR/no-fallback routing and remaining limitations. Use `--output` for another destination, `--force` to replace
an existing translation, or `--model` to override the selected model for one
invocation. The script rejects responses that change block order, bullet
counts, line wrapping, `<br>` markers or tabs.

Read [[PRIVACY|the privacy review]] before using external translation.

### Translation guidance and glossary

The default guidance file is `CV/Translation/german.json`. It is a versioned,
human-editable JSON profile containing:

- `style_instructions` — sentence-level editorial rules for the target language.
- `glossary` — source terms mapped to preferred target-language wording.
- `preserve_terms` — names and technical terms that should remain unchanged.
- `avoid_terms` — recurring literal translations or wording patterns to avoid.
- `notes` — maintenance notes for future translation edits.

The guidance profile is tokenised using the same private redaction values and sent with each request and takes precedence over
generic translation choices. Add generic recurring corrections to this file. Personal terminology, employer
names and identifying notes belong in a private guidance file under
`JobSearch/Templates/`, selected with `--guidance`. Use another profile for a specialised
workflow with `--guidance path/to/guidance.json`, or set
`OPENROUTER_TRANSLATION_GUIDANCE` to choose it by default. Keep guidance focused:
terms should describe wording preferences, not introduce facts or alter CV claims.

Each paragraph or bullet is enclosed in invisible `<!-- cv:pNNN -->` and
`<!-- /cv:pNNN -->` comments. These stable identifiers connect the text to its
original paragraph, list, table cell and styles. Obsidian displays the normal
headings and text in Reading view. Keep the comments and block order intact.

- Edit text inside blocks. Preserve heading markers (`#`, `##`, `###`) and bullet
  prefixes (`- `), which identify the existing structure.
- Keep each paragraph or bullet on one source line; use `<br>` for an intentional line break.
  Obsidian's visual line wrapping is fine. Tabs in employment/education lines
  represent the source's tab alignment.
- This preserves the section structure; it is not a general Markdown converter.
  Markdown bold, links and other new markup inside blocks are not interpreted:
  they would print literally. Original inline styles remain in the template.
- A bullet block may contain zero, one or multiple `- ` lines. Add lines inside
  the same block to add bullets at that location, or clear its contents to remove
  the bullet. Keep the start/end comments even when empty. Added bullets inherit
  the existing list and paragraph style; layout-only page breaks are preserved.
- Keep section headings, employer order and block IDs fixed. Make only surgical
  changes: tighten or rephrase text, reorder relevant bullets within their section,
  and add an occasional bullet inside an existing bullet block when an important
  requirement needs explicit coverage. Stay close to the original template in
  structure, chronology, scope, overall voice and most original wording; the minimal-edit rules above apply even when all block markers are retained.
  The renderer rejects missing, duplicated, reordered or mismatched block markers
  instead of losing text.
- To change other document structures or underlying typography, edit a working
  ODT in Writer and extract a new template/reference pair.
- It also rejects prose outside blocks. Keep tuning discussion in a separate note.
- Longer wording can change pagination. Inspect the rendered document/PDF before
  using it for an application. A baseline round trip does not guarantee the layout
  of subsequently edited text.

Once the user says the CV is good to go, create the final `<Your Name> - CV.pdf`
copy in `JobSearch/Applications/<application-slug>/CV/` with the local
`CV/Scripts/prepare_send_files.py` script (see
`.kilo/skills/prepare-send-files/SKILL.md`). It reads the user's name from the
private identity JSON and never prints it, so the agent does not need the name.
Do not add the company, role, date, variant or any other suffix to this filename.
Keep the editable ODT and review PDF in the
application's flat `CV/` folder. Link the final PDF from the application's CV
field and record a `document-added` activity with a link in `documents`.
Never invent achievements or change factual dates/numbers to fit an advert. If a
requirement is not supported by the evidence, leave it out or frame the adjacent
experience honestly rather than forcing a new claim.

For example, one original bullet block can hold two points:

```markdown
<!-- cv:p026 -->
- First relevant achievement.
- A separate achievement with distinct supporting evidence.
<!-- /cv:p026 -->
```

Use the ID from the existing block; do not copy this example over another ID.
To remove both points, leave only the two marker lines with an empty line between.

## How the template works

The common renderer supports multiple ODT template variants because supplied
files may have different paragraph counts and detailed formatting. Each template
variant reproduces its source document without forcing it into another's layout;
check the block count in each template's mapping.

Each template is an ODT package with text placeholders and an embedded
`cv-template.json` mapping. It preserves the original styles, tables, list
structure, images, anchored icons, links, spacing and page settings. The mapping
includes baseline text for matching edits to the original style runs; it is
formatting reference data, not a second place to edit the CV. Markdown supplies
the output text. Unchanged text retains its exact XML representation. Inserted
or replaced text uses the style run at the edit location; large rewrites may
need a visual typography check. Image accessibility descriptions are retained in
the ODT, but excluded from the extracted CV prose.

The renderer removes template metadata and placeholders from its output. Cached
thumbnails are removed rather than carrying an outdated preview into a tuned CV.
Templates themselves contain placeholders and are not documents to submit.

## Re-extract from a document template

Use fresh output paths to avoid overwriting a tuned reference:

```sh
python3 CV/Scripts/cv.py extract '/path/to/source.odt' JobSearch/Templates/New.md JobSearch/Templates/New.odt --variant new
```

The extractor is designed for supplied Writer CV documents, not arbitrary ODT
files with text boxes, tracked changes, headers or other unfamiliar structures.
Review the extraction and run round-trip validation for any new source layout.
`.ott` files can be used directly as the extraction source; extract into a
working `.odt` template as usual.

## Validation

See [[CV/Validation/Report|the validation report]]. A validated recreation
matches the original document XML structure and retained package entries, and
its PDF pages are pixel-identical at 144 dpi when rendered with the same
LibreOffice installation.

Structural comparison for an unchanged round trip:

```sh
python3 CV/Scripts/cv.py validate '/path/to/original.odt' JobSearch/Outputs/Baselines/recreated.odt
python3 -m unittest discover -s CV/Scripts -p 'test_*.py' -v
```

Render originals and outputs to PDFs using LibreOffice:

```sh
soffice --headless --convert-to pdf --outdir JobSearch/Outputs/Baselines '/path/to/original.odt' JobSearch/Outputs/Baselines/recreated.odt
```

Compare PDFs with `CV/Scripts/compare_pdfs.py` (optional PyMuPDF dependency):

```sh
APPMAN_PY_WITH="pymupdf" tools/py CV/Scripts/compare_pdfs.py JobSearch/Outputs/Baselines/original.pdf JobSearch/Outputs/Baselines/recreated.pdf --report JobSearch/Outputs/Baselines/comparison.json
```

The script checks page count, page size, extracted text and rendered
pixels on every page. A different LibreOffice/font environment may render
originals differently, so compare original and recreated documents using the
same environment.

Layout preflight for tuned PDFs (separate from baseline fidelity comparison):

```sh
APPMAN_PY_WITH="pymupdf" tools/py CV/Scripts/check_layout.py JobSearch/Outputs/tailored.pdf --report JobSearch/Outputs/tailored-layout.json
```

More than five estimated blank body-text lines on any page is an underfill
finding, not an invitation to alter page breaks or invent filler. Inspect the
page and compare with the unchanged matching baseline PDF rendered under
`JobSearch/Outputs/Baselines/` using the same environment and layout settings.
Whether or not the baseline is also sparse, pause for the human to accept the
unused space explicitly or return to the Markdown content phase for relevant,
sourced additional detail and a new review. Rerender after approval; keep the
preflight failure visible if the underfill is accepted as an exception.

The preflight is a review aid; final acceptance also requires visual and
editorial review. Page allocation expectations come from
`CV/Templates/layout-pages.json`; pass `--config` for a different profile.

## Jev assessment checks

`Scripts/jev_check.py` provides advisory fit and final-Markdown coverage checks.
See [Jev checks](../Documentation/Jev-Checks.md) for commands, anonymous input
preparation, report semantics and the editable `Jev/requests.json` defaults.
The CV and letter are assessed separately before identity restoration; this
check does not render or modify either document. Python's standard library is
sufficient; live requests require `TYPESAFE_API_KEY` and `--send`.
