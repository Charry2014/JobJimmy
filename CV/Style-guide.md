# CV layout and style guide

**Make best use of the available space.** Present relevant evidence clearly,
avoid unnecessary repetition, and keep every page comfortable to read. Do not
make pages look crammed. Avoid more than five lines of empty space at the bottom
of any page.

## Edits and tailoring

Choose one reference in [[CV/References/README|the references index]] and copy it
before editing, using its matching document template. The supplied CV is the
starting text, not just a formatting shell. Do not substitute another
application's draft or combine baselines into a new CV.

Preserve the vast majority of the wording, sentence structure, emphasis and detail.
Tailor only specific points that relate to concrete job requirements: adjust a
phrase, foreground a relevant existing achievement or add a short supported detail.
Leave unrelated text unchanged. Do not rewrite the profile, systematically reword
bullets, replace sections or substantially shorten the source to create a new
narrative. Keeping headings and block markers is necessary but not sufficient.
A normal draft/tailoring request does not authorise substantial or significant
rewrites; only an explicit user request for broader rewriting changes that scope.

Make required tense/voice corrections with the smallest possible wording change.
For another language, retain the lightly tailored source Markdown and translate
faithfully; translation does not justify changing emphasis, deleting detail or
rewriting content. Compare each changed source block against the selected baseline
before returning the draft and record the specific tailoring changes in the
activity note. Revert edits that have no job-specific, factual or required
language/style reason.

## Language and voice

Use implied first person throughout the CV, including Profile / About me, with
no “I” or “my”. Lead with strong, accurate past-tense action verbs in the active
voice, including for the current role: “Challenged”, “Applied”, “Led”. Preserve
actual employment dates and outcome boundaries. Use UK English spelling. Avoid third-person descriptions such as “Combines
delivery and…”, passive phrasing, clichés and repetitive sentence structures.
Pair relevant industry terms with supported measurable achievements or concrete
scope. Follow [[Knowledge/Writing-guide]] for examples and evidence boundaries.

## Fixed page structure

The page allocation is defined per document template in
`CV/Templates/layout-pages.json`. The typical three-page allocation is:

| Page | Purpose and required contents |
| --- | --- |
| 1 | Personal overview: name/contact details, positioning, Profile, Expertise & Achievements. Explain the experience and offer for the target role. |
| 2 | Work Experience part 1: the most recent roles, kept together on this page. |
| 3 | Remaining experience, followed by Education, Languages, Sports & Hobbies. |

Keep the section and employer order. Preserve explicit page breaks between the
allocated parts. Do not move an employer or part of its bullet list onto another
page to solve a space problem.

The number of bullets and the length of text may vary by version. The section
structure and page allocation remain fixed. Choose evidence and emphasis for
the role: executive strategy and organisational impact for executive roles;
technical leadership and delivery for roles closer to hands-on engineering.

For the `CV Template.ott` population workflow, the tagline line limit (50
characters per line, broken only at tag boundaries) and the conditional
Education page break are specified in
[[CV/Templates/CV-Template-Population-Agent-Instructions]]; the same three-page
allocation applies.

## Content and use of space

- Give each bullet a distinct purpose: responsibility, achievement, scale or
  relevant technical evidence. Combine overlapping claims and cut repetition.
- Page one synthesises the offer; experience pages substantiate it. Refer to an
  important achievement at both levels only when the detailed version adds useful
  evidence rather than repeating the same wording.
- Prefer concrete outcomes and supported numbers over generic assertions. Keep
  factual claims, employment dates and titles grounded in the user's references.
- If a page is sparse, add relevant, supported detail or restore an omitted
  achievement **only after returning to content review with the human**. The
  alternative is explicit human acceptance of the unused space. Review
  typography and spacing for a balanced page; do not pad it with repeated
  claims, invented achievements or excessive gaps between blocks.
- If a page is crowded, shorten prose, combine overlapping points and remove
  less relevant bullets. Preserve readable type, line spacing and section gaps;
  do not solve overflow by shrinking text indiscriminately. These are user-directed
  editorial choices: do not independently shorten text to fix an overflow.
- Keep headings with the text they introduce. Avoid stranded bullet lines,
  clipped text, overlapping objects, and crowded contact details.

## Bottom-space measurement

Interpret five empty lines as five normal body-text line heights inside the
usable page area, above the bottom margin. Count from the bottom of the final
visible text to the usable bottom edge; a decorative rule does not fill the gap.
Keep the normal bottom margin. The automated preflight defaults to 10 mm and
estimates the body line height from PDF text; supply explicit values if the
layout changes. Treat borderline results as a prompt for visual review.

## Review text first, then render

Work with the user in the plain Markdown draft
(`JobSearch/Applications/<application-slug>/CV/<application>-cv-draft.md`) until the text is
correct. Do not render ODT/PDF during wording iterations unless requested; fold the
agreed draft into block-marked Markdown (`<application>-blocks.md`) before
rendering. Keep the intended page structure while drafting; exact layout validation
follows text review.

1. Review and correct the text for role relevance, factual accuracy, language and unnecessary repetition.
2. Once the user confirms the text is correct or requests rendering, render the Markdown with its matching document template, then export to PDF.
3. Check the page count and the allocation in `CV/Templates/layout-pages.json`,
   including all bullets.
4. Run `CV/Scripts/check_layout.py` on the PDF to flag misplaced section headings,
   overflow and excessive bottom space. It requires PyMuPDF; run it with
   `JOBJIMMY_PY_WITH="pymupdf" tools/py CV/Scripts/check_layout.py ...` so PyMuPDF
   is provided per command and never installed into the checkout.
5. Inspect all pages for density, balance, line breaks and legibility. The
   automatic check cannot judge repetition or whether a page feels crammed, and
   section-heading checks alone cannot detect every spilled bullet.
6. If text overruns onto another page, do not shorten or rewrite it yourself:
    leave the rendered output and report the overflow (page count, affected
    sections and bottom-space measurement) for the user to revise. Re-render only
    after the user changes the text or explicitly requests a layout change.
7. If a page has more than five estimated blank body-text lines, inspect it
   visually and compare against the unchanged matching baseline rendered in
   the same environment. Baseline underfill is diagnostic, not permission to
   waive the tuned CV's failure. Report the page and measured space; ask the
   human to accept the exception explicitly or resume content creation with
   relevant sourced evidence. Rereview the added text before refolding and
   rendering. Do not fill space automatically or change page breaks to mask it.

```sh
python3 CV/Scripts/check_layout.py JobSearch/Outputs/tailored.pdf --report JobSearch/Outputs/layout-check.json
```

Use `--bottom-margin-mm` or `--line-height-pt` only to reflect the actual layout,
not to suppress a failed result. A failed check exits nonzero and records findings.
There is no automatic filler, font shrinking or prose rewriting in the renderer.

## Reference documents versus tuned outputs

The baseline recreations preserve the originals for extraction validation. Their
pixel-perfect round trips do not establish compliance with this style guide.
Record baseline preflight results in `JobSearch/Outputs/Baselines/*-style-preflight.json`; keep
those fidelity baselines unchanged and apply this guide when preparing tuned
versions. If the human accepts a tuned underfill, record the exception separately;
do not mark a failed automatic check as passed.
