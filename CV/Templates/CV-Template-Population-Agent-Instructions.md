# CV Template Population Agent Instructions

## Purpose

These instructions define how an agent must populate a per-application CV document
from a structured Markdown body file and produce a finished LibreOffice Writer
document and PDF without changing the template's visual design.

The body Markdown file supplies the tailored text for three sections: Profile,
Expertise and Achievements, and Work Experience. The Writer document supplies
everything else: identity fields, photograph, permanent sections, layout,
paragraph and character styles, colours, icons, page size, margins and
pagination framework.

The merge and rendering operation must run locally. It must not send the template,
identity fields, finished CV or temporary files to another model or external service.

## Document chain

1. **`CV Template.ott`** — the distributed blank template. It is the design
   source of truth and the one-time starting point for creating a personal
   master. Never modify it.
2. **Personal master `.odt`** — the user's private working template, created by
   opening `CV Template.ott` and saving a copy. It contains the user's
   photograph, full name, contact-row values, LinkedIn hyperlink, education,
   languages and hobbies, formatted exactly as the user wants them. It still
   contains the automation-owned tokens from the tailored sections.
3. **Per-application working `.odt` and PDF** — a byte-preserving copy of the
   personal master, populated with the body Markdown for one application.

Automation copies the personal master for every application and populates only
the tailored sections. It never modifies the master or the `.ott`.

## Ownership split

| Area | Owner |
| --- | --- |
| Full name | user |
| Contact row (email, telephone, location, nationalities) | user |
| LinkedIn hyperlink target on the icon | user |
| Photograph and its frame | user (template asset) |
| Education, Languages, Sports and Hobbies sections | user |
| Fixed section headings, icons, rules, body styles, page size and margins | template |
| `{{TAGLINES}}` | automation |
| `{{PROFILE_PARAGRAPHS}}` | automation |
| `{{EXPERTISE_1_TITLE}}`, `{{EXPERTISE_1_BULLET}}` | automation |
| `{{EXPERTISE_2_TITLE}}`, `{{EXPERTISE_2_BULLET}}` | automation |
| `{{ROLE_FIRST_*}}` and `{{ROLE_REPEAT_*}}` blocks | automation |

The full name enters the template through the user's personal master, exactly
as the user typed and formatted it. The automation never replaces it. The
tagline is tailored per application and is the only element of the identity
header supplied through the input Markdown.

The user-owned items are permanent and must be preserved byte-for-byte across
every application run. The agent must never "fix", reword, reformat or replace
user-owned content, even if it looks incomplete.

## Required deliverables

For each source body Markdown file, produce:

1. An editable `.odt` document created from a copy of the personal master.
2. A PDF rendered from that `.odt` document.

The personal master `.odt` and the blank `.ott` must remain unchanged. Open the
master as a template or make a byte-preserving working copy through an ODF-aware
mechanism before making any changes, then save the working file as `.odt`.

The population tooling is `CV/Scripts/populate_cv.py` (standard library only):

```sh
python3 CV/Scripts/populate_cv.py JobSearch/Outputs/body.md JobSearch/Templates/personal-master.odt JobSearch/Outputs/output.odt \
    [--education-break keep|suppress] [--pdf] [--outdir DIR] [--strict]
```

It validates the body Markdown against this contract, copies the master
byte-preservingly, fills the automation-owned anchors, refuses to run when
identity tokens are still present, and never modifies the master or the `.ott`.
`--pdf` also exports a PDF with LibreOffice and reports the page count.
`--education-break suppress` removes the forced page break before Education for
runs where Work Experience flows onto page 3. When the agent performs the merge
by hand instead, it must follow the identical steps and checks below.

## Markdown input format

The body Markdown must follow the structure below. Optional front matter may
carry only the taglines list:

```markdown
---
taglines:
  - "Engineering Leadership"
  - "Embedded and Connected Products"
---

# Profile

First profile paragraph.

Second profile paragraph.

# Expertise and Achievements

## Subgroup Title One

- First achievement.
- Second achievement.
- Third achievement.

## Subgroup Title Two

- First technology or delivery achievement.
- Second technology or delivery achievement.

# Work Experience

## Role 01

Company: Example Company GmbH
Title: Senior Engineering Director
Dates: September 2019 - October 2024
Location: Example City, Country

- Achievement or responsibility.
- Achievement or responsibility.
- Achievement or responsibility.

## Role 02

Company: Earlier Company GmbH
Title: Co-founder and Engineering Director
Dates: January 2014 - August 2019
Location: Example City, Country

- Achievement or responsibility.
- Achievement or responsibility.
```

### Front matter

- Only the optional `taglines` key is accepted. It must be a list of two or
  three short phrases, normally 2-5 words each, that together (including the
  ` | ` separators) fit the tagline area using the wrapping rules below.
- Reject any other front-matter key. Identity values (full name, email, phone,
  location, nationalities, LinkedIn URL) are not input here; they live in the
  personal master and are never supplied through Markdown.

### Heading hierarchy

The following level-one headings are mandatory and must occur once, in this
order:

1. `# Profile`
2. `# Expertise and Achievements`
3. `# Work Experience`

Under `# Expertise and Achievements`, exactly two level-two headings are
required. Their text becomes the two visible subgroup titles on page 1. The
subgroup names may change for each application.

Under `# Work Experience`, use consecutively numbered level-two headings:
`## Role 01`, `## Role 02`, and so forth. The role heading is structural and is
not printed. Each role must contain the four labelled fields `Company`,
`Title`, `Dates` and `Location`, followed by a Markdown bullet list.

Do not add arbitrary headings. Do not use Markdown tables, block quotations,
nested lists, HTML, code blocks, images or footnotes in the content file.

### Allowed inline formatting

The default input is plain text. The merge agent may support Markdown
`**bold**` and `*italic*` inside profile paragraphs and bullets only if it can
map them to character formatting without disturbing the template's paragraph
styles. If inline formatting is not implemented reliably, reject it during
validation rather than printing Markdown markers.

Do not accept embedded hyperlinks in narrative text.

## Content requirements and length budgets

The rendered three-page result is the final authority. The limits below are
drafting budgets intended to produce a reliable first render; they do not
replace render-and-inspect validation. They apply to the tailored sections
only. Education, Languages and Sports and Hobbies are populated by the user in
the master and are not addressed by these budgets.

### Taglines

- Two or three short phrases, normally 2-5 words each.
- Each rendered line must be at most 50 characters.
- Lines break at tag boundaries only: a tag is never reworded, reordered,
  truncated or split across lines to make it fit. When a tag cannot fit within
  50 characters on its own, report it and leave the tag unchanged; the main-body
  rule set decides whether to shorten the tag.
- Keep the tags in the order supplied. Tags that fit together on one line are
  joined with ` | `; a line break replaces the separator where the line wraps.
- Do not shrink the tagline font to accommodate excessive text.

### Profile

- Supply 3 or 4 paragraphs.
- Target 130-190 words in total.
- Each paragraph should normally contain 30-55 words.
- Use compact prose, not bullets.
- Establish the candidate's level, scope and strongest match to the target role.
- Prioritize evidence and outcomes over generic claims.
- Avoid repeating the expertise bullets word for word.
- The complete profile must remain in the Profile area of page 1 and must not
  push the Expertise and Achievements section onto page 2.

### Expertise and Achievements

- Supply exactly two subgroup headings.
- Keep each subgroup title to approximately 30 characters or fewer so it remains
  on one line.
- Supply 3-5 bullets per subgroup.
- Target 15-28 words per bullet.
- Each bullet should normally occupy one or two rendered lines.
- Across both groups, target approximately 140-220 words.
- A bullet should express a coherent capability, achievement or evidence
  cluster; it must not be a keyword dump.
- Preserve factual metrics and scope. Do not invent numbers or responsibilities.
- Both subgroups and all their bullets must remain on page 1.

### Work experience

- List roles in reverse chronological order.
- Keep each `Company`, `Title` and `Dates` value short enough for the existing
  three-part role heading to remain on one line.
- Use a consistent date convention throughout the document, for example
  `Sep 2019 - Oct 2024`.
- `Location` appears on a smaller separate line beneath the role heading.
- Use 3-5 bullets for recent or highly relevant roles.
- Use 1-3 bullets for older or less relevant roles.
- Target 15-30 words per bullet and normally no more than two rendered lines.
- Begin bullets with direct evidence: led, built, delivered, reduced, increased,
  introduced, scaled, transformed or another accurate action.
- Avoid first-person pronouns.
- Avoid repeating responsibilities already obvious from the job title.
- A role heading, its location and its first bullet must stay together.
- Avoid leaving a single bullet from one role isolated at the top or bottom of a
  page. If a role must split across pages 2 and 3, leave at least two bullets on
  each page where practical.

## Mapping Markdown to template anchors

Populate the template as follows:

| Markdown source | Template target | Required treatment |
| --- | --- | --- |
| `taglines` (front matter) | Bookmark `TAGLINES`; token `{{TAGLINES}}` | Join tags with ` | `, wrap at tag boundaries so no line exceeds 50 characters using explicit line breaks; preserve tag wording and order; never split or reword a tag. |
| Profile paragraphs | Bookmark `PROFILE_CONTENT`; token `{{PROFILE_PARAGRAPHS}}` | Use the prototype paragraph style for every supplied paragraph and remove the token. |
| First expertise heading | Bookmark `EXPERTISE_1_TITLE`; token `{{EXPERTISE_1_TITLE}}` | Replace text only; preserve blue subgroup style. |
| First expertise bullets | Bookmark `EXPERTISE_1_BULLETS`; token `{{EXPERTISE_1_BULLET}}` | Clone the prototype list item for every bullet while preserving the list style. |
| Second expertise heading | Bookmark `EXPERTISE_2_TITLE`; token `{{EXPERTISE_2_TITLE}}` | Replace text only; preserve blue subgroup style. |
| Second expertise bullets | Bookmark `EXPERTISE_2_BULLETS`; token `{{EXPERTISE_2_BULLET}}` | Clone the prototype list item for every bullet while preserving the list style. |
| First work role | Bookmarks beginning `ROLE_FIRST`; tokens beginning `{{ROLE_FIRST_...}}` | Populate the first-role prototype, which intentionally has no preceding separator line. |
| Remaining work roles | Bookmarks beginning `ROLE_REPEAT`; tokens beginning `{{ROLE_REPEAT_...}}` | Clone the complete repeat-role prototype for roles 2 onward; preserve its heading style and separating top margin. |
| User-owned identity and permanent sections | Name paragraph, contact table cells, LinkedIn icon, portrait, Education, Languages, Sports and Hobbies | Verify present and populated; do not modify. |

The agent should locate bookmarks first and verify that the expected placeholder
token is present in the bookmarked paragraph or block. The tokens provide a
deterministic fallback and make incomplete merges easy to detect. The agent must
preserve the surrounding styles, anchored graphics and tables. It must not
reconstruct the document from scratch or replace entire styled paragraphs when
replacing only their text is sufficient.

Block extents for cloning: the repeat-role prototype consists of the paragraph
carrying the `ROLE_REPEAT_START` bookmark, the following `ROLE_REPEAT_LOCATION`
paragraph and its bullet list, up to the paragraph carrying the
`EDUCATION_PAGE_BREAK` bookmark, excluding trailing empty spacer paragraphs.
Role separation comes from the repeat heading's own top margin; trailing spacers
stay outside the cloned block. The profile prototype paragraph and the
expertise prototype list items are consumed by the merge (cloned per supplied
item, then removed), together with their bookmarks.

## Population procedure

### 1. Validate the input

Before editing the document:

- Parse the optional front matter and the Markdown structure.
- Verify all required headings and their order.
- Reject unknown front-matter keys without silently ignoring them.
- Verify role numbering is consecutive.
- Reject duplicate scalar fields within a role.
- Reject unsupported Markdown structures.
- Check the initial content against the length budgets.
- Report specific validation errors rather than silently discarding content.

### 2. Create the working document

- The calling workflow supplies the personal master `.odt` explicitly. Never
  open the blank `.ott` for a merge, and never edit the master in place.
- Create a byte-preserving working copy through an ODF-aware mechanism and save
  it as `.odt` immediately.
- Verify that the automation-owned tokens are still present in the working copy
  and that the user-owned fields are populated and contain no `{{...}}` tokens.
- Use LibreOffice automation or another ODF-aware editing method that preserves
  styles, tables, anchored objects and hyperlinks.
- Do not use Pandoc or a from-scratch document generator for the merge.

### 3. Populate fixed fields

- Resolve the `TAGLINES` bookmark, verify the expected token, and replace only
  the placeholder text portion.
- Preserve the contact table, icons, paragraph alignment and character styles.
- Confirm that the user's name, contacts, LinkedIn target, photograph,
  education, languages and hobbies are untouched.

### 4. Populate variable-length sections

- Use the existing styled paragraphs and list items as prototypes.
- Clone style-bearing paragraphs when additional profile paragraphs or bullets
  are needed.
- Delete unused prototype and placeholder paragraphs cleanly.
- Do not leave empty bullet markers, placeholder brackets, ellipses or
  instructional text in the result.
- Keep fixed section headings and their icons unchanged.

### 5. Apply pagination rules

The intended result is exactly three pages:

- Page 1 contains the identity header, Profile, and both Expertise and
  Achievements groups.
- Work Experience starts on page 2.
- Work Experience may continue onto the upper part of page 3.
- Education, Languages, and Sports and Hobbies are populated in the master and
  must remain on page 3, unchanged.

The template contains a forced page break before Work Experience and a second
forced break in the paragraph bookmarked `EDUCATION_PAGE_BREAK`. Preserve the
Work Experience break. Handle `EDUCATION_PAGE_BREAK` conditionally:

- If Work Experience finishes on page 2, keep or insert the Education page
  break so the user's Education section starts page 3.
- If Work Experience has already flowed onto page 3, remove or suppress the
  forced Education break so the user's remaining sections follow the experience
  on page 3.
- Never allow the Education break to create a fourth page.

Keep every section heading with at least the first following content paragraph.
Keep each role heading with its location and first bullet.

### 6. Resolve overflow through editing, not design damage

The main-body overflow rule set is still being defined; until it is finalised,
apply this fallback:

- If the merged body cannot fit into page 2 and the upper part of page 3 without
  pushing the user's Education, Languages or Sports and Hobbies sections off
  their page or creating a fourth page, stop and report which section exceeds
  its available space. Do not shorten or delete text to make it fit, and never
  modify the user's permanent content.

In all cases, never respond to overflow by:

- reducing body text below the template's existing size;
- reducing margins;
- scaling icons or the portrait;
- changing the page size;
- compressing line spacing below the template values;
- hiding content outside page boundaries;
- allowing a fourth page.

### 7. Render and visually verify

After population:

1. Save the `.odt`.
2. Export it to PDF using LibreOffice.
3. Render every PDF page to an image.
4. Inspect all three pages at full resolution using local or explicitly approved
   vision processing. Otherwise request human visual review and mark it pending;
   do not upload private page images to satisfy this step. See `PRIVACY.md`.
5. Correct mechanical defects and repeat the render. Report text overflow without
   shortening approved wording; wait for the user's revision or specific authorisation.

The inspection must confirm:

- exactly three pages;
- no text overlap or clipping;
- no section on the wrong page;
- no heading separated from its content;
- no role heading separated from its location or first bullet;
- no empty bullets;
- no unexpected fourth page;
- no large avoidable blank region caused by a misplaced break;
- contact details fit within their cells;
- the name remains single-line and taglines wrap only at tag boundaries;
- role heading columns remain legible;
- Education, Languages, and Sports and Hobbies all fit on page 3;
- the portrait and every section icon remain correctly positioned;
- the LinkedIn icon remains clickable and points to the user's own profile;
- the user's identity and permanent sections are unchanged from the master.

## Final validation

Before returning the files, verify structurally as well as visually:

- Search the finished document content for `{{`, `}}`, `ROLE_FIRST_`,
  `ROLE_REPEAT_`, `EXPERTISE_`, and every other merge token. No visible merge
  token may remain.
- Confirm the output contains every supplied role and no extra prototype role.
- Confirm every supplied bullet appears once.
- Confirm the user-owned sections and identity fields match the personal master
  and contain no supplied Markdown text.
- Confirm the `.odt` opens successfully in LibreOffice.
- Confirm the PDF page count is exactly three.
- Confirm the personal master `.odt` and the blank `.ott` have not changed.
- Confirm temporary files, private Markdown inputs, `.odt` outputs and PDFs are
  not added to a source repository unless the user explicitly requests that.

## Writing rules for an upstream tailoring agent

If the same agent also creates the body Markdown content, it must follow these
additional rules:

- Use only facts supported by the candidate evidence database or explicitly
  supplied by the user.
- Never invent metrics, team sizes, reporting lines, budgets, technologies or
  qualifications.
- Tailor selection and emphasis to the target role without changing the
  underlying facts.
- State genuine gaps honestly and use adjacent evidence rather than claiming
  direct experience that does not exist.
- Prefer concrete scope, action and outcome over adjectives.
- Mirror useful terminology from the job description without copying entire
  phrases mechanically.
- Keep the language confident, direct and concise.
- Write the complete body Markdown in the document language first. If
  translation is required, translate the structured Markdown while preserving
  its headings, subgroup names, role numbering, field labels and bullets so the
  merge contract remains valid. Identity and permanent sections are not part of
  the body Markdown; they come from the language-specific personal master. The
  block-based `CV/Scripts/translate.py` operates on block-marked reference CVs,
  not on this body format, so translate the body before population and review
  the result against the source.
- Proper names, product names and qualifications must not be translated unless
  an established localized name exists.

## Privacy boundary

The population operation is a local rendering step. The merge agent must not
call an external model, web service, search tool or telemetry service with the
private Markdown or template content.

In a privacy-preserving tailoring workflow, external models should produce
pseudonymised narrative content containing stable placeholders. The local merge
stage may then resolve employer placeholders and exact dates immediately before
rendering. The identity mapping and populated output must remain outside the
model-accessible working directory. The user's master document, which contains
identity and permanent sections, must never be sent to an external model.