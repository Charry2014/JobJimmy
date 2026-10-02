# Document language and hosted drafting: settled decisions

One language decision per application, one route decision per format. Do not
re-litigate translation vs direct drafting per task; follow this file. Canonical
details stay in `Documentation/Agent-Reference/Documents.md` and `PRIVACY.md`.

## 1. Language (decide once, early)

- Advert prose and instructions are the evidence. If they are mostly in one
  language, prepare the CV and cover letter in that language.
- Genuinely mixed advert: follow the application instructions and any explicit
  document requirement.
- Record the lowercase ISO 639-1 code in the research note's `document_language`
  property with the evidence under **Research notes**. Both document workflows
  reuse it; never ask the user again if the note already records it.
- An explicit user instruction overrides the advert-language default and the
  vault language rule. Record the correction in the research note with its
  date, remove superseded drafts in the old language, and rerun document
  checks for the new language; keep old-language check reports as dated
  history.

## 2. Route (fixed mapping, no per-task debate)

| Need | Route |
| --- | --- |
| CV in a language matching its baseline | Tailor the baseline directly (existing CV workflow) |
| CV EN -> DE block-marked source and `JobSearch/Templates/translation-policy.json` exists and is reviewed | `CV/Scripts/translate.py` with `--privacy-policy` |
| Any other translation need (cover letter, population body, other language pairs, or the translation policy is missing/unreviewed) | The hosted agent drafts the target language directly, under the redaction workflow below |

- `translate.py` failing for a missing or unreviewed policy is normal, not a
  blocker: fall back to direct drafting. Do not create a translation policy
  without asking the user first.
- Direct drafting is the "approved language-capable route" that
  `Documentation/Agent-Reference/Documents.md` names. It is faithful carriage of
  the tailored source, not a licence to rewrite: translation rules there still
  apply to it.

## 3. CV with English baseline, German target (user answer: both drafts)

- Keep the tailored English source Markdown (minimal edits only) AND produce the
  faithful German draft alongside. Both go to the user for review; the English
  source is the comparison reference, the German draft is the render input.
- Cover letter: draft directly in the advert language from the start; there is
  no English intermediate.

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
