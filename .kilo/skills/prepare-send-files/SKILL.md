---
name: prepare-send-files
description: Prepare recruiter-friendly copies of an approved application's final CV and cover-letter PDFs for sending. Use only after both PDFs have been rendered and checked; this does not submit an application.
---

# Prepare files to send

Follow `AGENTS.md`, `PRIVACY.md` and the private vault's `AGENTS.md`. Work
only inside the selected application's private `JobSearch/Applications/<application-slug>/CV/`
folder. Do not read private filenames, PDF contents or tool output containing
identifiers into a hosted model; use a permitted local-only route for this step.

1. Confirm that this is the intended application and that its final CV and
   cover-letter PDFs both exist and have passed their respective layout and
   content checks. Do not use drafts, ODTs, PDFs from another application or
   unverified exports. If either is missing, stop and finish its document
   workflow first.
2. Run the local-only send-files script to create the recruiter-friendly
   copies. It reads the vault owner's display name from the private identity
   JSON itself, so the name never enters the agent context:

   ```sh
   python3 CV/Scripts/prepare_send_files.py \
     --identity JobSearch/Templates/letter-identity.json \
     --cv 'JobSearch/Applications/<application-slug>/CV/<slug>-cv.pdf' \
     --cover-letter 'JobSearch/Applications/<application-slug>/CV/<slug>-cover-letter.pdf'
   ```

   In the source files' own private `CV/` folder the script **copies** (never
   renames or moves) the CV to `<candidate name> - CV.pdf` and the letter to
   `<candidate name> - Cover Letter.pdf`, keeping the approved sources
   unchanged. Resolve `<candidate name>` afresh from the local JSON for each
   vault; never write the resolved name or those real filenames into the public
   repository, a public log or hosted-model output. The script refuses to
   overwrite an existing copy and rolls back if a copy fails; stop and
   investigate if it reports either.
3. The script verifies locally that both copies exist, are nonempty PDFs and
   match their respective approved source files byte-for-byte. Report only the
   script's generic success or a generic blocker through a hosted agent,
   without printing the private paths or identity. Copying files does not send
   them, record a submission or change the application status. Follow
   `PROCEDURES.md` if a document-added activity is separately needed; record
   only real files. Do not pass `--identity` a path outside the private vault,
   and never send the identity JSON or the resolved filenames to a model.
