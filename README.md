# JobJimmy

A small, experimental job-search workspace: keep track of applications in
Obsidian, build a reusable record of your experience, and use an AI assistant to
prepare evidence-backed CVs, cover letters and interview notes.

Your notes are ordinary Markdown. Documents are assembled locally with Python
and LibreOffice. Your real job-search data lives in a separate private Git
repository inside `JobSearch/`; the public project contains the reusable tools.

**Status: early-stage hobby project.** Application tracking and document tooling
exist, but setup still involves files and terminal commands. There is no hosted
service, application-submission bot or one-click installer.

## Start here

1. [Set up your workspace](Documentation/Getting-Started.md): tools, private
   storage, Obsidian and the first checks.
2. [Build your career knowledge base](Documentation/Knowledge-Base.md): give
   the assistant reliable facts and teach it from new information.
3. [Work with applications](Documentation/Applications.md): add a job, assess
   fit, track contacts, record submissions and follow up.
4. [Prepare CVs and cover letters](Documentation/Documents.md): choose a layout,
   draft, review, render and optionally translate.
5. [Prepare for interviews and offers](Documentation/Interviews-and-Offers.md):
   research, practise, debrief and plan a negotiation.

Start with tracking. You can add document automation and translation later.

## What you need

| Tool | Used for | Required? |
| --- | --- | --- |
| Obsidian | Read and edit the vault | Recommended interface; any Markdown editor can edit the notes |
| Dataview | Dashboard and activity tables in Obsidian | For the live tables |
| Git | Keep public tools and private records in separate repositories | For the documented setup and privacy gate |
| Python 3.11+ | Document scripts and privacy checks | For automation; development checks currently run on Python 3.12 |
| uv | Runs the Python tools with no in-tree venv | For automation |
| LibreOffice Writer | Personalise ODT layouts and export PDFs locally | For document work |
| A filesystem-capable AI assistant | Research, drafting and guided record updates | Optional for manual tracking; needed for agent-assisted workflows |
| OpenRouter account and API key | The supplied English-to-German translation script | Optional; a separate account from Jev, unrelated to your assistant's subscription |
| TypeSafe account and API key | The advisory Jev fit and document checks | Optional; a separate key from OpenRouter |
| PyMuPDF | Automated PDF layout and comparison checks | Optional; visual review is still needed |

Installation links, platform notes and commands are in
[Getting started](Documentation/Getting-Started.md). The complete list of
software, accounts, environment variables and network endpoints is in
[External dependencies](Documentation/Dependencies.md).

## A typical application

> Add this job advert, assess it against my experience, and propose which CV
> baseline to use. Keep unsupported claims and missing information explicit.

The assistant uses the [create-application skill](.kilo/skills/create-application/SKILL.md)
to create linked records for the role, employer, advert and recruiter where
applicable. You review its assessment, then ask for a CV and cover-letter draft.
After wording review, you render and inspect the documents. You submit the
application yourself and record what happened.

Skills are **agent-agnostic** and live in `.kilo/skills/`. The folder name does
not require a particular agent. If your assistant does not discover the skill,
ask it to read that file explicitly. It should follow [AGENTS.md](AGENTS.md)
and [PROCEDURES.md](PROCEDURES.md) when changing records.

## What works today

| Capability | Current state |
| --- | --- |
| Applications, companies, recruiter contacts and activity history | Markdown templates and Dataview views |
| Import and assess a job advert | One implemented agent skill; access to listings can fail |
| Career knowledge and learning from corrections | Private notes maintained with the assistant; no required memory service |
| Tailored CVs | Draft/review workflow; two local rendering approaches |
| Cover letters | Markdown drafting and local identity insertion; ODT rendering requires your own compatible template |
| Translation | OpenRouter script for block-marked CVs, currently English to German |
| Interview preparation and negotiation | Guided conversations and activity notes; dedicated skills are proposed, not installed |
| Jev fit and document checks | Advisory CLI scaffold with editable requests, anonymous input checks, separate match scores and confidence; needs a TypeSafe key and domain tuning |
| Email/calendar integration, automatic reminders, Notion sync | Not implemented as project workflows |

The blank `CV/Templates/CV Template.ott` is included. Personal CV baselines,
identity files and a ready-to-use cover-letter ODT are **not included**.
The [documents guide](Documentation/Documents.md) explains the implications.

[Jev checks](Documentation/Jev-Checks.md) run after the existing fit/gap analysis
and on each final Markdown CV and cover letter independently. The requests and
rubrics are editable; live scoring quality has not yet been validated.

## Your files stay separate

```text
jobjimmy/                       public tools, guides and source templates
├── Documentation/
├── Templates/                  canonical note templates (copied into the vault)
├── CV/                         CV tooling, references and templates
├── .kilo/skills/
└── JobSearch/                  the Obsidian vault; independent private Git repo
    ├── .obsidian/              vault configuration, plugins and snippets
    ├── Dashboard.md
    ├── Applications/
    ├── Companies/
    ├── Recruiters/             including Directory.md
    ├── Knowledge/
    ├── Templates/              note templates and your CV baselines
    └── Outputs/
```

Never enter personal details into public templates. Make personal copies under
`JobSearch/`, and open `JobSearch/` as the Obsidian vault so private notes and
the dashboard stay together. Git exclusion does not stop an AI assistant, a sync
service or a filesystem archive from reading those files. Check the privacy of
the actual model/tool route before sharing private text. See [Privacy](PRIVACY.md).

The vault, including its Obsidian configuration and UI state, lives entirely
inside the private `JobSearch/` tree, so workspace-state files no longer expose
private note paths in the public project. The
[setup guide](Documentation/Getting-Started.md) explains what to check before
use and publication.

## Troubleshooting and contributing

- [External dependencies](Documentation/Dependencies.md)
- [Troubleshooting](Documentation/Troubleshooting.md)
- [CV technical reference](CV/README.md)
- [Agentic roadmap](Documentation/Agentic-Roadmap.md)
- [Release readiness](Documentation/Release-Readiness.md)

Use synthetic data when reporting bugs. Never attach real CVs, private logs or
application records to public issues. Check the release-readiness list before
publishing a fork; this checkout currently has no project-level `LICENSE` file.
