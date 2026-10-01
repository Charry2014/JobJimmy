# Plan: knowledge base is model-safe when clean, with an on-edit check

## Goal

Agents currently treat *all* of `JobSearch/Knowledge/` as raw private text that
must never enter a remote model without the full reversible-redaction workflow.
That over-blocks normal work: the curated knowledge-base articles are meant to
be the reusable, locally reviewed profile.

Two changes:

1. **State the allowance clearly.** A knowledge-base article MAY be read into and
   sent to a remote model when it contains none of the reviewed policy's
   `redact_values` and no unlisted contact pattern. This is a standing allowance
   for `JobSearch/Knowledge/**` only; adverts, application/activity notes,
   company/recruiter records, identity JSON, CV baselines and generated
   documents keep the existing redaction workflow.
2. **Provide the review mechanism.** A deterministic local check that scans
   knowledge-base Markdown against the reviewed private
   `JobSearch/Templates/redaction-policy.json` and fails closed. It is required
   after each knowledge edit, and can be enforced by a private-vault pre-commit
   hook shipped in the scaffold.

## Part 1 — the check (public engine)

Extend `CV/Scripts/redact_md.py` (which already owns policy parsing) with:

- A pure function `scan_reasons(text, values) -> list[str]` returning generic
  reasons only, never the matched value:
  - `"reserved privacy token"` — text already contains an
    `APP_MAN_PRIVATE_..._TOKEN` (`RESERVED`).
  - `"listed identifier"` — a literal, case-sensitive `redact_values` match
    (same matching rule as `redact()`).
  - `"contact pattern"` — an email/phone/LinkedIn match (`CONTACT`).
- A `check` subcommand:
  ```sh
  tools/py CV/Scripts/redact_md.py check \
    JobSearch/Templates/redaction-policy.json JobSearch/Knowledge
  ```
  - Accepts one or more files or directories; a directory expands to
    `**/*.md` (skip non-Markdown, skip symlinks).
  - Loads the policy through the existing `policy_values()`, so an unreviewed or
    empty policy fails the whole check (cannot validate).
  - Prints one line per file: `PASS <path>` or `FAIL <path>: <reason>`
    (reasons joined, never the value). Paths are printed relative to the current
    directory, not absolute.
  - Exits non-zero if any file fails; `0` only when every scanned file is clean.
  - Does not call `check_output` (it reads inputs, writes nothing).

Rationale for a new function rather than reusing `redact()`: `redact()` fails
when a document has *no* match (its purpose is to export), while the clean check
must succeed exactly when there is no match.

## Part 2 — tests

Add synthetic cases to `CV/Scripts/test_redact_md.py`:
- clean text → `scan_reasons` returns `[]`.
- a listed value → `["listed identifier"]`; overlapping/absent values do not
  produce false positives.
- a contact pattern not in the policy → flags `"contact pattern"`.
- a reserved `APP_MAN_PRIVATE_..._TOKEN` → flags `"reserved privacy token"`.
- a directory/file CLI run: clean file exits 0, dirty file exits non-zero, and
  stdout never contains the identifier value.

## Part 3 — make the rule clear (documentation)

Edit the authoritative places, keeping one meaning everywhere:

- `PRIVACY.md` — in "Before reading private content into an agent", add the
  knowledge-base exception: curated articles are model-safe once the local
  clean check passes; define the check and its limits (pattern/literal
  matching, no anonymity proof). `Sources/` snapshots are included in the scan
  but often fail; keep the redaction workflow for those.
- `AGENTS.md` — the private-content paragraph currently forbids reading "employer
  paths" etc. Add the explicit carve-out with the check command and note the
  allowance is only for `JobSearch/Knowledge/**`.
- `.kilo/rules/project.md` — same one-line carve-out so all modes inherit it.
- `Documentation/Agent-Reference/Documents.md` — "Professional knowledge base
  for CV tailoring": state that KB articles may be sent to a remote model when
  the check passes, and that the check is mandatory after each KB edit.
- `.kilo/skills/create-application/references/import.md` — Step 1 (read the KB
  directly once clean instead of "do not read raw text") and Step 10 (run the
  clean check after every knowledge update; a failure means fix the article, not
  send it).
- `Documentation/Knowledge-Base.md` — "Memory and privacy": explain the clean
  check in user terms.
- Private `JobSearch/AGENTS.md` (precedence) and the distribution copy
  `Templates/jobsearch-repository/AGENTS.md` — mirror the rule and command so a
  fresh private vault inherits it. No personal values are copied into the public
  tree.

## Part 4 — enforce on each edit

- **Workflow gate (primary):** every workflow that edits `JobSearch/Knowledge/`
  runs the check before finishing and reports the mode/result, matching the
  existing "state which checks ran" rule. Failure blocks only the remote use of
  the offending article; the fix is to genericise the identifier or redact it.
- **Optional hard gate (scaffold):** add
  `Templates/jobsearch-repository/.githooks/pre-commit` that checks only the
  staged `Knowledge/**/*.md` files against the reviewed policy (located via the
  vault's `Templates/redaction-policy.json`, script resolved through the parent
  JobJimmy checkout). Document activation with
  `git config --local core.hooksPath .githooks`. It exits 0 when the policy or
  the parent script is absent, so an unmounted public checkout still works.
  Confirm the private vault's existing pre-commit hook before enabling.

## Validation

- `tools/py CV/Scripts/test_redact_md.py` (new cases pass) and the CV privacy
  regression suite.
- Run the new check against the real private KB + reviewed policy locally and
  record only the generic PASS/FAIL status; never print matched values.
- `tools/py tools/privacy_screen.py` in default and `--all` modes, and
  `git diff --check`.
- Confirm no `.venv` created and Python ran only through `tools/py`.

## Out of scope

- No change to the reversible-redaction workflow for adverts, notes, identity or
  documents.
- No attempt to prove anonymity or audit the policy's completeness; a clean
  check means "no known listed value or contact pattern is present", not
  "unidentifiable".
- No live remote-model transfer is performed as part of this work.
