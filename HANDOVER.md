# Engine handover — 2026-09-30

This snapshot supports a clean agent context. It is a dated state snapshot, not a
procedure: recurring vault actions are specified centrally in
[PROCEDURES.md](PROCEDURES.md). Read [AGENTS.md](AGENTS.md) for
durable instructions and recheck Git status before editing. Keep this file limited to reusable engine work. Personal work state belongs
in `JobSearch/HANDOVER.md`; never name real applications or people here. Application and activity notes remain the source of
truth for each opportunity: this handover is a snapshot, not permission to
submit anything or an instruction to redo completed work.

## Knowledge base is model-safe when clean — 2026-10-01

`redact_md.py` gained a `check` subcommand (backed by a `scan_reasons` helper)
that fails closed when a document already contains a listed `redact_values`
entry, a reserved privacy token or an unlisted contact pattern; it prints only
generic PASS/FAIL status, never the matched value, and accepts files or
directories. `PRIVACY.md`, root `AGENTS.md`, `.kilo/rules/project.md`, the
document workflow reference, the import skill, the knowledge-base guide and both
the private and scaffold `AGENTS.md` now state the same rule: curated
`JobSearch/Knowledge/**` articles may be read into and sent to a remote model
once this local clean check passes, while adverts, application/activity notes,
employer and recruiter records, identity JSON and documents keep the reversible
redaction workflow. An optional private-vault `.githooks/pre-commit` in the
scaffold runs the check on staged knowledge files.

Validation: redaction unit tests extended to 13 (all passed); the full CV suite
passed 111 tests (25 skipped for absent templates); the privacy screen was clean
in default and `--all` modes; `git diff --check` was clean. The check was also
exercised locally against the private knowledge tree and returned only generic
PASS/FAIL status; cleaning any flagged article remains private work. No private
article was read or rewritten.

## External dependencies reference — 2026-10-01

Added `Documentation/Dependencies.md`, a canonical list of the software, accounts,
API keys, environment variables, network endpoints and private input files AppMan
needs. It distinguishes the separate OpenRouter (`OPENROUTER_API_KEY`/`OPENROUTER_MODEL`/
`OPENROUTER_TRANSLATION_GUIDANCE`) and TypeSafe (`TYPESAFE_API_KEY`) credentials,
records `APPMAN_PY_WITH`, and notes the two external endpoints. Linked from the
README requirements table/footer and Getting-Started step 1, and corrected the
README so the Jev/TypeSafe key is listed separately from OpenRouter.

Validation: privacy screen clean in default and `--all` modes; `git diff --check`
clean. Documentation only; no scripts or private records changed.

## No in-tree venv: uv ephemeral runner — 2026-10-01

Removed the fixed sibling virtual environment (`../appman-venv`) convention,
which was not worktree-safe and was easy for agents to bypass with `uv venv`.
Added `tools/py`, a thin wrapper for `uv run --no-project python` that resolves
the checkout root and forwards optional dependencies from `APPMAN_PY_WITH` as uv
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
`git diff --check` was clean. The obsolete `/Users/name/work/projects/appman-venv`
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
public AppMan root. Moved `.obsidian/`, `Dashboard.md`,
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
