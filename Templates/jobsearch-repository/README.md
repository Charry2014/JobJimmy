# JobJimmy-JobSearch — private job-search repository

This repository holds **all user-specific job-search data**: application
records, company research, recruiter contacts, optional private career evidence,
personal CV templates and generated documents. It is **not** part of the public
JobJimmy repository. It is mounted at `JobSearch/` inside the JobJimmy workspace and
is also the **Obsidian vault**; JobJimmy ignores this whole tree.

## Using this repository with JobJimmy

1. Place (or clone) this repository so its contents sit at
   `<JobJimmy workspace>/JobSearch/`. Its remote repository may have any name;
   the local directory must be `JobSearch`.
2. Open **this repository** (`JobSearch/`) as the Obsidian vault. The vault
   configuration, dashboard and views live here, so the notes and tables render
   together without this repository becoming part of JobJimmy.
3. Commit and push **this repository separately** from JobJimmy. JobJimmy's Git
   status does not report changes made here — always check both:

```sh
git -C JobSearch status
```

## Layout

```text
JobSearch/                    # Open this directory as the Obsidian vault
├── .obsidian/                # Vault configuration, plugins and snippets
├── .githooks/                # Optional local pre-commit knowledge check
├── AGENTS.md                 # Copied from Templates/jobsearch-repository
├── README.md
├── .gitignore
├── Dashboard.md              # Application pipeline and status views
├── Applications/             # One folder per application
├── Companies/                # Reusable employer research
├── Recruiters/               # Agencies, individual contacts and Directory.md
├── Knowledge/                # Curated career evidence, preferences and sources
├── Experience/               # Private career evidence (optional)
├── Templates/                # Note templates and personal CV templates
├── Outputs/                  # Generated CVs and documents (optional)
└── Attachments/              # Shared attachments, if any
```

- Applications are stored as `Applications/<YYYY-MM-company-position>/` with the
  application note, `Activities/`, `CV/` and `Attachments/` folders.
- Application notes link supporting records with vault-relative links (no
  `JobSearch/` prefix), for example `[[Companies/company-slug]]` and
  `[[Recruiters/agency-person]]`; a Dataview table uses
  `FROM "Applications/<slug>/Activities"`.
- Recruiter notes distinguish an agency contact from a named person by the
  filename (`<agency-slug>-contact.md` vs `<agency-slug>-<person-slug>.md`) and
  by whether `recruiter_name` is set; both use `type: recruiter`.

## Git notes

- Private Git hosting is **access control, not encryption**. Anyone with read
  access to the remote can read every record in the history.
- Deleting personal material in a later commit does not remove it from earlier
  commits. Decide before the first push what belongs in the repository at all.
- Generated documents and final ODT/PDF files are tracked deliberately, one
  commit at a time; reports, intermediate renders and editor state are ignored —
  see `.gitignore`.
- `.githooks/pre-commit` is an optional local gate that validates staged
  `Knowledge/**` articles against the outer project's reviewed redaction policy.
  Activate it with `git config --local core.hooksPath .githooks`; it is a
  convenience, not a substitute for reviewing content before sending it to a
  model.

For onboarding, follow `Documentation/Getting-Started.md` and
`Documentation/Knowledge-Base.md` in the outer JobJimmy project. Create
`Knowledge/Sources/` during setup; no personal knowledge is prefilled.
