# Jev fit and document checks

[Home](../README.md) · [Applications](Applications.md) · [Documents](Documents.md)

Jev supplies an advisory second assessment at two points in the workflow:

| Point | Send | Return |
| --- | --- | --- |
| After the existing fit and gap analysis | Anonymous job description and completed analysis, including requirement/evidence rows and uncertainties | Match score and confidence |
| Final CV Markdown ready for review | Anonymous job description, required-points checklist and that CV alone | Match score, confidence and coverage of each point |
| Final cover-letter Markdown ready for review | Anonymous job description, required-points checklist and that letter alone | Match score, confidence and coverage of each point |

The existing evidence analysis comes first and remains authoritative for sourced
claims. Jev does not replace the application's `fit` value, write career facts,
edit documents, approve wording or submit anything. The two documents are checked
independently: a good CV cannot hide omissions in the letter, or vice versa.
Run whichever document is ready without waiting for its companion. Run again after
substantive wording, advert, checklist or request changes; old results describe
only the saved input snapshot. Do not rerun on a simple unchanged reimport.

## Editable requests

Tune [CV/Jev/requests.json](../CV/Jev/requests.json). It contains the suggested
instructions and criteria for `fit`, overall `document` coverage and each `point`.
`INDEX` in the point instructions is replaced with a zero-based checklist index.
The `model` is also configurable. Increase `version` when changing the rubric;
each result retains the exact request, its SHA-256 hash and the returned model.
A private override is accepted with `--requests`; keep any personal examples or
application-specific tuning inside `JobSearch/`.

The default fit request asks Jev to assess evidenced capability against the
mandate, credit relevant adjacent evidence and distinguish unknowns from gaps.
The document request asks whether the text actually answers the required points,
including explicit advert questions. An honest limitation can answer a point
without demonstrating the underlying qualification. Generic keyword mentions
are insufficient. Missing identity fields do not count against coverage.

Build the checklist from **all substantive required points in the advert**, the
existing requirements analysis and explicit application questions. Use a JSON
array of anonymous strings, for example:

```json
["Describe experience leading a team.", "Explain experience with software testing."]
```

Reconcile it against the full advert before calling Jev. By default, use the same
substantive list for both documents. If a point explicitly belongs only in one
document or a separate portal field, record that scope and exclusion in the
research note and use the appropriate list. Never silently remove a point merely
because it is hard to answer. Identity/contact fields and upload mechanics are
handled locally, outside this content-coverage check. The overall question also
references the full anonymous advert so checklist omissions can affect the score;
per-point results can only cover the points actually supplied.

## Anonymous inputs

Use the existing safe Markdown copies prepared under
[the privacy workflow](../PRIVACY.md#remote-drafting-reversible-markdown-tags).
Check the final text **before local identity restoration or hydration**, or make
a new safe copy of a restored document. Final Markdown is not automatically
anonymous: the advert, analysis, recipient, employer history and link targets can
still identify people or organisations.

Remove or tokenise all explicit identifiers locally, including employer/recruiter
names and addresses, contact details, job URLs/IDs, personal profile links and
private file references. Replace evidence wikilinks with anonymous labels while
retaining the actual evidence summaries; Jev cannot open vault links. Preserve
substantive requirements and career evidence. Do not send the knowledge vault,
identity JSON, mapping, redaction policy, restored documents or conversation.

`--policy` uses the existing locally reviewed redaction policy. The CLI rejects
remaining listed values (case-insensitively), common contact patterns, web URLs,
wikilinks and local path locators in the complete outgoing request, including
custom prompts. It does **not** rewrite paths, classify arbitrary long numbers as
phones, or use a cloud redaction filter. Already anonymous inputs need not match
any policy value. `--reviewed` records that the selected inputs and checklist were
checked locally for identifiers the patterns cannot find; it is not a new approval
request on every run. A missing/unreviewed policy or failed check blocks transmission.
Pattern checks cannot certify anonymity or detect all identifiers. Redacted career
narrative can still be identifying; use the user's standing privacy policy for
that residual risk. This workflow is authorised for anonymous Jev inputs, not raw
private records. No TypeSafe retention or ZDR guarantee is implied.

## Run from the project root

Python's standard library is sufficient. Set `TYPESAFE_API_KEY` through your local
secret manager or a non-echoing prompt; never put the key in a file in this public
repository, a command argument or chat. Calls go directly to TypeSafe's HTTPS
evaluation endpoint; no OpenRouter redaction setting is involved.

Prepare the following anonymous inputs privately. The example filenames are
generic; use the current application's files. Preview the exact fit request
offline first while tuning:

```sh
python3 CV/Scripts/jev_check.py fit \
  --job JobSearch/Outputs/job-safe.md \
  --analysis JobSearch/Outputs/fit-safe.md \
  --policy JobSearch/Templates/redaction-policy.json --reviewed \
  --output JobSearch/Outputs/jev-fit-preview.json
```

No network call or score is produced without `--send`. To run the fit check,
repeat with `--send` and a new output such as `JobSearch/Outputs/jev-fit-v1.json`.
An offline preview does not have to be approved each time; it is a tuning aid.

Run the final documents individually:

```sh
python3 CV/Scripts/jev_check.py cv \
  --job JobSearch/Outputs/job-safe.md \
  --document JobSearch/Outputs/cv-safe.md \
  --requirements JobSearch/Outputs/required-points-safe.json \
  --policy JobSearch/Templates/redaction-policy.json --reviewed --send \
  --output JobSearch/Outputs/jev-cv-v1.json

python3 CV/Scripts/jev_check.py cover-letter \
  --job JobSearch/Outputs/job-safe.md \
  --document JobSearch/Outputs/letter-safe.md \
  --requirements JobSearch/Outputs/required-points-safe.json \
  --policy JobSearch/Templates/redaction-policy.json --reviewed --send \
  --output JobSearch/Outputs/jev-letter-v1.json
```

Each successful call writes new JSON and Markdown reports. Existing files are
never overwritten. For application work, keep fit artifacts in that application's
`Attachments/` and document artifacts in its flat `CV/` folder. The tool refuses
public-workspace outputs and private-output symlink escapes. It also works with
synthetic inputs in an external temporary directory without an attached vault.

## Show and record the results

Always surface separate results in the user response, with links to the private
reports. Use: **Jev fit/CV/cover letter: match N/100; confidence C%.** For documents,
include partial, missing and unclear points with their individual confidences;
keep the full checklist table in the report. Explain disagreements with the
existing assessment as your interpretation, not an explanation generated by Jev.

Jev's Score is a probability-weighted position on the configured ordered levels.
The CLI converts it to 0–100 with `100 × score / (number of levels − 1)`.
Confidence comes directly from Jev's answer distribution; it is neither a hiring
probability nor independent proof of truth. Per-point Choice confidence is also
reported directly. There is no invented combined confidence, automatic pass
threshold or automatic acceptance. A high overall score does not mean every point
is covered; inspect the individual rows. These defaults still need domain tuning.

Record fit results under **Research notes → Jev fit check** in the existing
research note. Record document results under **Notes → Jev document check** in
the relevant `document-added` activity. Follow [PROCEDURES.md](../PROCEDURES.md#jev-check-results)
and the canonical templates; no new YAML properties are required. Keep scores
outside the CV/letter text. The CLI only writes reports, so the agent performs
these note updates and user-facing reporting.

If the key, safe inputs or service are unavailable, explicitly show
**Jev check unavailable/not run**, with the reason. Do not invent a score, label
an offline preview as a result, or silently substitute the drafting model.
Preserve completed analysis/drafts and continue independent work; report the
outstanding check. HTTP errors and malformed/missing answers fail without a
success report; provider error bodies are withheld. Retry only deliberately.

## Contract and validation

Integration references checked 2026-10-01:
[HTTP API](https://docs.typesafe.ai/api),
[Score](https://docs.typesafe.ai/primitives/score),
[confidence](https://docs.typesafe.ai/confidence) and
[evidence-checking cookbook](https://docs.typesafe.ai/cookbooks/citation_check).
The local tests use synthetic inputs and mocked responses. Live scoring quality,
latency, cost and calibration have not been established by those tests.

```sh
python3 -m unittest discover -s CV/Scripts -p test_jev_check.py
```
