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
  `JobSearch/Outputs/safe/<slug>/` (always including the voice guides
  `Writing-guide.md` and `Reasoning-profile.md`, and recording the baseline
  names), and `restore` brings the model's drafts back from its `out/` folder,
  refusing drafts the user changed since the bundle. For a source CV draft,
  `restore` runs the **tailoring check**: it compares the safe draft with the
  bundled safe baseline (front matter, block markers and the employer-header
  split ignored) and prints counts only (content blocks changed, bullets
  moved, baseline blocks removed), with a warning when changed blocks plus
  moved bullets are fewer than three. `render --cv` repeats the check against
  the private baseline as a warning line. `render` chains `align_md.py`, `cv.py`, the PDF export and
  `check_layout.py` (compared with the unchanged baseline's PDF in
  `JobSearch/Outputs/Baselines/`) for the CV, and hydration, rendering and the
  one-page export of `cover_letter.py` for the letter.
- **Agents**: Kilo Code runs the session on a fixed, inexpensive model
  (`kilo.jsonc`, Claude Haiku 5.5), which follows the skills in
  `.kilo/skills/` and runs the `jobflow.py` steps. The **Writer**
  (`.kilo/agents/writer.md`, `mode: subagent`, Claude Opus 5.5 through
  OpenRouter) is a Kilo subagent whose objective is natural, evidence-backed
  document text: it drafts one cover letter's prose or one CV tailoring per
  call from the safe bundle, writes the draft (and for a CV a tailoring change
  list, `<prefix>-cv-tailoring.md`) into the bundle's `out/` folder, and
  reports counts and gaps. Its permissions allow reading only the safe bundle
  and the public style guide and letter starter, writing only into `out/`, and
  deny shell, web and further delegation. It never sees the token registry or
  restored text; the session agent restores, checks and renders.
- **Prose model comparison**: `CV/Scripts/prose_compare.py` sends the
  Writer's exact request (its brief as the system message, the calling
  agent's task message, and the bundle files inline because the run has no
  file tools) to every model listed in `PROSE_COMPARE_MODELS` in `.env`, in
  parallel through OpenRouter with zero data retention required. It accepts
  only a safe bundle or a safe file, scans the input with the private policy
  before sending, and writes the drafts blind (`A.md`, `B.md`, ...) with
  `REVIEW.md`, `key.json` (label → model, tokens, cost, time) and
  `request.json` to `JobSearch/Outputs/model-compare/<time>/`. The console
  shows figures only, never draft text.
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
bundle` → `JobSearch/Outputs/safe/<slug>/` (safe copies) → the Writer
subagent → its drafts (and CV tailoring notes) in `out/` → `jobflow.py
restore` (plus the tailoring counts for a CV) →
`JobSearch/Applications/<slug>/CV/`. The tailoring notes stay in `out/`.
Approved drafts → `jobflow.py render` → ODT and PDF beside them.

**Model comparison.** A safe bundle → `prose_compare.py` (privacy scan) →
OpenRouter, one identical request per model → blind drafts, review sheet and
model key in `JobSearch/Outputs/model-compare/<time>/` (mode 0700/0600).
Nothing is restored automatically.
