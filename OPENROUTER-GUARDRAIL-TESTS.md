# OpenRouter guardrail tests — methodology and findings

This document describes a repeatable method for testing how OpenRouter guardrails
(Zero Data Retention enforcement and personal-data redaction) behave for a
specific account key, and records the findings shape such a test produces.
The hardened translator now requires a private privacy policy and sends explicit
ZDR, denied data collection and provider allowlist/no-fallback fields. Its unit
tests mock the network; they do not verify account settings. The table below is
a methodology and example, not a record of a current successful live test.

Re-run the tests with synthetic data whenever the account, key, guardrail
configuration or translation workflow changes.

## Why test

`CV/Scripts/translate.py` sends CV block text to OpenRouter. Two account-level
controls affect what happens to it:

- **ZDR guardrails** restrict which providers/models may serve a request.
- **Sensitive-data filtering** redacts or blocks detected personal information.

Both can change silently with account settings, and neither is verifiable from
the script's local output alone. Echo-style behavioural tests with fictional
fixtures are the practical way to observe enforcement.

## Method

1. Use the same `OPENROUTER_API_KEY` the workflow uses, without exposing or
   saving it. Do not send real CV text, private contact details or vault
   documents. Synthetic fixtures only.
2. Issue short chat-completion requests (small token caps) through the same
   endpoint and privacy fields the translation script would use, plus
   forced-provider variants:

   | Test | Purpose |
   | --- | --- |
   | Configured model, no provider fields | Baseline routing. |
   | Configured model, `zdr: true`, `data_collection: deny` | Explicit strict fields. |
   | Configured model, `zdr: false`, `data_collection: allow` | Relaxed fields must not bypass guardrails. |
   | Auto Router with strict fields | Whether automatic routing honours ZDR. |
   | `<direct-provider model>` with `only: [<provider>]`, fallback disabled | Whether guardrails reject non-compliant direct routes. |

   A request succeeding with relaxed fields does not prove enforcement; explicit
   rejections on forced direct-provider routes do.
3. Probe redaction with fictional values in several shapes:

   | Fixture | Expected safe behaviour |
   | --- | --- |
   | Plain email `user123@example.com` | Redacted or blocked. |
   | Telephone `+1 555-0100` | Redacted or blocked. |
   | Name in plain prose | Redacted or blocked. |
   | Obfuscated email `user123 [at] example [dot] com` | Not guaranteed — record actual behaviour. |
   | Email inside a simulated `role: tool` result | Record actual behaviour. |
   | CV-shaped JSON with name, email and achievement numbers | Record exactly which fields survive. |
   | Streaming response | Redaction may differ from non-streaming. |

4. Record the observed responses verbatim (synthetic data only), plus the
   generation IDs of successful requests so the account logs can be correlated
   without enabling content logging.
5. Also run read-only key/guardrail/model queries where the key permits:
   `GET /api/v1/key`, `GET /api/v1/guardrails`, `GET /api/v1/models/user`. A
   management key may be needed for guardrail introspection; do not replace the
   inference key with a management key in the translation tool merely to gain
   visibility.

## Findings template

| Check | Result |
| --- | --- |
| Tested direct-provider routes rejected under ZDR guardrail | e.g. `<provider list>` |
| Auto Router honours ZDR | yes / no + resolved model and provider |
| Plain email | `[EMAIL]` / blocked / unchanged |
| Phone with country prefix | e.g. `+1 [PHONE]` — prefix may survive |
| Name in prose | `[PERSON_NAME]` / unchanged |
| Obfuscated email | frequently unchanged |
| CV-shaped JSON | e.g. email redacted, name survives, JSON may become malformed |
| Streaming | e.g. redacted |

Recorded result example (synthetic fixtures, fictional accounts only):

> ZDR enforced on all tested direct routes. Redaction active but incomplete:
> obfuscated emails survive, one JSON response became malformed after partial
> redaction, and a fictional name in JSON survived while the same name in prose
> was redacted. Usage cost of the test run: `<amount>` (inference cost, not a
> reconciled bill).

## Interpretation limits

- Echo responses show filtering behaviour, not the exact request forwarded to
  the provider.
- Success alone does not establish that retention rules were applied.
- Redaction happens after transfer to OpenRouter; even blocked or redacted
  requests have already sent their original content to OpenRouter.
- Do not treat generic server placeholders as reversible pseudonymisation: a
  translation containing `[EMAIL]` is incomplete output, not an anonymised CV.
- These are point-in-time tests of one key and one account; other keys,
  gateways or agents are not covered.

## Recommended hardening (independent of test results)

1. Keep ZDR enforced across all model groups; keep provider training/data
   collection disabled for paid and free routes; keep the daily spend cap.
2. Verify OpenRouter storage settings separately: Private Input & Output
   Logging off; Use of Inputs/Outputs off; Broadcast destinations disabled
   unless explicitly needed.
3. In the translation workflow, prefer local safeguards: omit contact-only
   blocks, tokenise and restore values locally, reject unexpected redaction
   placeholders, and log only request IDs, resolved models/providers and policy
   metadata.
4. Restrict model/provider allowlists if automatic routing to unapproved
   providers is not acceptable.
5. Check regional routing only if region-restricted processing is a requirement.

## Policy sources

- [ZDR](https://openrouter.ai/docs/guides/features/zdr): inference restrictions,
  account/request precedence, in-memory caching caveat.
- [Guardrail overview](https://openrouter.ai/docs/guides/features/guardrails/overview):
  documented hierarchy and controls.
- [Sensitive-info filtering](https://openrouter.ai/docs/guides/features/guardrails/sensitive-info):
  input-side redact/block behaviour and detection limitations.
- [Data collection](https://openrouter.ai/docs/guides/privacy/data-collection) and
  [private logging](https://openrouter.ai/docs/guides/features/input-output-logging):
  separate content-storage and metadata policies.
- [Broadcast](https://openrouter.ai/docs/guides/features/broadcast/overview):
  separate external observability flow.

Provider policy promises are not independently verifiable through echo tests.
Previously disclosed data is not retroactively protected by new guardrails.
