# Plan: two-phase CV workflow + flat per-application CV folders

## Goal

Two related changes to how application CVs are produced and stored:

1. **Draft first in plain Markdown, fold second.** Write and review the CV text
   in a pure, human-readable Markdown draft, then fold the finished text into
   the block-marked (`cv:pNNN`) structure that carries paragraph/ODT formatting,
   then render. The plain draft's structural Markdown (headings, paragraph
   breaks, bullet lists, line grouping) is the mapping guide onto template
   paragraphs — there are no explicit per-paragraph markers in the draft.
2. **Flat per-application CV folders.** Each `Applications/<slug>/CV/` holds all
   its CV data directly, with no `Rendered/` or `Validation/` sub-folders: source
   Markdown, intermediate/folded Markdown, ODT, PDF and reports sit together.
   This applies **only to the per-application CV data folders**. The top-level
   `CV/` workspace (`References`, `Templates`, `Scripts`, `Knowledge`, `Rendered`,
   `Validation`, `Translation`) is unchanged.

## Part 1 — two-phase workflow

| Phase | File | Purpose |
| --- | --- | --- |
| 1. Draft | `Applications/<slug>/CV/<application>-cv-draft.md` | Fully plain, human-readable Markdown. Reviewed and revised with the user. No `cv:pNNN` markers, no ODT/PDF. |
| 2. Fold | `Applications/<slug>/CV/<application>-blocks.md` | Block-marked intermediate produced from the plain draft by `CV/Scripts/align_md.py`, reviewed before rendering. For older records the equivalent render-ready file is `<application>.md`. |

- The fold step uses `CV/Scripts/align_md.py` with the chosen template; review
  the alignment report; unmatched template blocks keep the reference baseline
  and unmatched source units are reported and dropped.
- `cv.py render` rejects missing, duplicated, reordered or mismatched blocks,
  which is the guardrail for the fold result.
- Language rule: determine the document language from the advert, translate
  faithfully with `CV/Scripts/translate.py` when required, and keep the tailored
  source Markdown for comparison.

## Part 2 — flat application CV folders

- Application CV filenames use compact slugs of the form `YYYY-MM-company-position`
  (about 30 characters) with short artifact suffixes (`-draft`, `-blocks`, `-de`,
  `-proposed`, `-review`, `-layout`).
- In the flat folders, source Markdown and the final ODT/PDF are tracked; JSON
  reports and `-proposed`/`-preview`/`-review`/`-test` renders are ignored by Git
  and regenerated on demand.
- `.gitignore` rules for `/Applications/*/CV/*-blocks-report.json`, `*-layout.json`,
  `*-comparison.json`, `*-proposed.*`, `*-preview.*`, `*-review.*`, `*-test.*`
  implement this; drafts, references, knowledge, scripts and templates stay tracked.
  (2026-09-22: superseded — the private data lives in the `JobSearch/`
  repository mount; equivalent rules live in the private repository's own
  `.gitignore`.)
