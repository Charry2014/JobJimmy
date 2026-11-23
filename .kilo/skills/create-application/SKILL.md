---
name: create-application
description: Create or update linked job application records from a job URL or an advert or email captured from the clipboard, including sourced fit assessment and positioning proposals. Use for imports, not standalone document rendering or interview preparation.
---

# Create application

Use the shared project `AGENTS.md`, regardless of model family or Kilo mode.
All filesystem paths in the workflow are relative to the public project root;
Obsidian links and Dataview paths are relative to `JobSearch/`.

Before *reading* any private advert, evidence or record into a hosted model,
follow `PRIVACY.md#remote-drafting-reversible-markdown-tags`: run local
redaction with a locally reviewed policy, then read only checked safe Markdown.
This applies to initial import/research and later document work alike. Never
expose raw company/recruiter names, contacts, private filenames, identity JSON
or Git diffs in tool output or chat. If the policy is unreviewed or the transfer
cannot be prepared safely, stop the remote research phase and use a truly local
workflow; do not read the original advert to investigate the blocker.
Before returning private evidence to a model, check `PRIVACY.md` and the private
agent guide. Never invent career claims, publisher identity or submission history.
Do not send messages or submit an application as part of importing it.
Never ask for advert or email text in chat: the user copies it to the clipboard
and `tools/py CV/Scripts/jobflow.py capture --clipboard` archives it locally and
writes the safe copy. Records, note sections and safe bundles are `jobflow.py`
commands (see the import workflow).

Read [the import workflow](references/import.md) for advert retrieval, deduplication,
linked records, the required fit table and verification. Its **Step 0 — Environment
verification** runs first, before any private content is read: it reports missing
tools, the private tree and API keys, and requires an explicit user decision for
each missing key. Use `python3 tools/check_env.py` (standard library only, so it
also detects a missing uv); it prints credential presence
only, never values. Read `PROCEDURES.md` and
only the note templates needed for the records being written. Public `Templates/`
is canonical; existing application notes are evidence, not specifications.

For a combined import and document request, complete the import then use
`Documentation/Agent-Reference/Documents.md` and the selected rendering workflow.
For a standalone fit reassessment, use that reference's knowledge and scoring
sections without importing or resetting records. Missing private inputs block
only the work that depends on them; complete the supported parts and report gaps.
