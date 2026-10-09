# Document language and hosted drafting: settled decisions

One language decision per application, one route decision per format. Do not
re-litigate translation vs direct drafting per task; follow this file. Canonical
details stay in `Documentation/Agent-Reference/Documents.md` and `PRIVACY.md`.

## 1. Language (decide once, early)

- Advert prose and instructions are the evidence. If they are mostly in one
  language, the final CV and cover letter use that language. `document_language`
  records the submission language; German applications still start with English
  working drafts of both documents.
- Genuinely mixed advert: follow the application instructions and any explicit
  document requirement.
- Record the lowercase ISO 639-1 code in the research note's `document_language`
  property with the evidence under **Research notes**. Both document workflows
  reuse it; never ask the user again if the note already records it.
- An explicit user instruction overrides the advert-language default and the
  vault language rule. Record the correction in the research note with its
  date, supersede obsolete target drafts while retaining approved English working
  sources, and rerun document
  checks for the new language; keep old-language check reports as dated
  history.

## 2. Route (fixed mapping, no per-task debate)

| Need | Route |
| --- | --- |
| German final CV or cover letter, any baseline language | Complete the English drafting/review stage in section 3 before selecting a translation route |
| Approved CV EN -> DE block-marked source and `JobSearch/Templates/translation-policy.json` exists and is reviewed | `CV/Scripts/translate.py` with `--privacy-policy`, then German review |
| Approved English cover letter, population body, or CV with missing/unreviewed translation policy | Translate the agreed English source under the hosted redaction workflow below, then German review |
| Other final language matching the CV baseline | Tailor the baseline directly (existing CV workflow) |
| Other language pairs | Hosted language-capable drafting under the redaction workflow below |

- `translate.py` failing for a missing or unreviewed policy is normal, not a
  blocker: fall back to hosted translation of the approved English source, not
  German drafting from scratch. A reviewed redaction policy is still required.
  Do not create a translation policy
  without asking the user first.
- Hosted translation is an "approved language-capable route" that
  `Documentation/Agent-Reference/Documents.md` names. It is faithful carriage of
  the tailored source, not a licence to rewrite: translation rules there still
  apply to it.

## 3. German applications: English first for both documents

- Follow `Documentation/Agent-Reference/Documents.md#english-drafting-before-german-translation`.
- Draft the CV and cover letter in English, review evidence/coverage, refine the
  wording, and incorporate user feedback over revision rounds until the English
  content is agreed. Do not translate the first draft automatically. When both
  documents are requested, finish both English reviews before translating either.
- Keep `document_language: de`; retain separate English sources and German
  drafts. A single-document request follows the same sequence independently.
- Translate only the agreed English text, review German against it, run each
  final German Jev check, then obtain German wording approval or an explicit
  rendering request before rendering. Later substantive changes return to the
  English source first. Neither a score nor English approval approves German.

## 4. Hosted-privacy stance (settled once, for every session)

This session is a hosted model. The stance does not depend on who drives it:

1. Before reading any private note, baseline, advert or evidence, run
   `CV/Scripts/redact_md.py prepare` with the reviewed private redaction policy
   and read only the produced `*-safe.md` copies. Check policy status with a
   local one-liner that prints only generic status (reviewed boolean, counts);
   never print the policy or identity JSON into context.
2. Policy `reviewed: false` or missing: stop dependent drafting. Do not send
   private material to the model; report the blocker instead.
3. Draft with `APP_MAN_PRIVATE_..._TOKEN` placeholders preserved exactly; save
   output to a private file and restore locally with `redact_md.py restore`.
   Never show the mapping or restored text back to the model; showing restored
   text to the user in chat is fine.
4. The user accepting residual identity inference from redacted career history
   is the standing policy: do not re-ask, and do not block drafting on it.
