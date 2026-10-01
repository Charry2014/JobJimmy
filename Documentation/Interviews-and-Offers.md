# Interviews, positioning and offers

[Home](../README.md) · [Applications](Applications.md) · [Knowledge base](Knowledge-Base.md)

These workflows use an assistant and the existing activity notes. Dedicated
interview and negotiation skills are on the roadmap; they are not commands you
can currently install from this project.

## Research before the interview

Give the assistant the application, interview format, date and any agenda you
received. Ask it to read the existing research before searching again:

> Prepare an interview briefing for this application. Research the company,
> product, role and relevant public professional background of the interviewers.
> Cite sources and dates, distinguish facts from hypotheses, and identify what
> is still unknown. Keep my private career details out of web search queries.

Useful output is a short briefing: what the company does, why the role might
exist, likely challenges, what the advert says success requires, and questions
that test those assumptions. Public claims can be stale; attach the observation
date and source rather than presenting guesses as inside knowledge.

Store preparation as `kind: interview-preparation` in the application's
Activities folder. Relevant new company facts can also enrich its company note.
The assistant should follow [PROCEDURES.md](../PROCEDURES.md) for record updates.

## Build a small set of evidence-backed answers

> Map the role's main requirements to examples in my knowledge base. For each,
> propose a concise answer with context, my action, outcome and a limitation or
> lesson. Identify missing facts; do not fill them in. Help me practise explaining
> the example, rather than memorising polished text.

Prepare a few stories you can adapt: a difficult decision, delivery under
constraints, working through conflict, a failure and what changed afterward.
Use examples you actually have. Distinguish what you personally implemented,
what you led and what the team delivered.

For positioning, ask for a short answer to “Why this role?” grounded in the
employer's stated needs and your evidence. Keep aspirations distinct from past
experience. A gap can be acknowledged honestly alongside transferable experience.

## Practise and evaluate the employer

> Run a mock interview, one question at a time. After my answer, assess relevance,
> clarity, specificity and evidence. Ask follow-up questions where my ownership
> or result is unclear. Save only the useful feedback, not an invented transcript.

Also prepare questions for the employer:

- What would success look like after six months?
- What decisions would this role own, and what resources are available?
- Which constraints or unresolved problems would I inherit?
- How are priorities, disagreements and performance evaluated?
- What remains to be clarified about working arrangements and the process?

Choose questions relevant to the actual role. Interview preparation is also about
finding out whether the opportunity suits you.

## Debrief while the details are fresh

> Record today's interview notes. Separate what was said from my interpretation,
> capture commitments and next steps, and identify any follow-up questions.
> Draft a thank-you message for review; do not send it.

Use `kind: interview-notes`. Record the date, participants, topics, answers,
outcomes and next steps. Update status when warranted; do not infer an offer or
rejection from tone. Link any files that actually exist.

New career facts or clarified preferences can update the knowledge base with
provenance. Keep employer-specific impressions in the application notes.
Record a follow-up as sent only after it has actually been sent.

## Prepare for an offer or salary conversation

> Help me compare the offer with my priorities. Separate guaranteed compensation,
> variable pay, equity assumptions, benefits and working conditions. Research
> relevant current market evidence with sources and dates. Keep my private
> minimums out of the proposed message to the employer.

Use a private comparison table with a row for each component, the offered terms,
questions outstanding and how much it matters to you. Use scenarios for uncertain
bonuses or equity rather than treating them as guaranteed cash. Compare location,
hours, travel, leave, authority and growth alongside pay.

Then practise a counteroffer grounded in your contribution and priorities. Never
invent another offer or a market figure. Keep the offer terms, your preferred
outcome and your reservation point separate. The assistant can organise questions;
legal, tax and complex equity questions may need qualified advice based on the
actual terms and jurisdiction.

No message, acceptance, withdrawal or application submission is automatic.
Record the outcome in a dated activity, using `kind: other` for negotiation notes
under the current schema, and update the application explicitly.

## Recordings and sensitive material

Written debriefs work without recording anyone. If using recordings or automated
transcription, establish permission and check applicable requirements first.
Transcripts, private negotiation limits and interview feedback are sensitive.
Keep them under `JobSearch/` and verify any model, transcription or storage
service before transfer. [Privacy guide](../PRIVACY.md).
