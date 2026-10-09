# Engine handover — 2026-10-09

This snapshot supports a clean agent context. It is a dated state snapshot, not a
procedure: recurring vault actions are specified centrally in
[PROCEDURES.md](PROCEDURES.md). Read [AGENTS.md](AGENTS.md) for
durable instructions and recheck Git status before editing. Keep this file limited to reusable engine work. Personal work state belongs
in `JobSearch/HANDOVER.md`; never name real applications or people here. Application and activity notes remain the source of
truth for each opportunity: this handover is a snapshot, not permission to
submit anything or an instruction to redo completed work.

## Draft files edited in place — 2026-10-09

Both document skills now require every draft/revision to be written to a real
Markdown file in the application's flat `CV/` folder before review. Read the
latest file through the privacy workflow to incorporate Obsidian edits, then
update the same path. Git provides history; no numbered, timestamped or backup
draft copies. English and German remain separate current documents. The letter
hydration instructions replace the previous manual-versioning advice with a
temporary private output followed by replacement at the stable Markdown path.

Validation: both edited skills passed the skill validator; changed-file privacy
screen and `git diff --check` passed. Instructions only; no private drafts changed.

## English review before German translation — 2026-10-09

German applications now prepare both CV and cover letter in English through
evidence, wording and user-feedback rounds before translation. The agreed English
sources remain alongside separate German drafts; `document_language` continues
to describe the final submission language. German wording gets its own review
and per-document Jev checks before rendering. Substantive later changes return
to English first. The shared sequence lives in
`Documentation/Agent-Reference/Documents.md`; language routing, document skills,
import proposals, send-file checks and user guides point to the same stages.
This supersedes the earlier direct-German letter rule and the earlier handover
advice to remove all old-language drafts: retain English working sources.

Validation: all four affected skills passed the skill validator; obsolete
direct-German instructions were checked for conflicts; changed-file and `--all`
privacy screens passed, and `git diff --check` was clean. Documentation/skill
instructions only: no live translation, Jev request or rendering was run.

## Location fit factor — 2026-10-06

Added `CV/Scripts/location_fit.py` (standard library, no network) and its tests.
It compares a role's office coordinates, working model, office days and travel
share against the private `JobSearch/Templates/location-preferences.json` and
prints a verdict (`compatible`/`review`/`unknown`/`incompatible`), with distances
rounded to 5 km and no home values. `--in-accepted-region` turns a commute over
the limit into `review`. The import reference now always includes a Central
**Location and working model** row in the fit table; an `incompatible` verdict
caps fit at 4 unless an exception is accepted. Documented in
`Documentation/Applications.md`, `Documentation/Agent-Reference/Documents.md` and
`Documentation/Dependencies.md`. Corrected the stale `TYPESAFE_API_KEY` reference
in import Step 0 to `OPENROUTER_JEV_API_KEY`. Not yet done: `check_env.py` does
not report whether the preferences file is present.

## Documentation consistency pass — 2026-10-06

Removed the stale `.kilo/worktrees/planet-desk` worktree (its commit was already
in `main`) and the implemented plans `central-action-procedures.md` and
`cv-plain-draft-workflow.md` from `.kilo/plans/`. Layout allocation is now
documented consistently as the private per-baseline
`JobSearch/Templates/<baseline>-layout-pages.json`, with
`CV/Templates/layout-pages.json` as the synthetic default only. Script commands in
the docs and skills now use `tools/py`; `check_layout.py`/`compare_pdfs.py` and
`populate_cv.py --pdf` add `JOBJIMMY_PY_WITH="pymupdf"`, and `translate.py`
adds `certifi`. `.kilo/rules/project.md` now points to
`.kilo/rules/document-language.md`, so the language rules load even if Kilo does
not auto-discover rule files. README calls Kilo Code the primary setup throughout.
Fixed the `privacy_screen.py` help text, which referred to a nonexistent
`--changed` flag. Open: `.kilo/kilo.jsonc` holds only `$schema` and may be
Kilo-generated; it was kept. The `APP_MAN_PRIVATE_<n>_TOKEN` redaction-token
format keeps its legacy name for compatibility.

## Template-location instructions clarified — 2026-10-02

Agents repeatedly "failed to find" the CV baselines and cover-letter ODTs because
`JobSearch/` is gitignored: the `glob`/`grep` tools (and `rg` without
`--no-ignore`) silently return no files there, which reads as "templates are
missing". Added one canonical inventory in root `AGENTS.md` ("Locating CV and
cover-letter templates") plus the gitignore/glob warning, and pointed to it from
`CV/README.md`, `CV/Templates/README.md`, `Documentation/Documents.md`,
`Documentation/Agent-Reference/Documents.md`, both document skills, and the
`JobSearch/Templates/` row of the Files table. Replaced ambiguous "not bundled
with the public project" wording with an explicit public-vs-private distinction:
"not bundled publicly" now states the files exist only in the attached private
vault. Removed the superseded 2026-10-01 knowledge clean-check handover section
and `.kilo/plans/knowledge-base-privacy-clean-check.md`.

Validation: all rendering templates confirmed present under `JobSearch/Templates/`
and valid ODF packages (embedded `cv-template.json` for `VP-CTO`/`Manager`;
`content.xml` for the letter templates and `CV Template.ott`). Letter anchor
`paragraph_count` matches each letter ODT (15/15/15); `letter-identity.json` has
exactly `Sender`/`Signature`; extracted baselines' `cv:pNNN` marker counts equal
their templates (VP-CTO 72, Manager 70). CV suite: 120 tests, OK (25 skipped for
optional private fixtures). Known gap: `Manager` has no
`JobSearch/Templates/Manager-layout-pages.json` (VP-CTO does), so its automated
layout preflight is unavailable; that page-allocation config is private and was
not created. No template binary or private document was changed.

## Hosted drafting and live Jev findings — 2026-10-02

First real application of the full hosted drafting flow (advert, baseline and
knowledge articles via `redact_md.py prepare`/`restore`). Engine findings, all
generic:

- Redaction policies need every case and spacing variant: a title-case value
  does not match an uppercase display heading. Bare company-name stems cause
  substring false positives on ordinary target-language words, so prefer the
  full names that actually occur. Locale words that are part of the user's own
  seeded address (country names and German city exonyms) must be routed through
  tokens in translated drafts, not written literally.
- `redact_md.py restore` can restore authored drafts by pairing the response
  with itself; when a draft mirrors the baseline structure 1:1, the baseline
  body acts as the validation original and catches accidental token loss or
  duplication, with deliberate token substitutions (e.g. localised city forms)
  validated explicitly.
- Live Jev checks on this machine require the certifi CA bundle
  (`JOBJIMMY_PY_WITH="certifi"` plus `SSL_CERT_FILE`); the
  standard-library-only claim holds elsewhere but not for this Python install.
- Live Jev consistency is flaky under repeated load: cover-letter checks
  validated four times in a row, then failed once and validated on retry; a
  CV-sized request failed internal-consistency validation four times before
  validating on the fifth. Both document kinds are therefore live-proven, but
  expect intermittent "Invalid Jev score"/coverage failures — retry
  deliberately, report failures, and never bypass `validate_response` to
  force a score.
- Layout preflights of tailored VP-CTO renders fail with baseline-inherent
  underfill (identical blank-line numbers on pages 1–2, page 3 improved by
  added bullets). The comparison render of the unchanged baseline with the
  same environment/config is the evidence the human needs to accept the
  exception explicitly; keep the preflight failure report in the folder.
- Language corrections after drafting: an explicit user instruction overrides
  the advert-language default. Update the recorded `document_language`, remove
  the superseded drafts instead of keeping both languages, redraft, and run
  document checks on the new language; keep old-language check reports as
  dated history.

## Knowledge model-safety exception retired — 2026-10-02

A local scan (`redact_md.py check JobSearch/Knowledge`) exposed that the curated
knowledge articles were never model-safe: the reviewed policy lists only the
full name and a few strings, while the articles also use the candidate's first
name (166 occurrences across 11 files) and real employer names the policy cannot
discover. Passing the check therefore produced a false "safe" result.

Retired the `JobSearch/Knowledge/**` exception: curated knowledge now follows the
same reversible `redact_md.py prepare`/`restore` workflow as every other private
source before any remote read. `redact_md.py check` is reframed as a local safety
scanner — a pass is not proof of anonymity and does not authorise remote use. No
private article or policy was rewritten.

`tools/privacy_screen.py` now also derives the candidate-name identifier from the
private `Templates/letter-identity.json`, so the public screen no longer depends
on knowledge `subject:` frontmatter. Removed the optional private-vault knowledge
pre-commit hook from the scaffold and updated PRIVACY.md, root AGENTS.md,
`.kilo/rules/project.md`, the document/import/knowledge-base references, and both
vault AGENTS.md copies.

Validation: tools suite 32 tests passed; CV suite 120 tests passed (25 skipped
for absent templates); default and `--all` privacy screens clean (48 identifiers
screened); `git diff --check` clean. Private articles were scanned locally for
counts only; no article content or policy value was read into model context.

## .env fallback for required keys and paths — 2026-10-02

Added `CV/Scripts/env_file.py`, a standard-library loader that reads an optional
`.env` at the repository root when a required variable is unset. Existing
environment values always win, so shell exports and IDE/secret-manager
environments keep precedence; parsing supports comments, blank lines, optional
`export`, single/double quotes with escapes, and inline `#` comments. Wired into
`CV/Scripts/translate.py` and `CV/Scripts/jev_check.py` at CLI start, and into
`tools/check_env.py` so its key report matches what the scripts see; `check_env`
reuses the loader rather than duplicating it. `.env` is now ignored
(anchored `/.env`) and a tracked `.env.example` documents the format without
secrets. OpenRouter setup, Dependencies, CV README and the code all state that
`.env` is a fallback only and never overrides a real export.

Validation: 8 new `test_env_file.py` tests passed; full CV suite 120 tests passed
(25 skipped for absent templates); tools suite 31 tests passed; a synthetic
`.env` was read end-to-end by `tools/check_env.py` and then removed; default and
`--all` privacy screens were clean. `.env` files carry secrets, not personal
data, so the deep screen is unaffected; no real key was read, written or logged.

## OpenRouter setup and Jev routing — 2026-10-02

Supersedes the account/key setup in the earlier dependency and Jev entries below.
One OpenRouter account serves application functions and Jev. Separate keys are
loaded as `OPENROUTER_API_KEY` and `OPENROUTER_JEV_API_KEY`; assigning the same
value to both is supported. Jev uses OpenRouter's compatible System One endpoint
and no longer reads `TYPESAFE_API_KEY`. No silent application-key fallback is used.
The request rubric and response validation remain unchanged.

Added `Documentation/OpenRouter-Setup.md` for signup, credit, suggested trial
budgets, guardrails, hidden environment prompts, shared-key setup and verification.
Getting Started sets the scene, Dependencies remains the full inventory, and
README, Jev, troubleshooting, privacy and attribution references are aligned.
The assistant still needs its own provider configuration. No actual keys or
account settings were read or changed.

Validation: 13 Jev tests and 6 environment-check tests passed, including dedicated
and shared OpenRouter credentials, missing-key isolation and secret-safe failures.
Local Markdown links, diff whitespace, and both default and `--all` privacy screens
passed. Upstream OpenRouter integration/settings documentation was checked; no
live API request, billing test or account guardrail audit was performed.

## License and attribution — 2026-10-01

Added a standard MIT `LICENSE` under the collective JobJimmy contributors name,
plus `THIRD_PARTY_NOTICES.md` covering separately installed software and service
providers. Updated README, dependencies and release readiness. Embedded CV
artwork is explicitly excluded from the MIT grant: SVG metadata suggests Office
stock assets, and raster provenance remains unverified. Resolve permissions or
replace those assets before considering the template cleared for redistribution.
No template binary or private data changed.

Validation: default and `--all` privacy screens, diff whitespace and local
Markdown link checks passed. Upstream license sources were reviewed. No runtime
code changed; no rendering or full publication/history audit was performed.

## External dependencies reference — 2026-10-01

Added `Documentation/Dependencies.md`, a canonical list of the software, accounts,
API keys, environment variables, network endpoints and private input files JobJimmy
needs. It distinguishes the separate OpenRouter (`OPENROUTER_API_KEY`/`OPENROUTER_MODEL`/
`OPENROUTER_TRANSLATION_GUIDANCE`) and TypeSafe (`TYPESAFE_API_KEY`) credentials,
records `JOBJIMMY_PY_WITH`, and notes the two external endpoints. Linked from the
README requirements table/footer and Getting-Started step 1, and corrected the
README so the Jev/TypeSafe key is listed separately from OpenRouter.

Validation: privacy screen clean in default and `--all` modes; `git diff --check`
clean. Documentation only; no scripts or private records changed.

## No in-tree venv: uv ephemeral runner — 2026-10-01

Removed the fixed sibling virtual environment (`../jobjimmy-venv`) convention,
which was not worktree-safe and was easy for agents to bypass with `uv venv`.
Added `tools/py`, a thin wrapper for `uv run --no-project python` that resolves
the checkout root and forwards optional dependencies from `JOBJIMMY_PY_WITH` as uv
`--with` flags. The project now has no virtual environment at all; uv's cache
lives outside the checkout, so the deep privacy screen stays clean in every
clone and Agent Manager worktree. Documented the rule (never `uv venv`,
`uv sync`, `uv add` or `uv pip install`; override of the global "create a venv"
rule) in `AGENTS.md`, `.kilo/rules/project.md`, `Getting-Started.md`,
`Troubleshooting.md`, `README.md` and the PyMuPDF/certifi commands, and added a
`/.venv/` `.gitignore` safety net. PyMuPDF/certifi error messages now point at
the per-command runner.

Validation: `tools/py` ran standard-library and PyMuPDF (`--with`) commands with
no `.venv` created in the checkout; the changed-file privacy screen passed and
`git diff --check` was clean. The obsolete `/Users/name/work/projects/jobjimmy-venv`
directory outside the repo was left in place. No live document rendering ran;
the global Kilo `AGENTS.md` still contains the generic "create a venv" rule and
is only overridden project-side.

## Jev workflow scaffolding — 2026-10-01

Added `CV/Scripts/jev_check.py` and editable `CV/Jev/requests.json` defaults.
Workflow hooks call Jev after the existing fit/gap analysis and independently on
final Markdown CV/letter text before identity restoration. Reports show a 0–100
match score, provider confidence and document per-point coverage; the existing
fit field remains unchanged. `Documentation/Jev-Checks.md` covers tuning, anonymous
inputs, offline previews, execution and result reporting. `PROCEDURES.md` defines
recording within existing research/document activities without new YAML fields.

Validation: 12 synthetic contract/privacy tests and CLI help passed; both privacy
screen modes and whitespace checks passed. No private records were read into
context or changed. No live Jev request or scoring-quality evaluation ran; live
use requires a TypeSafe key and locally reviewed anonymous inputs. Prompts and
rubrics are suggested defaults for user tuning, not calibrated acceptance gates.

## Shared agent instructions — 2026-10-01

Added project Kilo instruction wiring, keeping skills agent-agnostic under `.kilo/skills/`.
Moved detailed record and document rules to `Documentation/Agent-Reference/` and
made the import skill a focused entrypoint with its ordered workflow in a reference.
Corrected root paths, workflow-specific prerequisites, missing letter-template
claims, translation limits, private layout configuration and visual-review privacy.
Removed the notebook agent's unbundled skill dependency and documented its tool fallback.
Canonical/scaffold/private note-template comparison rules are now explicit.

Validation: both privacy-screen modes and `git diff --check` passed. No private
records changed; no live Kilo session or cross-model behaviour was tested.

## Vault relocated into the private repository — 2026-09-30

The Obsidian vault base is now the private `JobSearch/` checkout, not the
public JobJimmy root. Moved `.obsidian/`, `Dashboard.md`,
`Recruiters/Directory.md` and the note templates into `JobSearch/`; rewrote the
private vault's wikilinks and Dataview `FROM` paths to vault-relative form (no
`JobSearch/` prefix); repointed personal CV-baseline links to
`JobSearch/Templates/`; added a private tooling pointer note; and updated the
public docs, note templates, scaffold and the repository-boundary rule. The
public `.gitignore` now ignores `.obsidian/` entirely.

Validation: privacy screen passed in both modes; `git diff --check` clean;
vault-relative private links resolve within `JobSearch/`. No Obsidian UI
rendering was tested.

## User documentation — 2026-09-30

Replaced the README with a newcomer introduction and linked guides for setup,
knowledge capture, applications, documents/layouts, interviews/offers and
troubleshooting. Added a release-readiness checklist, corrected public-template
personalisation advice and missing-template claims, and aligned technical-guide
navigation. No runtime tools or personal application records changed in this pass.

Validation: relative documentation links/anchors passed; private-repository setup
passed in an isolated temporary workspace without user data; eight core CLI help
checks passed. The optional PDF layout help check requires PyMuPDF, which is absent
in this environment. No Obsidian UI or visual document rendering was tested.
The changed-file privacy screen passed. The deeper `--all` audit previously
flagged an ignored `.obsidian/workspace.json` in the public tree; that exposure
was resolved by relocating the Obsidian vault into the private repository
(below). Publication remains subject to the release-readiness checks. The
unrelated appearance setting was preserved.

## Latest completed work

Privacy hardening now covers the public index, staged blobs, ignored working
outputs, filenames and symlinks. Document tools enforce output destinations.
Translation uses an explicit private policy, enforced routing and local identity
preservation/tokenisation; cover-letter identity can be hydrated locally.
The import skill remains agent-agnostic under `.kilo/skills/` and no longer
requires an unspecified memory graph. See `Documentation/Agentic-Roadmap.md`
for the remaining proposals and operational checks.

Validation: CV regression suite ran 74 tests (49 passed, 25 skipped because
required templates are absent); privacy regression suite passed all 25 tests.
The synthetic cover-letter identity test exercised actual ODT generation.
Skill frontmatter parsed successfully with Ruby YAML; the bundled Python skill
validator could not run because PyYAML is absent. Both privacy-screen modes and
the enabled pre-commit hook passed. Working-tree and staged whitespace checks passed.
No live translation, account audit, visual rendering review or history rewrite
was performed. The app was closed before archiving its latest private session
state. The durable Obsidian runtime configuration now lives in the private
vault at `JobSearch/.obsidian/`.

## Remaining review points

- Open questions, pending user input or unfinished checks.
- Documents waiting for user review or confirmation before rendering or use.
- Anything that must not be treated as done without evidence.

## Rendered previews and checks

Local generated files (ignored by Git) and the commands to regenerate them:

```sh
# Example: regenerate a rendered ODT and its PDF export
python3 CV/Scripts/cv.py render \
    JobSearch/Applications/<application-slug>/CV/<application>-blocks.md \
    JobSearch/Templates/<variant>.odt \
    JobSearch/Applications/<application-slug>/CV/<output>.odt
soffice --headless --convert-to pdf --outdir \
    JobSearch/Applications/<application-slug>/CV \
    JobSearch/Applications/<application-slug>/CV/<output>.odt
```

State explicitly which checks ran (renderer tests, structural comparison,
PDF export, visual review) and which did not. Never claim layout or visual
validation that was not performed.

## Other handover documentation

| Document | Use |
| --- | --- |
| [[PROCEDURES]] | Central runbooks for vault actions (submissions, follow-ups, documents, interviews, research). |
| [[README]] and [[Templates/Application]] / [[Templates/Research]] / [[Templates/Company]] / [[Templates/Recruiter]] | Vault relationships, fields and current note schemas. |
| [[CV/README]] | Markdown/ODT workflow, commands and block-format limits. |
| [[CV/Style-guide]] | Fixed page allocation, variable bullets, non-repetition, readability and five-line bottom-space rule. |
| [[Documentation/CV-Automation-User-Template-Setup]] | Creating the personal `.odt` master from `CV Template.ott` (identity, contacts, photograph, education, languages, hobbies). |
| [[CV/Templates/CV-Template-Population-Agent-Instructions]] | Token/bookmark merge contract, ownership split, budgets and validation for `CV/Scripts/populate_cv.py`. |
| [[Knowledge/Overview]] and [[Knowledge/Evidence-and-sources]] | Personal reference, source register and claim boundaries. |
| [[Knowledge/Gaps-and-mitigations]] and [[Knowledge/Experience]] | Wider direct/adjacent experience to use positively in suitability scoring. |
| [[Knowledge/Writing-guide]] and [[Knowledge/Reasoning-profile]] | Character and reasoning guide for CV bullets and cover letters. |
| [[Knowledge/Role-fit]] and [[Knowledge/CV-positioning]] | Preferences and executive versus managerial emphasis. |
| [[CV/Validation/Report]] | Baseline fidelity validation notes. |

## Working-tree care

List the intentional changes currently in the working tree, so the next agent
can distinguish them from stray files. Recheck Git status before editing or
committing. Never commit API keys or other secrets. Original templates,
reference baselines and unrelated applications must remain unmodified.
