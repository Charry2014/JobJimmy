---
name: write-cover-letter
description: Draft a cover letter in plain Obsidian Markdown, then locally merge it with a compatible private Writer template and export PDF after wording approval. Use for letter creation and rendering, not for sending it.
---

# Write a cover letter

Follow root `AGENTS.md`, `PRIVACY.md`, private `JobSearch/AGENTS.md` and
`Documentation/Agent-Reference/Documents.md` (cover-letter and knowledge
sections). Commands run from the public project root; personal files stay in
`JobSearch/`. Never send a completed letter, identity JSON or PDF to an
remote model. Before reading any advert, employer research or career evidence
into a hosted agent, use `CV/Scripts/redact_md.py prepare` locally on each
Markdown source with a private policy listing all explicit identifiers,
including company names and addresses. Read only safe copies, preserve tags
in the drafted prose, and run `redact_md.py restore` locally before rendering.
Follow `PRIVACY.md#remote-drafting-reversible-markdown-tags`; the user accepts
residual identity inference from redacted career history. Never send the token
mapping or a restored letter back to the model. Read
`CV/README.md#cover-letters-plain-markdown-to-odtpdf`
for syntax and failure modes.

1. **Check inputs.** Identify the application and read `document_language` in
   its linked research note. Reuse that research decision (`en`, `de`, etc.)
   for drafting and rendering; do not choose by template filename or company
   location. For an older note without the field, derive it once from the
   advert and explicit application instructions, record the code and evidence
   there, then proceed. Clarify only genuinely conflicting instructions.
   Consult only checked redacted copies of relevant researched company facts and evidence from
   `JobSearch/Knowledge/Overview.md`, `Evidence-and-sources.md`,
   `Writing-guide.md` and relevant experience. Unknown recipient details
   remain generic; do not invent names, dates, achievements or contact details.
2. **Start a private plain-Markdown draft.** Run
    `uv run --no-project python CV/Scripts/cover_letter.py init
   JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter-prose.md`
   only if that file does not exist. Open it in Obsidian and retain exactly the
   eight English `##` field headings: `Sender`, `Date`, `Recipient`, `Subject`,
   `Salutation`, `Body`, `Closing`, `Signature`. Write the *field values* in
   the application's language; use first-person natural prose and blank lines
   between body paragraphs. The renderer does not support lists, inline
   Markdown, YAML, HTML or links in this letter. Replace all placeholders
    except `{{local sender}}` and `{{local signature}}` in their respective
    sections; replace the starter's synthetic Sender and Signature lines with
    those placeholders before prose review. They remain until local identity
    insertion. Use one line each
   for date, subject, salutation and closing, and set a deliberate date.
3. **Review prose first.** When the final Markdown prose is ready, run the
   cover-letter check in `Documentation/Jev-Checks.md` on its checked anonymous
   copy, the anonymous advert and complete required-points checklist. Send this
   letter alone before identity restoration/hydration; do not include the CV.
   Present Jev's match score, confidence and partial/missing/unclear points with
   the draft. Recheck after substantive wording changes; report unavailable
   checks explicitly. Record the report with the document activity per
   `PROCEDURES.md`, outside the letter text. Check the factual claims, specific motivation,
   recipient, language, signature plan and length with the user. Do not render
   for every revision. Preserve existing drafts rather than reinitialising.
4. **Choose the exact language pair and check identity.** For `en` use
   `JobSearch/Templates/letter-template-en.odt` and
   `JobSearch/Templates/letter-anchors-en.json`; for `de` use
   `letter-template-de.odt` and `letter-anchors-de.json` in that folder.
   The unsuffixed `letter-template.odt` / `letter-anchors.json` is a legacy
   **German alias, not a language-neutral default**. Never use it for English.
   `letter-example-original.odt` is a private archive, not a rendering
   template; `letter-template.fodt` is obsolete, and any
   `letter-template-smoke.md` is test input, not an application draft. For a
   language without a validated pair, keep the prose draft and use local
   Writer assembly or report the missing render pair; never silently substitute
   another language. The local
   `JobSearch/Templates/letter-identity.json` contains Sender and Signature
   arrays extracted from the user's example. From the public project root run
   `uv run --no-project python CV/Scripts/cover_letter.py check-identity
   JobSearch/Templates/letter-identity.json`. A successful check confirms a
   usable name, phone and email without printing them. A redacted CV baseline
   showing `[EMAIL]` is **not** evidence the letter identity is absent or lacks
   an email; do not derive contacts from CV baselines. Do not read or print the
   JSON into hosted context. If this command fails in another checkout, verify
   that checkout has the attached private `JobSearch/` repository. Only if its
   identity is genuinely missing or invalid should you request local setup or
   a complete private Markdown letter. Never fabricate contacts.
5. **Hydrate locally, then render.** Once the identity JSON exists, create the
   full private Markdown and preserve the prose draft:

   ```sh
    uv run --no-project python CV/Scripts/cover_letter.py hydrate-identity JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter-prose.md JobSearch/Templates/letter-identity.json JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.md
    ```

    Render the hydrated Markdown using the pair selected in step 4. For `en`:

    ```sh
    uv run --no-project python CV/Scripts/cover_letter.py render JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.md JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.odt --template JobSearch/Templates/letter-template-en.odt --config JobSearch/Templates/letter-anchors-en.json
    ```

    For `de`:

    ```sh
    uv run --no-project python CV/Scripts/cover_letter.py render JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.md JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.odt --template JobSearch/Templates/letter-template-de.odt --config JobSearch/Templates/letter-anchors-de.json
    ```

   `hydrate-identity` refuses to overwrite a prior complete draft: review and
   deliberately version an existing file before repeating. The full Markdown
   signature must contain name, phone and email, with contacts below the name.
   Alternatively render the prose file using `render ... --identity
   JobSearch/Templates/letter-identity.json` when a complete Markdown copy is
   not required; prefer retaining all three formats for an application.
6. **Export only one page and inspect.** Do not call `soffice` directly for a
   final letter. Run the guarded local exporter, which writes the final PDF
   only when it can verify exactly one page:

   ```sh
   uv run --no-project python CV/Scripts/cover_letter.py export-pdf JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.odt JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.pdf
   ```

    An overflow keeps the ODT and writes **no final PDF**. Make exactly one
    spacing retry: rerun the **same** language-specific `render` command from
    step 5 with `--compact-title-gap` appended, using the **same** approved
    Markdown and ODT output path. This removes only the template's empty
    paragraph between the Position/Subject title and the salutation (the
    two-line-looking gap); it does not edit prose or search for other space.
    Run the **same** `export-pdf` command once more. If it still has more than
    one page, **stop and ask the user how to proceed**; do not search for other
    whitespace, shrink text/margins/font, move blocks or trim prose on your
    own. If the template lacks that exact gap, the option fails closed: stop
    and ask instead of improvising. Existing final PDFs are never silently
    overwritten. Inspect
   the one-page PDF locally for omitted text, address, signature and the
   bottom-right linked LinkedIn icon; keep the Markdown and ODT. If rendering
   or page counting cannot be verified, report it as blocked, not completed.
7. **Record real documents.** Link only existing files from the application
   and use `PROCEDURES.md` plus the activity template for a `document-added`
   note. Run private diff checks and the public privacy screen; report what was
   generated and what remains unverified. Do not submit or email the letter.
