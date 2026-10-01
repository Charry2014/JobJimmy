# Plan: central, discoverable procedures for vault actions

## Goal

Every recurring vault action must have one authoritative central procedure that an
agent can find and follow without copying the format from an existing application.
This covers recording an application submission and the other activity kinds, plus
the linked application-field updates each action requires.

## Observed failure

When asked to record an application submission, the agent read another
application's activity note to reverse-engineer the expected format. That was not a
documented step; it happened because the instructions for this action were not
discoverable or complete in one central place. Any correct action that exists only
as an implicit example is a documentation defect, not a valid workflow.

## Documentation gaps

1. **No canonical action runbook.** The "how to record an action" content is
   fragmented across three places, none of which is the clear entry point:
   - `AGENTS.md`, step 6 of "Adding a job from a link" (scoped to imports only).
   - `README.md`, "Application activities" (written for a human using the Obsidian
     UI: "Insert template", "Settings → Templates").
   - `Templates/Activity.md` (minimal; no body skeleton, no filename rule).
2. **The apply rule is buried inside the import workflow.** A request that is only
   "record a submission" does not obviously match a section titled "Adding a job
   from a link", so the agent has no documented entry point.
3. **No task → procedure index.** `AGENTS.md` is large with no map; there is no
   stated lookup order for "which document tells me how to do X".
4. **No authority statement.** Nothing says the central docs/templates are
   authoritative and that existing notes are examples, not specifications. Nothing
   forbids using another application's activity as a template.
5. **Inconsistent real examples actively invite imitation.** Apply activities used
   two different filename patterns and bodies:
   - `<date>-<application-slug>-application-submitted.md`
   - `<date>-<application-slug>-application.md`
   The naming rule (`YYYY-MM-DD-company-position-action.md`) does not resolve which
   suffix is correct, so an agent samples an example.
6. **Agent-facing vs UI-facing mismatch.** `README.md` assumes the Obsidian UI
   inserts the template; `AGENTS.md` only vaguely says "an agent writing files
   directly must resolve these itself" without a concrete agent procedure.
7. **No per-kind body guidance.** Nothing states what must be recorded for `apply`,
   `follow-up`, `interview-notes`, `document-added`, `other`, so each agent invents
   structure.
8. **Application-field side effects are not co-located.** That a submission sets
   `status: applied` and `date_applied` while activities otherwise never change
   status is spread between `README.md` and `AGENTS.md`, not part of an activity
   procedure.
9. **`HANDOVER.md` can be mistaken for procedure.** It is a dated snapshot but
   reads like instructions; nothing marks it as non-authoritative for "how".
10. **No discoverability hook in the agent config.** `.kilo/` has no command/agent
    pointing at a runbook, and the import skill (outside the repo) also stops at
    import.

## Proposed improvements

### 1. Create one canonical action runbook
Add `PROCEDURES.md` at the vault root as the single source of truth for vault
actions. Contents:
- A short "read this before performing an action; do not infer format from
  existing notes" preamble and a precedence rule (Templates + this runbook >
  examples; flag conflicts).
- A **task → procedure index** table at the top.
- One section per activity `kind` with an exact runbook:
  - filename (fixed pattern), frontmatter block, body skeleton, and which
    application fields to update / not touch.
- Start with "Recording an application submission (`kind: apply`)" — the case that
  failed — specifying:
  - create `Activities/YYYY-MM-DD-company-position-application.md` from the
    Activity template;
  - frontmatter: `type: activity`, quoted `application` wikilink to the exact
    application note, `date` = submission date, `kind: apply`, `documents` list;
  - body: a `# Application submitted — <position> — <company>` title and a Notes
    paragraph stating the submission date and that it was user-reported, with the
    channel/reference only if supplied;
  - update the application: `status: applied`, `date_applied: <date>`, a sensible
    `next_action`, leave `next_action_date` blank unless known, never reset
    `priority`/`fit`/`date_found`;
  - record only a user-reported submission; never infer one.

### 2. Make it discoverable
- Add a short pointer at the very top of `AGENTS.md`: "Vault actions (recording a
  submission, follow-ups, interview notes, document-added) are specified centrally
  in `PROCEDURES.md`; follow it and do not model a new note on another
  application's file."
- Add the same pointer in `README.md`.
- Add a Kilo command `.kilo/command/record-application.md` (or similar) whose body
  says to read and follow `PROCEDURES.md` for the relevant kind, so a normal
  request routes to the central procedure.
- Add a one-line pointer in the external skill note and `HANDOVER.md`.

### 3. Give agents the file-writing procedure, not just the UI steps
In `PROCEDURES.md`, restate `README.md`'s activity steps as agent steps: read
`Templates/Activity.md`, resolve `{{title}}`/date placeholders, quote wikilinks,
write the file directly, and verify the `application` link. Keep `README.md`'s UI
instructions for the human path and cross-link the two.

### 4. Encode the schema in the template
Extend `Templates/Activity.md`'s comment with the filename convention and a
one-line body hint per `kind`, so the template itself reinforces the runbook.

### 5. Resolve the inconsistent examples
Normalise the `...-application-submitted.md` activity files to the documented
`...-application.md` pattern. Dataview lists are link-driven, so no application
links change; verify tables still populate. If normalising is undesired, instead
document both patterns as accepted — but the plan prefers one canonical suffix.

### 6. Keep the dated snapshot out of the "how" role
Add one line to `HANDOVER.md` stating it is a state snapshot and that procedures
live in `PROCEDURES.md`, to prevent it being read as the workflow.

## Files to change

| File | Change |
| --- | --- |
| `PROCEDURES.md` (new) | Canonical action runbook + task→procedure index |
| `AGENTS.md` | Top-of-file pointer; replace the buried step-6 fragment with a reference to `PROCEDURES.md`; note that activities must not be modelled on existing notes |
| `README.md` | Pointer to `PROCEDURES.md`; agent-facing cross-link alongside the existing UI steps |
| `Templates/Activity.md` | Filename rule + per-kind body hints in the comment |
| `.kilo/command/record-application.md` (new) | Routes the request to `PROCEDURES.md` |
| `HANDOVER.md` | Non-authoritative-for-procedure note + pointer |
| Existing `...-application-submitted.md` activity notes | Rename to the documented `...-application.md` pattern |
| `CV/README.md` (optional) | No change expected; confirm it does not describe vault actions |

Out of scope: changing the CV/cover-letter rendering workflow, the skill's import
logic, or any application data beyond the filename normalisations.

## Verification

- `PROCEDURES.md` exists and contains a runbook for every `kind` in the naming
  rule; each runbook names the exact file pattern, frontmatter and field updates.
- `AGENTS.md`, `README.md`, `HANDOVER.md` and `Templates/Activity.md` all point to
  `PROCEDURES.md`; grep confirms no other doc claims to define the apply/activity
  procedure.
- A dry run: apply the "record a submission" runbook to a scratch note and confirm
  it is self-sufficient without reading any existing application.
- Dataview-visible activity links still resolve after any renames; the affected
  application notes and their tables still list the submission activities.
- No unresolved placeholders; `git diff --check` clean; inspect the diff and new
  files.
- Confirm `.kilo/plans/` stays untracked and nothing secret is added.
