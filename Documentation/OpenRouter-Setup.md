# Set up OpenRouter

[Home](../README.md) · [Getting started](Getting-Started.md) · [Dependencies](Dependencies.md)

**One OpenRouter account for all paid AI services** is the design principle.
Application assistance, translation and Jev checks all use that account; separate
keys divide controls within it, not accounts or billing providers. This guide
uses two keys so you can control their spending and privacy settings independently.
Using one key for both is also supported. Tracking and local document assembly
need no AI account. No separate TypeSafe account is required for Jev.

## 1. Create the account and add credit

Sign up at [OpenRouter](https://openrouter.ai/), then open your account's credits
page and add a small prepaid balance you are comfortable spending. Check the
checkout total and fees before paying. For initial testing, leave automatic
recharge off; revisit it once you understand actual usage. Credit funds requests;
it is separate from a key's spending cap. Choose an assistant that supports
your OpenRouter key; the documented setup needs no separate paid AI subscription.
See the [OpenRouter quickstart](https://openrouter.ai/docs/quickstart).

## 2. Create and limit the keys

Open [API keys](https://openrouter.ai/settings/keys). Create ordinary inference
keys named `jobjimmy-applications` and `jobjimmy-jev`. Save the values in your
password/secret manager when shown. Do not use a management key in the program.

A conservative starting budget for a trial is **$2 per day for application
functions and $1 per day for Jev**. These are suggested spending ceilings, not
cost estimates or a promise of how many applications they will cover. Adjust
after reviewing a few synthetic tests and your actual usage. With one shared
key, use a combined ceiling you are comfortable spending, for example $3/day.

Set a nonempty key limit and explicitly choose its reset period. OpenRouter
supports daily, weekly, monthly or no reset; resets use UTC. No-reset limits are
useful for a fixed trial budget. Two daily caps can both be spent each day: they
do not create a monthly total cap. Track the combined spend, keep the prepaid
balance small, and use a shared monthly guardrail where appropriate.
[Key limits and reset rules](https://openrouter.ai/docs/api/api-reference/api-keys/create-keys).

## 3. Apply privacy and routing guardrails

In OpenRouter's privacy settings, configure account defaults and assign guardrails
to **both** keys. Start with a guardrail for application functions and another for
Jev if they need different model permissions or budgets. Restrict each to the
models/providers you intend to use. Ensure the Jev rules permit the configured
Jev model and its provider. A shared key shares its restrictions and budget.
Account restrictions still apply; a separate key cannot loosen them.
[Guardrail setup and precedence](https://openrouter.ai/docs/guides/features/guardrails/overview).

For career-related work, use these starting settings:

- Enforce Zero Data Retention across all model groups, including other/non-frontier
  models. If no eligible route exists, investigate or leave the check unavailable.
  [ZDR documentation](https://openrouter.ai/docs/guides/features/zdr).
- Disable provider training/data collection for both paid and free routes.
  [Data collection controls](https://openrouter.ai/docs/guides/privacy/data-collection).
- Leave private input/output logging and use of inputs/outputs disabled, and
  disable unused Broadcast destinations. Content logging is separate from billing
  metadata. [Logging](https://openrouter.ai/docs/guides/features/input-output-logging)
  and [Broadcast](https://openrouter.ai/docs/guides/features/broadcast/overview).
- Consider sensitive-information blocking as an additional check. Test it with
  fictional inputs; filters can miss identifiers or block valid requests.
  [Sensitive-info filtering](https://openrouter.ai/docs/guides/features/guardrails/sensitive-info).

These are account settings, not proof of live enforcement. The translation script
also sends strict provider-routing fields; the Jev CLI uses the System One request
format and relies on account/key controls for routing policy. Test each route.
Continue the [local anonymisation workflow](../PRIVACY.md): OpenRouter-side filters
act after data has already left your machine.

## 4. Load keys into the program's environment

An environment variable is a named value inherited by programs started from your
terminal. JobJimmy reads these variables; it does not load `.env` files automatically.
Run the following in an interactive Bash or zsh terminal. Paste a key only at the
hidden prompt, not into the command itself. Keep shell tracing (`set -x`) off.

```sh
set +x
export OPENROUTER_API_KEY="$(python3 -c 'import getpass; print(getpass.getpass("Application OpenRouter key: "))')"
export OPENROUTER_JEV_API_KEY="$(python3 -c 'import getpass; print(getpass.getpass("Jev OpenRouter key: "))')"
```

If you prefer one key, load the application key using the first prompt above,
then assign it to both variables instead of entering a second key:

```sh
export OPENROUTER_JEV_API_KEY="$OPENROUTER_API_KEY"
```

| Variable | Consumer |
| --- | --- |
| `OPENROUTER_API_KEY` | Translation script; use this application's key in your assistant's OpenRouter configuration too |
| `OPENROUTER_JEV_API_KEY` | Jev CLI only; required explicitly, with no fallback to the application key |
| `OPENROUTER_MODEL` | Translation model, unless overridden with `--model` |

For translation, select a model supported by your privacy policy and set its
OpenRouter ID, replacing the placeholder:

```sh
export OPENROUTER_MODEL='<provider>/<model-id>'
```

Jev's model is configured separately in `CV/Jev/requests.json`. The System One
endpoint accepts the supplied `jev-latest` alias; it is not a chat/AutoRouter
model selection. [OpenRouter System One integration](https://openrouter.ai/docs/guides/community/typesafe-sdk).

Start scripts from this terminal. Existing IDE processes do not gain newly
exported variables: restart the IDE from the configured environment or use its
secure environment/secret configuration. Configure the assistant's OpenRouter
provider explicitly; it may use its own credential store rather than these
variables. Check that it uses the application key. JobJimmy cannot change the
assistant's provider automatically.

The exports last for this shell session and its child processes. For repeat use,
load them through your secret manager's environment integration. Keep literal
keys out of shell startup files, project configuration, Git, notes, chat and logs.
An ignored file is not a secret store. Never use `env`, `printenv` or `echo` to
show credentials while troubleshooting. Clear this shell's variables when done:

```sh
unset OPENROUTER_API_KEY OPENROUTER_JEV_API_KEY
```

## 5. Verify before using career material

From the project root in the configured terminal:

```sh
python3 tools/check_env.py
```

Both key variables should be reported as `set`. This checks presence only; it
makes no network request and does not verify validity, balance or guardrails.
Missing LibreOffice only affects document export; a missing translation model
only affects translation without a `--model` override.

Use fictional inputs for a small first request in the assistant, the translation
workflow and the [Jev workflow](Jev-Checks.md), whichever you enable. Confirm each
request appears under the intended key in OpenRouter's activity/usage view and
inspect its cost. Follow the [guardrail test method](../OPENROUTER-GUARDRAIL-TESTS.md)
for enforcement checks; a successful response alone does not prove ZDR or filtering.
Do not use real records merely to test credentials.

If authentication fails, check the selected key, revocation/expiry and process
environment. If credit or a spending cap is exhausted, review usage before
raising it. If a guardrail blocks the route, review model eligibility rather than
silently relaxing privacy. Rotate a disclosed key in OpenRouter and reload its
replacement in each consumer.

Sources reviewed 2026-10-02. Dashboard labels may change; the linked upstream
documentation is authoritative for provider settings. No live account audit is
implied by this guide.
