# Vault action procedures

Single source of truth for how to carry out vault actions — recording an
application submission, follow-ups, document additions, interview actions and
other activity notes.

**Read this before performing an action.** Do not infer the format of a new note
from an existing application's files: existing notes are examples, not
specifications. Templates plus this runbook are authoritative. If an existing
note conflicts with this runbook, follow the runbook and report the inconsistency
rather than copying the note. `HANDOVER.md` records dated state, not procedure;
`Documentation/Applications.md` describes the same actions for a human using
the Obsidian UI; `README.md` is the project introduction.

Every task that changes files in the outer repository must additionally pass
the [privacy screening gate](AGENTS.md#privacy-screening-hard-gate) in
`AGENTS.md` (`python3 tools/privacy_screen.py`) before completion; personal
data belongs only in the private `JobSearch/` tree.

## Task → procedure

| Task | `kind` | Section |
| --- | --- | --- |
| Record an application submission | `apply` | [Recording an application submission](#recording-an-application-submission) |
| Record a follow-up sent | `follow-up` | [Other activity kinds](#other-activity-kinds) |
| Record a document added (CV, cover letter, attachment) | `document-added` | [Other activity kinds](#other-activity-kinds) |
| Record interview preparation | `interview-preparation` | [Other activity kinds](#other-activity-kinds) |
| Record interview notes | `interview-notes` | [Other activity kinds](#other-activity-kinds) |
| Record advert research / original advert | `research` | [Research subpage](#research-subpage) |
| Record any other action | `other` | [Other activity kinds](#other-activity-kinds) |

Importing a new job from a link is a separate workflow: see the "Adding a job
from a link" section of `Documentation/Agent-Reference/Records.md` and the `create-application` skill
(`.kilo/skills/create-application/SKILL.md`). That workflow may record an
`apply` activity as part of its steps, and when it does, it follows the
submission runbook below.

## How an agent writes an activity file

The Obsidian Templates plugin resolves `{{title}}` and date placeholders when a
human inserts a template. An agent writing files directly must do this itself:
read `Templates/Activity.md`, replace every placeholder with the real value, keep
the YAML valid, quote wikilinks, and keep `documents` as a list (`documents: []`
when empty). Never leave `{{...}}` in a written file.

Keep **Activity** immediately below the application's YAML properties; do not move
or edit its Dataview table. A correctly linked activity appears in that table
automatically — the table is a view, not a write-back form.

## Common rules for every activity

- **Filename:** `YYYY-MM-DD-<application-slug-without-date>-<action>.md`, stored in
  that application's `Activities/` folder. Add a `-2`-style suffix only to avoid a
  collision. See each kind for its `<action>` token.
- **Frontmatter:** `type: activity`; `application` set to a quoted wikilink of the
  exact application note; `date` set to the day the action happened
  (`DD-MM-YYYY`, zero-padded); `kind` set to the kind above; `documents` a
  list of quoted wikilinks to real files (or `[]`).
- **Body:** `# ` title, then a `## Notes` section with the details. Write details
  in the body, not in extra YAML.
- **Activities do not change application status, dates or next action.** Update
  those explicitly and only where the kind's runbook says so.
- **Record only what happened.** Never invent a submission, a follow-up sent, a
  contact, a channel or a confirmation reference. A reported "no response" is a
  separate `other` activity dated when reported; it is not a follow-up sent.
- Use the exact `kind` values: `research`, `apply`, `interview-preparation`,
  `interview-notes`, `document-added`, `follow-up`, `other`.

## Recording an application submission

Use for a user-reported submission (also the step-6 case in the import workflow).

1. Create `JobSearch/Applications/<application-slug>/Activities/YYYY-MM-DD-<application-slug-without-date>-application.md`.
2. Frontmatter:
   ```yaml
   ---
   type: activity
   application: "[[Applications/<application-slug>/<application-slug>]]"
   date: <submission date>
   kind: apply
   documents: []
   ---
   ```
3. Body: title `# Application submitted — <position> — <company>`, then a
   `## Notes` paragraph stating the submission date and that it was reported by
   the user. Record the submission channel or a confirmation reference only if the
   user supplied one; otherwise say none was recorded.
4. Update the application note's frontmatter:
   - `status: applied`
   - `date_applied: <submission date>`
   - `next_action`: one of the canonical values `Send Application`, `Await
     Response` or `Interview Prep`; deviate only rarely, keeping any deviation
     to three words maximum.
   - `next_action_date`: the `DD-MM-YYYY` date whenever a date for the next
     action is known; leave it blank only when none is known.
   - Do **not** reset `priority`, `fit`, `date_found`, `advert_url` or other
     existing values.
5. Do not submit the application, send messages or claim a confirmation that was
   not provided.

## Other activity kinds

Each follows the common rules; only the `<action>` token, the body focus and any
application-field side effect differ.

| `kind` | `<action>` token | Body focus | Application fields |
| --- | --- | --- | --- |
| `follow-up` | `follow-up` | Date, channel and content of a message actually sent by the user | Optionally set the next `next_action`; do not change status |
| `document-added` | `document-added` | Which document was added and why, with the file(s) in `documents` | None; link the file from the application's relevant section |
| `interview-preparation` | `interview-preparation` | Questions, talking points and preparation notes | Optionally set `next_action` toward the interview date |
| `interview-notes` | `interview-notes` | Attendees, discussion, outcomes, next steps | Usually `status: interviewing` if the interview happened |
| `other` | short descriptor (for example `no-response`) | Any other action or observation, dated when it happened or was reported | Usually none |

For a `document-added` activity, the `documents` list holds a quoted wikilink to
the real added file, for example:
```yaml
documents:
  - "[[Applications/<application-slug>/CV/<slug>-cover-letter.pdf]]"
```

## Jev check results

Follow `Documentation/Jev-Checks.md` for anonymous payloads, editable requests,
execution and interpretation. A check does not change application status, dates,
next action, the existing `fit` property or approved document text.

- After fit/gap analysis, append **Jev fit check** under the existing research
  note's **Research notes**. Record the match score (0–100), confidence, actual
  check date, request version/hash and a link to the report. Also record the Jev
  match score and confidence in the application note's **Assessment** section,
  kept distinct from the 0–10 `fit`. Keep the original reasoned assessment and
  explain disagreements separately.
- For final Markdown CV/letter checks, include **Jev document check** under
  **Notes** in the corresponding `document-added` activity, with separate
  results for each document, report links, omitted/partial/unclear points and
  their confidences. Add only existing reports to `documents`. If the check is
  a later standalone action with no new document, use `kind: other` and action
  `jev-check`; do not invent another document addition.
- A preview or failed call is not a completed assessment. Record unavailable
  status and reason when relevant, never a fabricated score. Keep earlier results
  as history and mark them superseded after input/request changes.
- Present results in chat as well as saving notes. Keep reports outside renderable
  CV/letter text. No new YAML properties or note types are introduced.

Read and compare the canonical and private working note templates before writing
records, as required by `AGENTS.md`. The CLI creates reports only; the agent owns
these record updates.

## Research subpage

The advert research note is an activity with `kind: research`, but it is not named
with the dated pattern. Use `Templates/Research.md`, store it as
`Activities/<application-filename>-research.md`, and:
- set `application` to the exact application note;
- populate `date`, `advert_url`, and `advert_captured` (only when the original
  text is actually saved);
- set `document_language` to the lowercase ISO 639-1 document language chosen
  from the advert and application instructions (`en` or `de`, for example), and
  state the evidence under **Research notes**. If genuinely ambiguous, leave it
  blank and resolve before drafting; do not infer from the employer's location;
- keep the full original advert under **Original job advert** and analysis under
  **Research notes**.

Reuse an existing research note rather than creating a duplicate. The application's
**Job advert** link must point here. See `AGENTS.md` for advert reproduction and
capture rules.
