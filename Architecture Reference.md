# 260921-cvgen Architecture Reference

One document for people who want to understand 260921-cvgen without reading
the code. The rules for it are in `~/.config/agents/rules/DOCUMENTATION.md`.
A change that alters anything described here updates this document in the
same change.

Contents: [[#Purpose]] · [[#How it works]] · [[#Interfaces to other projects]] · [[#Key components]] · [[#Internal interfaces]] · [[#Data flows]]

## Purpose

<!-- What the project aims to do, for whom, and what it deliberately leaves out. -->

## How it works

<!-- The mechanism from input to outcome in a few paragraphs; a diagram where one explains more than prose. -->

## Interfaces to other projects

<!-- Every project, service or tool this one calls or is called by: what crosses each boundary and in which direction. -->

- **LibreOffice (`soffice`)**, called headless to export rendered ODTs to PDF.
  ODT paths go in, PDFs come out. Every call goes through
  `CV/Scripts/office.py` (directly or via the `tools/soffice` wrapper), which
  sets `FONTCONFIG_FILE` on macOS so headless LibreOffice sees installed fonts
  and the private substitutions in `JobSearch/Templates/fonts.conf`.

## Key components

<!-- The main modules, processes or services: each one's responsibility and where it lives in the code. -->

- **PDF export layer**: `CV/Scripts/office.py` finds LibreOffice and builds
  the font environment; `tools/soffice` is its command-line form. It is used by
  `populate_cv.py --pdf`, `cover_letter.py export-pdf` and the documented CV
  export command.

## Internal interfaces

<!-- How the key components talk to each other: function boundaries, queues, files, protocols, schemas. -->

## Data flows

<!-- The paths the important data takes through the components, from source to sink, including every persistent store. -->
