# Work with applications

[Home](../README.md) · [Knowledge base](Knowledge-Base.md) · Next: [Documents](Documents.md)

One application represents one opportunity. It links to a company, an advert
research note and, where relevant, a recruiter. Dated activity notes record what
happened without overwriting the history.

## Add a job with an assistant

> Use .kilo/skills/create-application/SKILL.md to add this opportunity: [paste the
> job URL or advert text]. Check for duplicates, assess it against my knowledge
> base, and propose CV positioning and a cover-letter approach. Do not create
> document drafts or submit anything yet.

The skill should return an evidence-based fit assessment, requirements and gaps,
a baseline proposal, a language decision recorded as `document_language` on the
linked research note with its evidence under **Research notes**, and links to
the notes it created. CV and letter preparation reuse this decision rather
than selecting a language from the employer's location or template filename.
A numeric fit score is a judgement with uncertainties, not a prediction of success.

After that analysis, the assistant runs a separate [Jev fit check](Jev-Checks.md)
on the anonymous analysis and job description. It shows Jev's match score and
confidence alongside the existing assessment and links the report from research
notes. Missing setup or a failed call is shown as unavailable, never as a score.

If the listing cannot be fetched, paste the advert text. A link-only import may
save a labelled summary rather than a complete original because access or
reproduction rights are limited. `advert_captured` is filled only when the full
original is actually saved. Keep later research separate from the original wording.

If a recruiter advertises an undisclosed client, the recruiter is not the employer.
The company link can remain blank until the client is known. Re-imports should
enrich existing records rather than create duplicates or reset their status.

## Add a job manually

The example below is fictional. Use your actual role information only inside
`JobSearch/`.

1. Create `JobSearch/Applications/2026-09-example-engineering-lead/` and its
   `Activities`, `CV` and `Attachments` subfolders.
2. Create `2026-09-example-engineering-lead.md` inside that folder, and insert
   [Templates/Application.md](../Templates/Application.md) with Obsidian Templates.
3. Set the title, position, source URL and known fields. Start with
   `status: researching`, `priority: medium` and `next_action: Send Application`.
   Leave unknown dates and fit blank.
4. Create the company note from [Templates/Company.md](../Templates/Company.md)
   in `JobSearch/Companies/`. Set the application company's property to its
   quoted wikilink and add the application to the company's Applications list.
5. Create the advert note under `Activities/` using
   [Templates/Research.md](../Templates/Research.md). Use the application slug
   plus `-research.md` for its filename. Set its `application` property to the
   exact application note, then set the application's Job advert link to it.
6. Add a recruiter note from [Templates/Recruiter.md](../Templates/Recruiter.md)
   if relevant. Reuse the same agency/person note for later applications.

The application link for this synthetic example is:

```yaml
application: "[[Applications/2026-09-example-engineering-lead/2026-09-example-engineering-lead]]"
```

When copying templates manually, replace every `{{title}}` and date placeholder,
including those inside the Dataview query. Templates do not create linked files
for you. A copied research template's title is not the parent application slug;
set its parent link explicitly.

**Check:** the application appears on `Dashboard.md`, and its advert research
appears in its Activity table. If not, see [Troubleshooting](Troubleshooting.md).

## Track progress

| Status | Use when |
| --- | --- |
| `researching` | Assessing the opportunity |
| `preparing` | Preparing the application |
| `applied` | The application was actually submitted |
| `interviewing` | In the interview process |
| `offer` | An offer has been received |
| `rejected` | A rejection was received |
| `withdrawn` | You withdrew |
| `closed` | Otherwise no longer active |

Keep the next action short: normally `Send Application`, `Await Response` or
`Interview Prep`. Set `next_action_date` when you know a date; do not invent one.
Dates in properties are `DD-MM-YYYY`; dated filenames use `YYYY-MM-DD`.

The dashboard hides rejected, withdrawn and closed applications by default.
Set its `include_closed_applications` property to `true` to show them. Tables
are views: change the underlying note's properties, not the table cells.

## Record a submission

When both final PDFs have been checked, use
`.kilo/skills/prepare-send-files/SKILL.md` to make recruiter-friendly copies in
the application's private `CV/` folder. Keep the approved originals; preparing
copies does not send them or change application status.

Submit through the employer's chosen route yourself. Then ask:

> Record that I submitted this application on [date] through [channel]. Link the
> documents I actually used. Set it to applied and awaiting response. Do not
> invent a confirmation reference or follow-up date.

This should create a `kind: apply` activity and update `status`, `date_applied`
and `next_action`. A document draft or rendered PDF does not establish submission.
Manual steps follow [Recording a submission](../PROCEDURES.md#recording-an-application-submission).

## Record other events

Use [Templates/Activity.md](../Templates/Activity.md) under the application's
`Activities/` folder. Set the exact parent link, action date, `kind` and a list of
existing documents (`documents: []` if there are none).

| Event | Activity kind |
| --- | --- |
| A message actually sent | `follow-up` |
| A draft or document added | `document-added` |
| Interview preparation | `interview-preparation` |
| Interview discussion and outcomes | `interview-notes` |
| Other observation, including no response | `other` |

Writing a follow-up draft is not a sent follow-up. Silence is not a rejection.
Activities do not automatically change the application's fields; update them
explicitly when warranted, using [the procedures](../PROCEDURES.md).

## Review the pipeline each week

Open the dashboard, check upcoming dates, review unanswered applications and
identify drafts waiting for your review. You can ask an assistant to suggest next
actions, but there is no background reminder or automatic email service.

Check private changes before backing them up:

```sh
git -C JobSearch status
```

Commit/push the private repository separately. Never publish a whole vault archive
as the public project.
