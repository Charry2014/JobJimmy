# 260921-cvgen Architecture Reference

One document for people who want to understand 260921-cvgen without reading
the code. The rules for it are in `~/.config/agents/rules/DOCUMENTATION.md`.
A change that alters anything described here updates this document in the
same change.

Contents: [[#Purpose]] · [[#How it works]] · [[#Interfaces to other projects]] · [[#Key components]] · [[#Internal interfaces]] · [[#Data flows]]

## Purpose

<!-- What the project aims to do, for whom, and what it deliberately leaves out. -->

## How it works

<!-- The mechanism from input to outcome in a few paragraphs; a diagram where one explains more than prose. -->

## Interfaces to other projects

<!-- Every project, service or tool this one calls or is called by: what crosses each boundary and in which direction. -->

- **LibreOffice (`soffice`)**, called headless to export rendered ODTs to PDF.
  ODT paths go in, PDFs come out. Every call goes through
  `CV/Scripts/office.py` (directly or via the `tools/soffice` wrapper), which
  sets `FONTCONFIG_FILE` on macOS so headless LibreOffice sees installed fonts
  and the private substitutions in `JobSearch/Templates/fonts.conf`.

## Key components

<!-- The main modules, processes or services: each one's responsibility and where it lives in the code. -->

- **Redaction layer**: `CV/Scripts/redact_md.py` turns private Markdown into
  safe copies with stable `@@LABEL_NN@@` tokens and restores model responses
  locally. It is driven by the private policy
  (`JobSearch/Templates/redaction-policy.json`) and token registry
  (`JobSearch/Templates/redaction-tokens.json`). `jev_check.py` reuses its
  policy and contact checks.
- **Workflow steps**: `CV/Scripts/jobflow.py` runs the routine steps of the
  import and document workflows locally and prints generic status only.
  `capture` takes an advert or recruiter email from the clipboard or a file,
  keeps it verbatim in the private inbox `JobSearch/Outputs/inbox/<id>/`, adds
  the contacts and email-header names it finds to the policy and writes the
  safe copy; `add-name` adds a name the user types locally. `records` creates
  the linked notes from the canonical `Templates/` and archives the captured
  original between `advert:start`/`advert:end` markers; `update` replaces a
  note section or front-matter field from a safe file. `bundle` writes checked
  safe copies of notes, knowledge articles, baselines and drafts to
  `JobSearch/Outputs/safe/<slug>/`, and `restore` brings the model's drafts
  back from its `out/` folder, refusing drafts the user changed since the
  bundle. `render` chains `align_md.py`, `cv.py`, the PDF export and
  `check_layout.py` (compared with the unchanged baseline's PDF in
  `JobSearch/Outputs/Baselines/`) for the CV, and hydration, rendering and the
  one-page export of `cover_letter.py` for the letter.
- **PDF export layer**: `CV/Scripts/office.py` finds LibreOffice and builds
  the font environment; `tools/soffice` is its command-line form. It is used by
  `populate_cv.py --pdf`, `cover_letter.py export-pdf` and the documented CV
  export command.

## Internal interfaces

<!-- How the key components talk to each other: function boundaries, queues, files, protocols, schemas. -->

## Data flows

<!-- The paths the important data takes through the components, from source to sink, including every persistent store. -->

**Advert import.** Clipboard or file → `jobflow.py capture` → private inbox
(original, mode 0600) plus safe copy; new contacts and header names → the
private policy, new tokens → the registry. The model reads the safe copy and
writes a records spec with tokens → `jobflow.py records` restores them →
application, research (with the verbatim original), company and recruiter
notes in `JobSearch/`.

**Drafting.** Notes, knowledge articles, baseline and drafts → `jobflow.py
bundle` → `JobSearch/Outputs/safe/<slug>/` (safe copies) → the model → its
drafts in `out/` → `jobflow.py restore` → `JobSearch/Applications/<slug>/CV/`.
Approved drafts → `jobflow.py render` → ODT and PDF beside them.
