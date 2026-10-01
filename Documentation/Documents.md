# Prepare CVs and cover letters

[Home](../README.md) · [Setup](Getting-Started.md) · [Applications](Applications.md)

Start from your own factual CV, make a small number of changes for the role,
review the wording, then render and inspect the document. Do not ask the assistant
to manufacture a new career narrative from the advert.

You need Python for the scripts and LibreOffice Writer for layouts/PDFs.
OpenRouter is optional and only used by the supplied translation script.
All commands below run from the JobJimmy root. Keep personal inputs and outputs
under `JobSearch/`.

## Choose a document approach

| Approach | Choose it when | What you supply |
| --- | --- | --- |
| A. Personal master from the included blank template | You want to use the project's supplied CV layout | A completed personal master ODT and a baseline body Markdown |
| B. Extract your existing Writer CV | Keeping your current CV's wording and layout is important | Your source ODT; extraction creates a matching Markdown/template pair |
| Manual Writer editing | Your layout is complex or you do not want to configure automation | Your own document, with reviewed text inserted manually |

These are different input formats. Do not pass a block-marked reference to the
personal-master populator, or a body-only draft to the block renderer.
No personal baselines are distributed with JobJimmy. The current import skill uses
`Manager` and `VP-CTO` as baseline names, not as documents supplied by the project.
Every user must supply their own ODT CV source with the basic layout and
substantive content they require, then extract the matching Markdown and ODT
pair. This private vault already has a VP/CTO/Director variant and an
engineering manager/team lead variant. Agents may tweak wording and reorder
existing bullets within their sections, not fundamentally rewrite the CV or
change its layout. The included blank `.ott` is an optional starting layout,
not a replacement for a user-supplied content baseline.
Record your actual setup in `JobSearch/Knowledge/CV-positioning.md`; missing
baselines must be reported rather than silently invented. For a different naming
or rendering arrangement, explicitly instruct the assistant which reference and
workflow to use. That setup is not automatically inferred.

## A. Use the included layout

1. Open `CV/Templates/CV Template.ott` in LibreOffice Writer.
2. Immediately save the personal document as
   `JobSearch/Templates/personal-master.odt`. Never put your details in the public
   `.ott` or overwrite it.
3. Follow the [personal template walkthrough](CV-Automation-User-Template-Setup.md)
   to enter identity/contact information and permanent sections. Leave the
   automation tokens and bookmarks intact.
4. Prepare a baseline body Markdown from your existing CV, using the structure
   below. Store the baseline privately and preserve it; tailor a copy per role.

This abbreviated example shows the format only; its content is synthetic and not
a useful CV. The two expertise subheadings and the three main headings are
required. Each role has Company, Title, Dates and Location fields.

```markdown
---
taglines:
  - "Engineering Leadership"
  - "Product Delivery"
---

# Profile

A factual overview from the candidate's own baseline.

# Expertise and Achievements

## Leadership

- An evidence-supported leadership achievement.

## Delivery

- An evidence-supported delivery achievement.

# Work Experience

## Role 01

Company: Example Company
Title: Engineering Lead
Dates: January 2020 - December 2024
Location: Example City

- An accurate account of the candidate's contribution and outcome.
```

Save a reviewed working copy as `JobSearch/Outputs/cv-body.md` for a first local
trial. To populate an editable ODT and export PDF:

```sh
python3 CV/Scripts/populate_cv.py \
  JobSearch/Outputs/cv-body.md \
  JobSearch/Templates/personal-master.odt \
  JobSearch/Outputs/cv-preview.odt --pdf
```

Use the application's own `CV/` folder for real application documents. The command
keeps the master unchanged. It reports length warnings; do not treat a generated
file as evidence of a good layout. The supplied layout targets three pages;
substantial layout changes require corresponding validation changes.

The [population contract](../CV/Templates/CV-Template-Population-Agent-Instructions.md)
describes full input rules, tokens and layout constraints. If automatic PDF export
cannot find LibreOffice, open the ODT in Writer and export manually.

## B. Keep your existing Writer CV

Save your source as `JobSearch/Templates/source.odt`. DOCX/PDF inputs are not
directly supported by the extractor; prepare and visually review an ODT in Writer
first. Keep your original untouched.

Extract a baseline and matching template:

```sh
python3 CV/Scripts/cv.py extract \
  JobSearch/Templates/source.odt \
  JobSearch/Templates/Manager.md \
  JobSearch/Templates/Manager.odt --variant manager
```

`Manager` is the filename used in this example and one of the import skill's
expected baseline names. Choose the baseline appropriate to your actual role.
Extraction is designed for paragraph/list/table-based Writer CVs; text boxes,
tracked changes and unfamiliar structures may need adaptation.

Before tailoring anything, check an unchanged round trip:

```sh
python3 CV/Scripts/cv.py render \
  JobSearch/Templates/Manager.md \
  JobSearch/Templates/Manager.odt \
  JobSearch/Outputs/baseline-check.odt
python3 CV/Scripts/cv.py validate \
  JobSearch/Templates/source.odt \
  JobSearch/Outputs/baseline-check.odt
```

Also open the source and recreated ODT in Writer, export both to PDF, and compare
every page. Structural validation does not prove visual fidelity. Do not rely on
a new template until you have checked it.

## Tailor for an application

> Use my chosen baseline and this application's advert to prepare a plain
> Markdown CV draft. Preserve the baseline's wording except where a specific
> requirement warrants a supported change. List each targeted change and its
> evidence. Decide the language from the advert and application instructions.
> Do not render yet.

For agents, follow `.kilo/skills/tailor-cv/SKILL.md` step by step. Store the
draft in the application's `CV/` folder. Review factual claims, tone,
language and chronology before approving it. A request to tailor does not mean
rewriting every bullet or changing identity/permanent sections.

For approach A, render the accepted body draft with `populate_cv.py` as above.
For approach B, map a plain draft back onto the chosen extracted template with
`align_md.py`, then render. The following paths illustrate a fictional application;
replace the slug with your existing application folder:

```sh
python3 CV/Scripts/align_md.py \
  JobSearch/Applications/2026-09-example-lead/CV/example-cv-draft.md \
  JobSearch/Templates/Manager.odt \
  JobSearch/Applications/2026-09-example-lead/CV/example-blocks.md \
  --report JobSearch/Applications/2026-09-example-lead/CV/example-blocks-report.json
```

Review the report before continuing. Unmatched source text can be dropped;
unmatched template content can retain baseline wording. Resolve any unintended
omission or fallback, then:

```sh
python3 CV/Scripts/cv.py render \
  JobSearch/Applications/2026-09-example-lead/CV/example-blocks.md \
  JobSearch/Templates/Manager.odt \
  JobSearch/Applications/2026-09-example-lead/CV/example-cv.odt
```

Export in Writer, or with LibreOffice on your PATH:

```sh
soffice --headless --convert-to pdf \
  --outdir JobSearch/Applications/2026-09-example-lead/CV \
  JobSearch/Applications/2026-09-example-lead/CV/example-cv.odt
```

On macOS, the executable is commonly
`/Applications/LibreOffice.app/Contents/MacOS/soffice`; use that quoted path if
`soffice` is not on PATH. Automatic discovery in `populate_cv.py` checks that path.

## Change the layout safely

Work on a new private template version. Change fonts, spacing, margins and styles
in Writer, then generate a trial with realistic text and inspect every page.
For approach A, preserve the tokens/bookmarks and role prototypes; removing them
breaks the merge contract. The identity setup walkthrough deliberately preserves
the supplied layout and is not a general-purpose layout designer.

For approach B, make structural layout changes in the source ODT and extract a
new reference/template pair. Keep each reference paired with its own template;
do not mix baselines or reuse old alignment reports after changing structure.

The public `layout-pages.json` contains synthetic employer headings. Copy it to
`JobSearch/Templates/layout-pages.json` and change the expected sections/page
allocation privately before using automatic checks:

```sh
JOBJIMMY_PY_WITH="pymupdf" tools/py CV/Scripts/check_layout.py \
  JobSearch/Outputs/cv-preview.pdf \
  --config JobSearch/Templates/layout-pages.json \
  --report JobSearch/Outputs/cv-layout.json
```

This needs PyMuPDF and a configuration matching your actual layout. It supplements
visual review; it does not prove readability. If text overflows, revise it yourself
or approve a specific change. The assistant should not silently shorten approved
wording to force a page count.

## Write a cover letter

> Draft a cover letter for this application, using my strongest relevant evidence
> and sourced company research. Use the application's language and natural
> first-person prose. Leave identity fields for local insertion. Do not render
> or send it yet.

Use the eight-section [Markdown starter](../CV/Templates/Cover-Letter.md).
The `init` command copies it into a private file:

```sh
python3 CV/Scripts/cover_letter.py init JobSearch/Outputs/letter-prose.md
```

Complete Date, Recipient, Subject, Salutation, Body and Closing. For the
model-facing draft, put `{{local sender}}` in Sender and `{{local signature}}` in
Signature. Create your private identity JSON locally using the format in the
[technical reference](../CV/README.md#local-cover-letter-identity-insertion).
Do not paste that JSON into a hosted assistant. Assemble a complete private draft:

```sh
python3 CV/Scripts/cover_letter.py hydrate-identity \
  JobSearch/Outputs/letter-prose.md \
  JobSearch/Templates/letter-identity.json \
  JobSearch/Outputs/letter.md
```

The signature retains name, phone and email. The source prose remains unchanged.
You can now insert the reviewed text into your own Writer letter and export PDF.

For agents, follow `.kilo/skills/write-cover-letter/SKILL.md` step by step.
**Automatic cover-letter ODT rendering needs a matching private template.**
This attached private vault includes the user's preferred German layout as
`letter-template-de.odt`/`letter-anchors-de.json`, and the matching English
layout as `letter-template-en.odt`/`letter-anchors-en.json`. The identity JSON
has been extracted locally from the user's example. Its original is backed up
privately as `letter-example-original.odt`; do not send it to a remote model.
The older `letter-template.fodt` is not the source of these updated layouts.
For your own layout, supply a private compatible
ODT and matching anchors describing its paragraph positions. Merely renaming an
arbitrary letter is insufficient. See
[template configuration](../CV/Templates/README.md#cover-letter). Then run:

```sh
python3 CV/Scripts/cover_letter.py render \
  JobSearch/Outputs/letter.md JobSearch/Outputs/letter.odt \
  --template JobSearch/Templates/letter-template-en.odt \
  --config JobSearch/Templates/letter-anchors-en.json
```

The example is for `document_language: en` on the linked research note. For
`de`, use `letter-template-de.odt` with `letter-anchors-de.json`. The unsuffixed
`letter-template.odt` / `letter-anchors.json` is only a German alias, not the
default for other languages. Keep the ODT and anchor file paired; neither contains the
example's original letter prose or identity.

Export through the guarded command, not an unchecked Writer conversion:

```sh
uv run --no-project python CV/Scripts/cover_letter.py export-pdf \
  JobSearch/Outputs/letter.odt JobSearch/Outputs/letter.pdf
```

This creates a final PDF only if it can verify exactly one page. On overflow,
retry **once** by rerunning the original language-specific `render` command
with `--compact-title-gap`, the same Markdown and the same ODT path, then repeat
`export-pdf`. That flag removes only the empty paragraph between Subject and
salutation. If the retry still overflows or the gap is absent, stop and ask the
user how to proceed; do not explore other spacing or edit the wording yourself.
Check that the linked icon survives in the bottom-right
corner. The exporter refuses to overwrite an existing PDF.

If no compatible private letter template is available, use manual Writer
assembly. Keep the final Markdown, ODT and PDF in the application's `CV/`
folder, link them from the application and record a `document-added` activity.

## Optional: English-to-German CV translation

This script translates the **block-marked CV format from approach B**. It does
not directly accept approach A's body format or cover-letter Markdown. Other
language pairs are not implemented as selectable options; they require code and
guidance changes. Do not assume a guidance file alone changes the target language.

1. Create an OpenRouter account and API key following the
   [official quickstart](https://openrouter.ai/docs/quickstart). Usage has costs;
   check model/provider pricing and set suitable account limits.
2. Verify account logging, retention and provider controls using
   [the privacy guide](../PRIVACY.md). An API key is not evidence of privacy approval.
3. Create a private `JobSearch/Templates/translation-policy.json` listing reviewed
   model/provider IDs, kept block IDs and explicit redaction values. The exact
   schema and its limitations are in [PRIVACY.md](../PRIVACY.md#translation-implemented-safeguards).
4. Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in the terminal environment.
   Use your secret manager or a non-echoing prompt for the key; never commit it,
   paste it into chat or put it in a command saved to shell history.
5. Run on a reviewed block-marked file, for example:

```sh
python3 CV/Scripts/translate.py \
  JobSearch/Applications/2026-09-example-lead/CV/example-blocks.md \
  --privacy-policy JobSearch/Templates/translation-policy.json
```

It creates `example-blocks-de.md` alongside the source. Review it before rendering
with the matching template. Identity/contact blocks stay local; selected values
are tokenised and restored. Other career text still reaches the external provider.
Missing policy, forbidden routes or damaged tokens should fail rather than relax
privacy. No compliant route available means use another approved route or a local
workflow—not disable the safeguards.

## Jev coverage check before rendering

When final Markdown wording is ready, the assistant checks the CV and cover letter
**individually** with Jev using anonymous text, the anonymous job description and
the required-points checklist. It shows each document's match score, confidence,
and partial/missing/unclear answers before wording approval and local identity
insertion. Results stay in separate reports and document activities. A substantive
revision requires a new check. The results support review; they do not approve
wording or verify career claims. See [Jev checks](Jev-Checks.md) for setup,
editable default requests, exact commands and unavailable-check handling.

## Before using the documents

Check all pages, links, dates, text extraction and contact details locally. Keep
editable ODTs as well as PDFs. Final acceptance is a human decision; a successful
script run does not mean the document is ready. A hosted model viewing PDF images
is another personal-data transfer.

Preparing documents does not submit an application. Return to
[Applications](Applications.md#record-a-submission) after you have actually sent it.
