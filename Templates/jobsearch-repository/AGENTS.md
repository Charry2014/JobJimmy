# AppMan-JobSearch: agent guide

This repository contains **private job-search data** — real application notes,
activity history, company and recruiter records, CV source documents and
generated documents. It is mounted inside the AppMan workspace at `JobSearch/`,
is an independent Git repository, and is the **Obsidian vault**: nothing here is
ever committed to the public AppMan repository, and AppMan's `.gitignore`
excludes this whole tree.

## Workflow

Follow the AppMan workflow documents for how to carry out vault actions:

- the root `AGENTS.md` and `PROCEDURES.md` of the AppMan workspace (durable
  rules and central runbooks for submissions, follow-ups, document additions,
  interview actions and research);
- this repository's own `AGENTS.md`, which takes precedence for the privacy
  rules below.

Templates (`Templates/` in the AppMan workspace and this vault), the dashboards
(`Dashboard.md`, `Recruiters/Directory.md`) and the runbooks are authoritative.
Existing application notes are examples, not specifications; do not model a new
note on another application's file.

## Layout

- `Applications/<YYYY-MM-company-position>/` — one folder per application with
  its note, `Activities/`, `CV/` and `Attachments/`.
- `Companies/` — reusable employer research, one note per company.
- `Recruiters/` — agency and named-person contacts; `<agency-slug>-contact.md`
  for an unnamed person, `<agency-slug>-<person-slug>.md` otherwise, both with
  `type: recruiter`.
- `Templates/` — the note templates (`Application`, `Company`, `Activity`,
  `Research`, `Recruiter`) and optional personal CV baselines.
- `Knowledge/` — the curated professional knowledge base (profile, evidence,
  gaps and writing guides), with source snapshots under `Sources/`.
- `Experience/`, `Outputs/` — optional private areas for career evidence and
  generated documents.

Links from application notes to supporting records are vault-relative to this
repository and carry no `JobSearch/` prefix, for example
`company: "[[Companies/company-slug]]"`.

## Factual honesty

- Never invent employment claims, qualifications, dates, metrics or outcomes.
- Record company names, dates and other potentially identifying experience
  data only as supplied by the user, with provenance where it matters.
- Preserve unknowns as blank; do not guess.

## Personal documents and identity data

- Fixed personal details (name, address, phone, email, photograph, LinkedIn
  target, education, languages, hobbies) live in the user's private master ODT
  template or local identity JSON. Keep them out of model-facing drafts; local
  hydration may insert them into the complete private Markdown deliverable.
- The split is deliberate: model-generated Markdown (taglines, Profile,
  Expertise, Work Experience, cover-letter text) is kept separate from fixed
  personal details, and must be enforced before model transfer. Career history can still identify
  a person. Neither this instruction nor a local CLI proves cloud privacy.
- Use `cover_letter.py hydrate-identity` to insert the sender and full signature
  locally; complete letters retain name, phone and email. Do not print the
  identity JSON or hydrated draft into hosted agent context.
- ODT/PDF merging and rendering are **local-only** operations on this machine.
  Never upload application documents to external services.

## What agents must not read or expose directly

- For **every** phase, a hosted agent reads only locally prepared, checked
  Markdown. The curated knowledge-base articles under `Knowledge/**` are the
  exception: they are kept free of the reviewed redaction policy's
  `redact_values`, so once the local clean check passes they may be read and
  sent to a remote model directly — do not force them through the redaction
  workflow. Run the check after every knowledge edit and treat a failure as
  "fix the article", not "send it":
  `tools/py CV/Scripts/redact_md.py check JobSearch/Templates/redaction-policy.json JobSearch/Knowledge`
  An optional `.githooks/pre-commit` (see README) runs the same check on staged
  knowledge files. Do not read raw adverts, company/recruiter records, identity
  JSON, application paths, final documents or private Git diffs into model
  context; private filenames and tool output may identify people too. Use
  `PRIVACY.md`'s reviewed-policy `redact_md.py` workflow before any other
  private read. If the policy has not been locally reviewed, stop rather than
  treating a seeded identity list as complete.
- Completed submission PDFs and final documents are the user's outputs; link
  them, do not restate their personal contents in new notes.
- Any local master ODT/personal template files kept alongside this repository.
- Treat every path under this repository as potentially personal: do not copy
  its contents into public repositories, issue descriptions, commit messages,
  test fixtures or documentation.

## Generated documents

- Generated documents must not be pushed unintentionally: check
  `git status` in this repository before committing, and commit final ODT/PDF
  documents deliberately.
- `.gitignore` here ignores intermediate renders, reports and editor state.
  It does **not** hide anything from an AI agent, a backup tool or a
  filesystem archive — Git exclusion is a repository boundary, not an access
  control.
- `.gitignore` likewise does not decide what may be sent to an external model;
  the AppMan privacy documentation (`PRIVACY.md`) governs that.
