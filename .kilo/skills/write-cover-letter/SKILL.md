---
name: write-cover-letter
description: Draft a cover letter in plain Obsidian Markdown, then locally merge it with a compatible private Writer template and export PDF after wording approval. Use for letter creation and rendering, not for sending it.
---

# Write a cover letter

For rendering requests, follow
`Documentation/Agent-Reference/Documents.md#rendering-scope-and-completion`.
When "render to PDF" follows work on both CV and cover letter, render both using
their respective skills unless the user narrows the scope. This skill produces
only the letter; also run `.kilo/skills/tailor-cv/SKILL.md` for the CV.

Follow root `AGENTS.md`, `PRIVACY.md`, private `JobSearch/AGENTS.md` and
`Documentation/Agent-Reference/Documents.md` (cover-letter and knowledge
sections). Commands run from the public project root; personal files stay in
`JobSearch/`. `JobSearch/` is gitignored, so the `glob`/`grep` tools return
nothing there; locate the letter template pair with `ls`/`find` or the exact
path (root `AGENTS.md` "Locating CV and cover-letter templates" lists the
`letter-template-<lang>.odt`/`letter-anchors-<lang>.json` pairs) and never treat
an empty glob as a missing template.
Never send a completed letter, identity JSON or PDF to a
remote model. Run `tools/py CV/Scripts/jobflow.py bundle <slug>` and read only
the checked safe copies it prints (advert, notes, company research, knowledge
articles and the current drafts with the user's latest edits). Tokens such as
`@@EMPLOYER_03@@` are stable across all safe copies: copy them exactly, combine
them freely and never invent one. Write the prose to the bundle's `out/` folder
under its `CV/` file name and run `tools/py CV/Scripts/jobflow.py restore
<slug>`; restore refuses a draft the user changed since the bundle (bundle
again and revise their version). Follow
`PRIVACY.md#remote-drafting-reversible-markdown-tags`; the user accepts residual
identity inference from redacted career history. Never send the token registry
or a restored letter back to the model. Read
`CV/README.md#cover-letters-plain-markdown-to-odtpdf`
for syntax and failure modes.

1. **Check inputs.** Identify the application and read `document_language` in
   its linked research note. Reuse that research decision (`en`, `de`, etc.)
   for final output. For `de`, follow
   `Documentation/Agent-Reference/Documents.md#english-drafting-before-german-translation`:
   draft and revise English first, then translate the agreed source. Do not
   choose by template filename or company
   location. For an older note without the field, derive it once from the
   advert and explicit application instructions, record the code and evidence
   there, then proceed. Clarify only genuinely conflicting instructions.
   Consult only checked redacted copies of relevant researched company facts and evidence from
   `JobSearch/Knowledge/Overview.md`, `Evidence-and-sources.md`,
   `Writing-guide.md` and relevant experience. Unknown recipient details
   remain generic; do not invent names, dates, achievements or contact details.
2. **Save the draft as an editable Markdown file.** Every drafting or revision
   request must restore the actual `.md` file into
   `JobSearch/Applications/<application-slug>/CV/` (`jobflow.py restore`) before presenting it for
   review; a chat-only draft is not complete. The user edits this file in
   Obsidian. Read its latest contents through the privacy workflow before
   revising so their edits are retained. Overwrite the same working file on each
   revision; do not create `(1)`, `-v2`, timestamped or backup draft copies. Git
   provides history. Keep one current file per document and language, including
   separate English and German prose files when translating. Save the prose even
   when rendering or Jev is unavailable; report any actual write failure rather
   than claiming it was saved. A new draft starts from the public starter `CV/Templates/Cover-Letter.md`,
   written to `out/<slug>-cover-letter-prose.md` (for a German final:
   `<slug>-cover-letter-prose-en.md`, preserved through translation). Retain exactly the
   eight English `##` field headings: `Sender`, `Date`, `Recipient`, `Subject`,
   `Salutation`, `Body`, `Closing`, `Signature`. Write the *field values* in
   English during preparation for a German application, otherwise in the
   application's language; use first-person natural prose and blank lines
   between body paragraphs. The renderer does not support lists, inline
   Markdown, YAML, HTML or links in this letter. Replace all placeholders
    except `{{local sender}}` and `{{local signature}}` in their respective
    sections; replace the starter's synthetic Sender and Signature lines with
    those placeholders before prose review. They remain until local identity
    insertion. Use one line each
   for date, subject, salutation and closing, and set a deliberate date.
3. **Review prose first.** For German applications, work through English evidence
   and wording review rounds with user feedback until agreed for translation.
   If both documents were requested, finish both English reviews first. Translate
   the agreed prose to `<slug>-cover-letter-prose-de.md` under the redaction
   workflow, keeping the eight English field headings and local identity
   placeholders. Review German against English and obtain German wording approval
   or an explicit render request before step 4 (rendering). Subsequent commands use generic
   filenames: hydrate/render the approved German prose for `de`, retaining the
   English source. `translate.py` does not accept cover letters.
   At English review and again at final German review (or final review for other
   languages), run the cover-letter check in `Documentation/Jev-Checks.md` on its checked anonymous
   copy, the anonymous advert and complete required-points checklist. Send this
   letter alone before identity restoration/hydration; do not include the CV.
   Present Jev's match score, confidence and partial/missing/unclear points with
   the draft. Recheck after substantive wording changes; report unavailable
   checks explicitly. Record the report with the document activity per
   `PROCEDURES.md`, outside the letter text. Check the factual claims, specific motivation,
   recipient, language, signature plan and length with the user. Do not render
   for every revision. Update the existing draft in place rather than
   reinitialising it or keeping revision copies.
4. **Render with checks.** Run
   `tools/py CV/Scripts/jobflow.py render <slug> --letter`. It reads
   `document_language` from the research note and uses only the validated pair
   for it (`letter-template-<lang>.odt` with `letter-anchors-<lang>.json`; the
   unsuffixed legacy pair is never used, and a language without a pair stops).
   It checks the local identity without printing it, hydrates the complete
   private letter (`<slug>-cover-letter.md`), renders the ODT and exports the
   PDF only if it is exactly one page, making the one allowed
   `--compact-title-gap` retry itself. It stops when:
   - **the complete letter was edited after its prose:** carry those edits into
     the prose file through the bundle, then rerun;
   - **a final PDF exists:** rerun with `--replace` once the user approves;
   - **the letter still overflows:** ask the user how to proceed; never shrink
     text, margins or fonts, move blocks or trim prose on your own;
   - **the identity is missing or invalid:** request local setup; never derive
     contacts from a CV baseline (a redacted `[EMAIL]` there is not evidence)
     and never fabricate them.
   Inspect the one-page PDF locally for omitted text, address, signature and
   the bottom-right linked LinkedIn icon; keep the Markdown and ODT. Never call
   `soffice` directly. If rendering or page counting cannot be verified,
   report it as blocked, not completed.
5. **Record real documents.** For rendering requests, verify the current approved
   letter's ODT and PDF both exist and passed the required checks. If rendering includes a CV,
   complete its rendering workflow too and account for all four outputs before
   reporting the combined task complete. Report any missing or blocked output
   explicitly; a finished letter is not a finished CV-and-letter request.
   Link only existing files from the application
   and use `PROCEDURES.md` plus the activity template for a `document-added`
   note. Run private diff checks and the public privacy screen; report what was
   generated and what remains unverified. Do not submit or email the letter.
