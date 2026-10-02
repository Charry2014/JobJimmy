# External dependencies

[Home](../README.md) · [Setup](Getting-Started.md) · [Documents](Documents.md) · [Jev checks](Jev-Checks.md)

Everything the project needs from outside this repository: software, accounts,
API keys, environment variables and network endpoints. The documented tracking
setup uses Git, Python and uv, with Obsidian recommended; OpenRouter and Jev are
opt-in. JobJimmy has no hosted
service, installer or background job, and the privacy screen, redaction and CV
rendering run locally without network access.

License and provider credits are recorded in
[Third-party acknowledgements](../THIRD_PARTY_NOTICES.md), including PyMuPDF’s
AGPL/commercial terms and the CV template artwork exclusion.

## Software

| Tool | Used for | Required? |
| --- | --- | --- |
| [Git](https://git-scm.com/downloads) | Cloning, the public/private split and the privacy gate | Yes |
| [Python](https://www.python.org/downloads/) 3.11+ (development checks run on 3.12) | All scripts; the pre-commit hook runs `python3` directly | Yes |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Runs the Python tools in a cached environment outside the checkout | Yes |
| A POSIX `sh` (Git Bash on Windows) | `tools/py` is a shell script | Yes |
| [Obsidian](https://obsidian.md/download) | Opening and editing the `JobSearch/` vault | Recommended; any Markdown editor can edit notes |
| Obsidian **Dataview** community plugin | Dashboard and activity tables | For the live tables |
| [LibreOffice](https://www.libreoffice.org/download/) Writer (`soffice`) | Personalising ODT layouts and exporting PDFs | For document work |
| Visual Studio Code with Kilo Code (primary), or another file/terminal-capable AI agent | Research, drafting and guided record updates; see [interface setup](Getting-Started.md#kilo-code-in-visual-studio-code-primary-interface) | Optional; not needed for manual tracking |
| PyMuPDF | Automated PDF layout and comparison checks | Optional, requested per command |
| certifi | TLS trust for the translation script if the system store is unavailable | Optional, requested per command |

Notes:

- No Python package manifest and no virtual environment exist here. Never run
  `uv venv`, `uv sync`, `uv add` or `uv pip install`: an in-tree `.venv` breaks
  the deep privacy gate. Request optional packages per command instead, for
  example `JOBJIMMY_PY_WITH="pymupdf" tools/py CV/Scripts/check_layout.py ...`.
- `soffice` must be on `PATH`, or present at the macOS path
  `/Applications/LibreOffice.app/Contents/MacOS/soffice`; otherwise export PDFs
  manually from Writer.
- Document fidelity depends on the same LibreOffice and **fonts** being available
  wherever a document is rendered and compared.
- macOS and Linux commands are the validated route. Windows is documented but not
  validated; use Git Bash and LibreOffice's **Export as PDF**.

## Accounts and keys

| Account | Key / credential | Used for | Required? |
| --- | --- | --- | --- |
| [OpenRouter](OpenRouter-Setup.md) | `OPENROUTER_API_KEY` | Application AI functions and the translation script; configure the assistant separately | For those AI functions |
| Same OpenRouter account | `OPENROUTER_JEV_API_KEY` | Advisory Jev fit and document checks | For live Jev checks |
| A private Git host (for example a private GitHub repository) | Your own login | Off-machine backup/access for the private `JobSearch/` repository | Optional; a local repository works alone |

**One OpenRouter account for all paid AI services** is the account design.
Configure application assistance, translation and Jev through that account.
Separate keys for application functions and Jev allow independent spending and
privacy controls within the same account. Reusing one key in both
places is supported; no TypeSafe account or key is required. Follow
[OpenRouter setup](OpenRouter-Setup.md) for account creation, guardrails and safe
environment loading. Never commit keys or paste them into chat or command arguments.

### Optional direct TypeSafe route

When using a separately billed agent such as Claude or Codex, Jev can be purchased
through OpenRouter or [TypeSafe directly](https://docs.typesafe.ai/api). OpenRouter
is recommended for the additional model choices, not required by Jev itself.
Direct TypeSafe access uses a TypeSafe account and key with a suitably configured
client. The bundled `jev_check.py` currently supports OpenRouter only; a direct
TypeSafe key is not interchangeable with `OPENROUTER_JEV_API_KEY`.

## Environment variables

| Variable | Read by | Required? | Purpose |
| --- | --- | --- | --- |
| `OPENROUTER_API_KEY` | `CV/Scripts/translate.py` | For translation | Bearer credential for OpenRouter |
| `OPENROUTER_MODEL` | `CV/Scripts/translate.py` | For translation | Model identifier, `<provider>/<model-id>`; override per run with `--model` |
| `OPENROUTER_TRANSLATION_GUIDANCE` | `CV/Scripts/translate.py` | Optional | Default guidance profile; overrides `CV/Translation/german.json`, overridden by `--guidance` |
| `OPENROUTER_JEV_API_KEY` | `CV/Scripts/jev_check.py` | For live Jev (`--send`) | OpenRouter credential dedicated to Jev; may equal `OPENROUTER_API_KEY` |
| `JOBJIMMY_PY_WITH` | `tools/py` | Optional | Space-separated packages to add as uv `--with` flags for one command (for example `pymupdf`, `certifi`) |

The Jev model is configured in `CV/Jev/requests.json`, not in the environment.
Offline Jev previews (no `--send`) need no key and make no network call.

## Network endpoints

| Endpoint | Used by | Notes |
| --- | --- | --- |
| `https://openrouter.ai/api/v1/chat/completions` | Translation (and separately configured assistant chat) | Translator requires a reviewed private `--privacy-policy` and enforces ZDR/no-fallback routing; assistant settings are separate |
| `https://openrouter.ai/api/v1/systemone` | Jev checks | Called only with `--send`; redirects are rejected and error bodies withheld |

The assistant, package downloads and Git remotes have their own network access.
The privacy screen, redaction, identity hydration and CV/ODT rendering are local.

## Verify your environment

The application-creation workflow runs this check first, before any private
content is read. Run it yourself from the project root:

```sh
python3 tools/check_env.py
```

It reports Python, uv, git, LibreOffice and the private tree as present or
missing, and lists each API key as `set` or `missing`. It uses the standard
library only (so it also detects a missing uv), never prints a key or
model value and sends nothing; add `--json` for structured output. Missing
optional keys block only their dependent step (translation, or the live Jev
check), not tracking or import.

## Private input files you must supply

These are user-provided inputs, not distributed with the project, and they belong
under `JobSearch/`. See the linked guides for their schemas.

| File | Needed for |
| --- | --- |
| Identity JSON (for example `JobSearch/Templates/letter-identity.json`) | Local address/signature insertion and redaction-policy seeding |
| A personal CV master ODT or a source ODT plus its extracted baseline pair | Any CV rendering workflow |
| A cover-letter ODT and matching anchors JSON | Automatic letter rendering; otherwise assemble manually in Writer |
| `JobSearch/Templates/redaction-policy.json` (reviewed) | Remote drafting and Jev input checks |
| `JobSearch/Templates/translation-policy.json` (reviewed) | Translation |
| `JobSearch/Templates/layout-pages.json` | Automatic layout checks; a synthetic default ships in `CV/Templates/` |

See [Getting started](Getting-Started.md) for installation links and the first
checks, [Documents](Documents.md) for document inputs, and
[Jev checks](Jev-Checks.md) for anonymous-input and key handling.
