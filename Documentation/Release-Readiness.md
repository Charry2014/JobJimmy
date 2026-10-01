# Release readiness

[Home](../README.md) · [Roadmap](Agentic-Roadmap.md)

AppMan is suitable to present as an experimental hobby project, provided the
release describes its limits honestly. This page is a checklist, not a claim that
a publication audit or cross-platform test has been completed.

## Documentation assessment — 2026-09-30

The previous documentation was primarily an internal specification. It mixed
onboarding, implementation rules, historical assumptions and future features.
Required tools were unclear, private baselines were assumed, interview workflows
were absent, and the README incorrectly told readers to personalise a public
cover-letter template. Some instructions claimed a letter ODT was supplied when
it was not.

The user-facing documentation now has a reading path: setup, knowledge base,
applications, documents, interviews/offers and troubleshooting. Examples are
synthetic; implementation and roadmap status are distinguished. Existing technical
references remain available without being the first thing a newcomer must read.

## Before publishing

- [ ] Choose a project licence and add `LICENSE`. There is currently no
  project-level licence file; no licence has been chosen on the owner's behalf.
  Verify redistribution rights for included templates, images, fonts and vendored
  plugin files separately.
- [ ] Audit public Git history, filenames, branches, messages and binary assets
  for personal data, not just the current working tree. Do not publish a whole
  workspace archive or include the private repository.
- [ ] Run the privacy screen in default and `--all` modes and review the diff.
  Confirm the Obsidian vault, including its session state, stays inside the
  private `JobSearch/` tree and never appears in the public project.
- [ ] Follow the new setup guide in a fresh checkout without the author's private
  data, account settings or global skills. Verify the dashboard in the actual app.
- [ ] Generate and visually inspect a wholly synthetic CV from the included
  layout. Record the Python, LibreOffice and font environment used.
- [ ] Either ship a validated blank cover-letter ODT/anchor pair or retain the
  explicit manual-assembly limitation in the documentation.
- [ ] Verify installation and export on each platform advertised as supported.
  Current documentation does not claim Windows validation.
- [ ] Add a synthetic screenshot or short walkthrough if useful; inspect it for
  private tabs, paths, notification banners and metadata before publication.

No hosted service, automatic application submission, email/calendar workflow or
Notion sync is advertised as implemented. The [Jev scaffold](Jev-Checks.md) has
synthetic contract tests; live quality, calibration, cost and latency remain
unverified. Describe it as advisory and tunable, not a validated hiring predictor.

## Keep the guides trustworthy

When a command or schema changes, update the relevant user guide and technical
reference together. Keep completed implementation out of the future roadmap and
keep planned capabilities out of setup promises. Prefer a short successful task
with a visible result over more policy text.
