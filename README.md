# JobJimmy

### Give your applications some leverage.

**The job application process in a nutshell - Hours of work, skimmed then binned.**

Find a promising job... Decode the advert... Rewrite your CV... Wrestle with a cover letter... Invest emotional energy... Imagine yourself in that job... Submit... Repeat... 

Somehow remember which company you applied to and what you told them.

JobJimmy is your AI job application assistant: a butler with a metaphorical crowbar to help force that glass door open. Keep those links in order, and all joined up. It helps you decide which roles deserve your time, put your relevant experience forward, and keep the whole process organised.

* Already tailoring every application? Get your evenings back. 
* Sending the same CV everywhere? Give employers a clearer reason to consider you.

## Before you spend an afternoon, check the fit

A shiny job title isn't enough to justify three hours of application work.
Ask Jimmy to compare the actual requirements with your experience first.

The aim is an honest assessment you can inspect:

- **Strong matches:** requirements you can support with specific evidence.
- **Transferable experience:** relevant work that needs explaining, rather than
  pretending you've done exactly the same thing.
- **Real gaps:** missing experience or constraints that could make the role a
  poor use of your time.
- **Unknowns:** questions worth answering before you commit to an application.

Then decide: apply, investigate, or move on. Spend your effort where you have
a credible case, and stop polishing applications with obvious deal-breakers.

Jimmy doesn't know who else applied or what the hiring manager will decide.
A fit assessment is a reasoned comparison, not your probability of getting
hired. Optional numerical checks are advisory and their live scoring quality
has not yet been validated.

## What Jimmy takes off your plate

| The usual chore | Jimmy's helping hand |
| --- | --- |
| "Do I actually fit this job?" | Compare the advert with your evidence, identify gaps, and help you decide whether to proceed. |
| "Which version of my CV should I use?" | Choose a baseline and draft a version that puts relevant experience first. |
| "How do I write this without sounding like a corporate chatbot?" | Draft an evidence-backed cover letter for you to review and make your own. |
| "What was that good example I used last time?" | Build a reusable career knowledge base of achievements, examples, and corrections. |
| "Did I apply there already?" | Keep applications, companies, recruiters, contacts, and activity history together. |
| "The interview is tomorrow." | Work with your assistant on research, practice answers, and preparation notes. |
| "Now they want it in German." | Use the supplied English-to-German CV translation workflow. |

**Better tailoring means selecting and explaining your real experience.**
Unsupported claims and missing information should stay visible. Jimmy can help
you make your case; you review the wording and submit the application yourself.

## Your first application, with Jimmy

### 1. Give Jimmy something true to work with

Start with your existing CV and a record of your experience: roles, achievements,
projects, skills, and concrete examples. You can expand this over time.

Your [career knowledge base](Documentation/Knowledge-Base.md) gives the assistant
material to reuse instead of making you explain your entire working life for
every advert. Correct a weak claim, add a better example, or record a new
achievement so future drafts can draw on it.

### 2. Bring a job advert—and ask for honesty

For example, take any job posting on LinkedIn:

1. Open the posting and select the **…** menu.
2. Choose **Share**, then **Copy link**.
3. Paste the link into your AI assistant and ask it to run the
   [create-application skill](.kilo/skills/create-application/SKILL.md).

Try:

> Run the create-application skill for this LinkedIn job: [paste link here].
> Assess it against my experience. Show the strongest
> matches, transferable evidence, important gaps, and unanswered questions.
> Help me decide whether it's worth applying before we draft anything.

From there, the skill handles the import and assessment automatically, creating
linked records for the role, employer, advert, and recruiter where applicable.
You review the result and decide whether to proceed. If LinkedIn blocks access
to the listing, paste the advert text instead so Jimmy can carry on.

### 3. Make the relevant experience easy to find

If the role looks worthwhile:

> Propose the best CV baseline, tailor it to this role, and draft a concise
> cover letter. Use specific evidence from my knowledge base. Flag anything
> you need me to confirm.

Review the wording, then use the local document tools to assemble and inspect
the result. The [documents guide](Documentation/Documents.md) covers layouts,
rendering, and translation. You remain the editor: check the facts, tone, and
final PDF before sending it.

### 4. Submit, record, and keep moving

Submit the application yourself. Record the date, documents sent, contacts,
and what happened next. Use the dashboard to see where things stand.

When an interview arrives, keep preparation and debrief notes with the
application. When a rejection arrives, record any useful feedback and move on.
At least you won't also be wondering which CV you sent.

## Get started

### Free tools. Some assembly required.

You can use JobJimmy with **free and open-source tools**, including
**Visual Studio Code with Kilo Code as your AI interface**, Git, Python, uv,
and LibreOffice. Obsidian is an optional, free-to-use interface for the notes
and dashboard, but isn't open source; a Markdown editor works too. The tools
can be free even though external AI usage still costs money.

**The primary interface is Kilo Code in Visual Studio Code.** Use it like any
other AI agent: describe the task, let it work with the project files and tools,
and review the result. JobJimmy supplies the job-search instructions, templates
and local automation. Other capable agents—including Claude Code, Codex and
Cursor desktop/editor or CLI interfaces—can use the same workspace. See
[interface setup and alternatives](Documentation/Getting-Started.md#kilo-code-in-visual-studio-code-primary-interface)
for setup, capabilities and billing differences. With Claude or Codex's own
billing, Jev checks need their own credentials and billing: choose OpenRouter or
TypeSafe directly. OpenRouter is recommended for access to other AI models too;
it is an individual choice. The bundled Jev script currently uses OpenRouter.

And yes: **sorry about the rather engineering-like user experience.** Jimmy
currently wears a tool belt more often than a dinner jacket. Expect Markdown
files, configuration, and a few terminal commands rather than a polished
point-and-click app. The guides will help you get set up; making this easier
is part of the project's direction.

**Start with tracking and your knowledge base. Add document automation when
you're ready.**

1. [Set up your workspace](Documentation/Getting-Started.md): tools, private
   storage, Obsidian, and the first checks.
2. [Build your career knowledge base](Documentation/Knowledge-Base.md).
3. [Add and manage applications](Documentation/Applications.md).
4. [Prepare CVs and cover letters](Documentation/Documents.md).
5. [Prepare for interviews and offers](Documentation/Interviews-and-Offers.md).

**Current status: early-stage hobby project.** Tracking and document tooling
exist. Setup involves files and terminal commands; there is no hosted service,
one-click installer, or automatic application submission.

## Privacy: Jimmy can keep a secret

Your career history is personal. A lot of work has gone into keeping the
original private data on your own systems while still letting external AI
models help with the application process.

JobJimmy uses a **reversible anonymisation layer** before sending data through
its protected workflows to external models. Identifying details are replaced
locally with stand-ins; the local mapping lets the workflow restore those
details afterwards. The model gets the material it needs to work on your
application without needing the original identities. Your real details go
back into the finished documents locally.

**Jimmy needs your story. The external model doesn't need your name.**

This is a practical privacy measure, not a promise of perfect anonymity.
Distinctive projects or combinations of career details may still identify
someone, and anonymisation can miss information. A separate assistant or tool
with direct access to your files can also send data outside this protected
route. Keep the mapping private, check what you're sharing, and use the
documented workflow. See [Privacy](PRIVACY.md) for the details.

## Costs: a little AI, a lot less admin

AI isn't free, but an application shouldn't need a coffee-sized AI budget.
Using **OpenRouter's AutoRouter with the defaults**, the project's estimate is
**about 10 cents per average application**.

Treat that as a useful ballpark, rather than a fixed price. Longer inputs,
extra revisions, different models, and provider pricing changes can alter the
bill. **One OpenRouter account for all paid AI services** is a core design
decision: application assistance, translation and Jev checks share one billing
account. No separate paid AI subscription or TypeSafe account is required for
the documented OpenRouter setup.

The idea is simple: spend a little on the repetitive work, and keep your time
for deciding where to apply, checking the result, and preparing for the
conversation that matters.

## What's under the butler's jacket?

Ordinary Markdown notes, an Obsidian workspace, a filesystem-capable AI
assistant, and local Python/LibreOffice document tools. Your job-search records
live in a separate private Git repository inside `JobSearch/`.

| Tool | What you need it for |
| --- | --- |
| Obsidian | Recommended workspace; another Markdown editor also works. |
| Dataview | Live dashboard and activity tables in Obsidian. |
| Git | The documented setup, separate public/private repositories, and privacy gate. |
| Python 3.11+ and uv | Automation scripts and privacy checks; development checks currently use Python 3.12. |
| LibreOffice Writer | Personalise ODT layouts and export PDFs locally. |
| A filesystem-capable AI assistant | Guided research, assessment, drafting, and record updates; VS Code with Kilo Code is one free, open-source setup. Manual tracking works without an assistant. |
| OpenRouter account and API key | All AI calls, including AutoRouter, optional English-to-German translation, and advisory Jev fit and document checks. |
| PyMuPDF | Optional automated PDF layout/comparison checks; still inspect documents visually. |

One OpenRouter account covers all paid AI services, including Jev; no separate
provider account is needed. Configure your assistant to use OpenRouter too.
The default setup uses separate OpenRouter keys for application
functions and Jev to control costs and privacy settings independently. You can
assign the same key to both if preferred. Follow [OpenRouter setup](Documentation/OpenRouter-Setup.md)
for account creation, guardrails, spending limits and environment variables. See [Getting started](Documentation/Getting-Started.md)
for installation and [External dependencies](Documentation/Dependencies.md)
for accounts, environment variables, and network endpoints.

Skills live in `.kilo/skills/`, but are **agent-agnostic**. If your assistant
doesn't discover a skill, ask it to read the file explicitly. It should follow
[AGENTS.md](AGENTS.md) and [PROCEDURES.md](PROCEDURES.md) when changing records.

## What works today—and what still needs building

| Capability | Current state |
| --- | --- |
| Application, company, recruiter, and activity tracking | Markdown templates and Dataview views. |
| Job advert import and fit assessment | Implemented agent skill; listing access can fail. |
| Career knowledge and learning from corrections | Private notes maintained with your assistant; no required memory service. |
| Tailored CVs | Draft/review workflow with two local rendering approaches. |
| Cover letters | Markdown drafting and local identity insertion; ODT rendering needs your own compatible template. |
| Translation | OpenRouter script for block-marked CVs, currently English to German. |
| Interview and negotiation support | Guided conversations and activity notes; dedicated skills are proposed, not installed. |
| Jev fit and document checks | Advisory CLI scaffold; uses your OpenRouter key to access Jev and requires domain tuning. Scoring quality is not yet validated. |
| Email/calendar integration, automatic reminders, Notion sync | Not implemented as project workflows. |

A blank `CV/Templates/CV Template.ott` is included. Your personal CV baselines,
identity files, and a ready-to-use cover-letter ODT are not supplied; follow
the [documents guide](Documentation/Documents.md) to prepare them.

[Jev checks](Documentation/Jev-Checks.md) supplement the existing fit/gap analysis
and check each final Markdown CV and cover letter independently. Their requests
and rubrics are editable, with anonymous input checks and separate match and
confidence scores. Treat them as a second opinion, not a hiring verdict.

## Your career history belongs in your private workspace

Keep reusable project tools public and personal job-search data private:

```text
jobjimmy/                       public tools, guides, and source templates
├── Documentation/
├── Templates/                  canonical note templates
├── CV/                         document tooling and templates
├── .kilo/skills/
└── JobSearch/                  Obsidian vault; independent private Git repo
    ├── .obsidian/              vault configuration, plugins, and UI state
    ├── Dashboard.md
    ├── Applications/
    ├── Companies/
    ├── Recruiters/             including Directory.md
    ├── Knowledge/
    ├── Templates/              personal note templates and CV baselines
    └── Outputs/
```

Open `JobSearch/` as your Obsidian vault. Put personal copies of templates there;
never enter personal details into public templates.

Keep the anonymisation mapping and original personal records in your private
workspace too. Git exclusion prevents accidental inclusion in the public
repository; it doesn't prevent an assistant, sync service, or filesystem
archive from reading the files. See [Privacy](PRIVACY.md) and the
[setup guide](Documentation/Getting-Started.md).

## Help Jimmy get better

Useful improvements, clearer guides, and bug reports are welcome. Use synthetic
examples in public issues—keep real CVs, private logs, and application records
out of them.

- [Troubleshooting](Documentation/Troubleshooting.md)
- [External dependencies](Documentation/Dependencies.md)
- [CV technical reference](CV/README.md)
- [Agentic roadmap](Documentation/Agentic-Roadmap.md)
- [Release readiness](Documentation/Release-Readiness.md)

## License and acknowledgements

JobJimmy’s original code, documentation and Markdown templates use the
[MIT License](LICENSE). See [third-party acknowledgements](THIRD_PARTY_NOTICES.md)
for dependency licenses, provider credits and the embedded CV artwork exclusion.
The CV template artwork still needs provenance and redistribution review; check
[release readiness](Documentation/Release-Readiness.md) before publishing a fork.

---

**JobJimmy. Give your applications some leverage.**
