# Getting started

[Home](../README.md) · Next: [Your knowledge base](Knowledge-Base.md)

The first milestone is a working dashboard backed by your own private notes.
You do not need OpenRouter or LibreOffice to reach it.

## 1. Install the tools you will use

| Install | What to check |
| --- | --- |
| [Obsidian](https://obsidian.md/download) | You can open a local folder as a vault |
| [Git](https://git-scm.com/downloads) | `git --version` works in your terminal |
| [Python](https://www.python.org/downloads/) — use 3.11 or later | `python3 --version` works; on Windows you may use `py -3` instead |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | `uv --version` works; it runs the project's Python without creating an in-tree venv |
| [LibreOffice](https://www.libreoffice.org/download/) — for documents | Writer opens an ODT and can export it as PDF |

The full list of software, accounts, API keys, environment variables and network
endpoints — including the optional OpenRouter (translation) and TypeSafe (Jev)
credentials — is in [External dependencies](Dependencies.md).

This guide uses macOS/Linux shell commands. On Windows, use Git Bash for the
Git/file commands, and replace `python3` with your Python launcher as needed.
Windows installation and automatic PDF export have not been validated here;
Writer's **Export as PDF** is the fallback. Run commands from the JobJimmy root
unless a step says otherwise.

This project has **no Python package manifest and no virtual environment**. Do
not run `uv venv`, `uv sync`, `uv add` or `uv pip install`: they create a
`.venv` inside the checkout, and the deep privacy gate audits ignored files,
including installed third-party metadata and interpreter symlinks, so a root
`.venv` blocks public commits. A failed `test -d .venv` is expected here.

Run Python through uv's ephemeral, cached environment instead. It lives outside
the checkout and behaves identically in every clone and Agent Manager worktree.
`tools/py` is the entrypoint:

```sh
tools/py tools/privacy_screen.py
```

Most scripts, including the privacy screen and cover-letter and CV assembly,
need only the standard library. Request the optional PyMuPDF for PDF checks and
certifi for translation TLS per command; they are never installed into the
checkout:

```sh
JOBJIMMY_PY_WITH="pymupdf" tools/py CV/Scripts/check_layout.py JobSearch/Outputs/cv.pdf
```

The equivalent without the helper is `uv run --no-project [--with PKG ...]
python <script> [args]`. On Windows, run `tools/py` from Git Bash, or use that
`uv run` form directly. Do not link a venv back into the public root or store
personal material in one. Never disable TLS verification to fix a certificate
error.

## 2. Get JobJimmy

Use the repository's **Code → Clone** URL. Replace `REPOSITORY_URL` below with
that URL; it is a placeholder, not an actual project address.

```sh
git clone REPOSITORY_URL jobjimmy
cd jobjimmy
```

No separate environment setup is needed: the Python tools run through uv's
cached environment (see step 1). Do not create a venv after cloning.

A ZIP download contains the same working files but no Git repository. The privacy
gate needs Git, so cloning is the documented route. Do not create a public remote
for your personal data.

## 3. Create your private records repository

If `JobSearch/` already exists, stop here and inspect it; do not overwrite an
existing collection. For a **new workspace**, these commands create the private
repository and copy the starter, including its hidden `.gitignore`:

```sh
mkdir JobSearch
cp -R Templates/jobsearch-repository/. JobSearch/
mkdir -p JobSearch/Knowledge/Sources
git -C JobSearch init
```

Alternatively, clone an existing private repository into `JobSearch/` instead.
The directory name is required by the dashboards. The remote repository can have
any name and is optional: a local Git repository works without a hosting account.

Check the separation:

```sh
git check-ignore JobSearch/README.md
git status --short
git -C JobSearch status --short
```

The first command should print `JobSearch/README.md`. Public status must not list
private records; the final command shows the private repository's new files.
Do not use `git add -f JobSearch` or make it a submodule.

After reviewing private files, make the private repository's first commit:

```sh
git -C JobSearch add .
git -C JobSearch commit -m "Initial private workspace"
```

If Git asks for author settings, configure your own identity locally in that
repository. If you later add a remote, verify it is private before pushing.
Version control is not a substitute for a backup you have tested restoring.

## 4. Open Obsidian

1. Choose **Open folder as vault**, and select `JobSearch/` (the private
   repository), not the public `jobjimmy/` root.
2. In Settings → Core plugins, enable **Templates**.
3. Set the template folder to `Templates` in the Templates settings.
4. Enable the **Dataview** community plugin through Obsidian's community plugin
   browser and enable it. Only enable plugins you trust.
5. Open `Dashboard.md` in Reading view or Live Preview.

You should see an empty pipeline and status table. An empty dashboard is expected
until you add an application. Plain query text usually means Dataview is disabled
or the note is in Source mode. [Dataview documentation](https://blacksmithgu.github.io/obsidian-dataview/).

Keep `readableLineLength: false` in `JobSearch/.obsidian/app.json` for the wide
tables. The dashboard CSS snippet provides additional column sizing.

**Storage note:** Obsidian writes `.obsidian/workspace.json` containing the
last-open note paths. Because the vault now lives inside the private
`JobSearch/` repository, that state file is created inside the private tree
rather than in the public project. Do not archive or upload the whole
workspace; close Obsidian before a release audit.

## 5. Decide how your assistant may use private data

Tracking works without an AI assistant. For assisted work, choose one that can
read/write local files and run the Python tools; browsing is useful for research.
No particular assistant, paid plan or memory plugin is required by JobJimmy.

Read [Privacy](../PRIVACY.md) before granting access. A locally running editor can
still send file contents to a hosted model. An OpenRouter privacy setting does
not govern your assistant's separate provider. Identity masters and completed
PDFs should stay out of hosted context unless that destination is approved.

A useful first instruction is:

> Read AGENTS.md and PROCEDURES.md. Skills are agent-agnostic in .kilo/skills/.
> Check the public/private boundary first. Help me set up my knowledge base from
> information I provide; keep personal records under JobSearch/. Do not submit
> applications or send messages.

For a job import, explicitly name `.kilo/skills/create-application/SKILL.md` if
your assistant does not discover it. Skills are instructions, not background jobs.

## 6. Enable the public privacy gate

First inspect any existing Git hooks. If none need preserving:

```sh
git config --local core.hooksPath .githooks
tools/py tools/privacy_screen.py
tools/py tools/privacy_screen.py --all
```

The hook runs before public commits and calls the standard-library screen with
`python3` directly, so it needs no venv. Never create a local `.venv`: the deep
scan reads ignored files, so installed third-party files make it fail. Use uv's
ephemeral environment instead of weakening the scanner. The hook does not configure the private repo,
prevent every leak, or scan historical Git objects. A finding needs investigation;
never add an exemption for real personal data just to make a check pass.

## 7. Choose your next step

- [Knowledge base](Knowledge-Base.md): record your experience before asking for fit analysis.
- [Applications](Applications.md): create a first application and see it on the dashboard.
- [Documents](Documents.md): add a personal layout and generate documents locally.
- [Interviews and offers](Interviews-and-Offers.md): prepare using the same evidence.

OpenRouter is only needed if you choose the supplied translation script. Its
account and policy setup is covered in the documents guide, at the point you need it.

## Kilo Code: shared instructions across models

Open the public JobJimmy folder as the Kilo workspace; open `JobSearch/` separately
as the Obsidian vault. The project `kilo.jsonc` loads `.kilo/rules/project.md`,
which routes every mode/model to `AGENTS.md`. Skills remain agent-agnostic in
`.kilo/skills/`; if a client does not discover them, explicitly ask it to read the
relevant `SKILL.md`. Do not copy instructions into separate provider folders.

Start a fresh session after updating these files. Check that the assistant can
identify the two roots and select the appropriate task reference before giving it
private inputs. Changing provider or model requires checking the private-data
route again; shared instructions do not enforce a provider's retention controls.
No model credentials or permission overrides are included in the project config.

This wiring follows Kilo's [project rule configuration](https://kilo.ai/docs/customize/custom-rules).
It requires a client supporting `kilo.jsonc` instructions; older clients should
be upgraded or explicitly directed to `AGENTS.md`. Runtime loading and model
behaviour must be checked in the installed client, not inferred from file existence.
