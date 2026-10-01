# Build your career knowledge base

[Home](../README.md) · [Setup](Getting-Started.md) · Next: [Applications](Applications.md)

The knowledge base is your reusable evidence for applications and interviews.
A CV is a selective summary; the knowledge base can hold the detail behind it,
including experience omitted from your current CV and the limits of each claim.
It lives in `JobSearch/Knowledge/`, not in the public `CV/` folder.

## Start with what you already know

Gather your existing CV, project notes and a few examples you can discuss
confidently. Keep original source files private. Give your assistant only content
permitted by your chosen privacy policy; names and contact details are not needed
to discuss an achievement.

Ask:

> Help me initialise JobSearch/Knowledge/ from the career information I provide.
> Preserve sources, distinguish my statements from your interpretations, and ask
> about missing details rather than inventing them. Do not change my baseline CV.

There is currently no automatic knowledge-base importer. The assistant helps
write ordinary notes. Review the initial notes before relying on them.

## The notes the application skill expects

| Note | Put here |
| --- | --- |
| `Overview.md` | A short index of your background and links to supporting notes |
| `Evidence-and-sources.md` | Source register, provenance and boundaries on claims |
| `Experience.md` | Projects, responsibilities, decisions and outcomes you can substantiate |
| `Gaps-and-mitigations.md` | Missing or adjacent evidence, what transfers and what remains uncertain |
| `Role-fit.md` | Roles you want, motivations and working preferences |
| `CV-positioning.md` | Which personal baseline suits which role, with its Markdown/ODT paths |
| `Reasoning-profile.md` | Your reported approach to decisions and problem-solving, not an invented personality assessment |
| `Writing-guide.md` | Preferred voice and wording, plus expressions or claims to avoid |
| `Sources/` | Original supplied notes or dated records of what you told the assistant |

These are ordinary Markdown files; they do not need elaborate metadata to get
started. Put a real, concise entry in each relevant note. If information is
missing, label it unknown. Empty scaffolding is not evidence: the import skill
will treat an incomplete knowledge base as provisional.

## Record a useful experience

For each example, capture:

- **Context:** the problem and constraints.
- **Your contribution:** what you personally did, decided or led.
- **Outcome:** what happened; include numbers only if you can support them.
- **Scope:** dates, team or organisation boundaries, and who else contributed.
- **Source:** a document link or a dated note that this was reported by you.
- **Claim boundary:** what this example does not establish.

For example, a synthetic entry could say: “Led the review of a release process;
implementation was performed by the team.” That supports leadership of the change,
not a claim that you personally implemented every part of it.

A simple source register can be a table of source note, date recorded, information
supported and limitations. Keep source documents unchanged; put later corrections
in a dated note and update the curated summary.

## Let it grow during normal work

When you remember something useful:

> Add this experience to my knowledge base. Check for an existing entry, record
> the source as my statement today, and update relevant gap assessments. Show me
> the factual claims you changed. Do not revise older applications automatically.

The assistant should retrieve existing evidence before asking you to repeat it.
It should distinguish “not documented” from “cannot do”. An adjacent experience
can help address a requirement without becoming a qualification you do not have.

Interview feedback belongs first in that interview's notes. Promote reusable
learning to the knowledge base when it adds a fact, correction or preference.
Generated CV wording, mock answers and job requirements are not new career evidence.

## Memory and privacy

No external memory graph is needed. The notes remain authoritative; an agent's
chat history or automatic memory should not become a competing copy. Keep
unfinished personal task state in `JobSearch/HANDOVER.md` if useful.

Request focused retrieval for each task. The assistant does not need your entire
history to answer a question about one project. See [Privacy](../PRIVACY.md)
for model, memory and tool-transfer boundaries.

The curated notes are prepared for assistant use: they are kept free of the
identifiers listed in your private redaction policy, so they can be sent to a
remote model once the local clean check passes. Run it after each edit:

```sh
tools/py CV/Scripts/redact_md.py check JobSearch/Templates/redaction-policy.json JobSearch/Knowledge
```

A failure means an identifier slipped in; remove or generalise it before using
the note remotely. The unchanged snapshots under `Sources/` are not cleaned
automatically and stay local unless redacted.
