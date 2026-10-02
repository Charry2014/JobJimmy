# Troubleshooting

[Home](../README.md) · [Setup](Getting-Started.md) · [Documents](Documents.md)

| What you see | Check or next step |
| --- | --- |
| Dashboard displays a query instead of a table | Enable Dataview; switch to Reading view or Live Preview |
| Dashboard is empty | Open `JobSearch/` as the vault; check notes are under `Applications/` with `type: application`; closed statuses are hidden by default |
| An activity is absent | Check `type: activity`, the exact `application` wikilink, its Activities folder, and unresolved `{{title}}` text in the application's query |
| An application appears under the wrong recruiter | Fix the application `recruiter` link; a recruiter agency is not automatically the employer |
| The assistant cannot find the skill | Ask it to read `.kilo/skills/create-application/SKILL.md` explicitly; `.kilo/` does not require a specific runtime |
| Fit analysis is provisional | Seed the knowledge base; missing evidence or baselines should not be invented |
| “Generated artifacts must not be written into the public project” | Put personal output under `JobSearch/`; do not write documents to the project root or public `CV/` folders |
| “Private artifact destination escapes JobSearch/” | Check output paths and symlinks; keep artifacts inside the physical private tree |
| Missing `Manager.md` or another baseline | Personal baseline pairs are not shipped; create your own using the documents guide |
| Missing cover-letter ODT | Only the Markdown starter and example anchors ship; use Writer manually or configure a private compatible ODT/anchor pair |
| “Template structure changed” | The letter's anchor configuration no longer matches its ODT. Verify paragraph positions and create a matching private configuration |
| Missing tokens or bookmarks | A personal-master template was changed structurally; compare it with the supplied blank template |
| A CV paragraph disappeared or old text returned | Review the alignment report's dropped source and baseline fallback entries before accepting a render |
| A document has too many pages | Inspect it in Writer; review wording and layout. Do not silently shorten accepted text or shrink fonts indiscriminately |
| `soffice` not found | Open the ODT in Writer and export manually, or configure the executable on PATH; see platform notes in the documents guide |
| `.venv` missing or `test -d .venv` fails | Expected: this project has no venv. Run Python with `tools/py` or `uv run --no-project`; see [Getting started](Getting-Started.md) |
| Deep privacy audit flags `.venv` | Remove the stray `.venv`; never create one here. Run Python with `tools/py`/`uv run --no-project`; ignored third-party files and interpreter symlinks are still scanned |
| `uv venv`, `uv sync` or `uv pip install` wants to create `.venv` | Do not run them here; request packages per command with `JOBJIMMY_PY_WITH="pkg" tools/py ...` or `uv run --no-project --with pkg python ...` |
| `pymupdf` missing | Request it per command: `JOBJIMMY_PY_WITH="pymupdf" tools/py CV/Scripts/check_layout.py ...`; basic ODT operations do not require it |
| Layout checker flags example employers | Create a private layout configuration matching your own CV and pass `--config` |
| Translation requires a policy | Supply `--privacy-policy` with a reviewed private configuration; model selection alone is insufficient |
| Translation rejects keep-block IDs | The policy does not match this baseline; inspect the source block IDs locally and correct the policy |
| Translation fails with an HTTP status | Check key, balance, model/provider availability and strict routing. Error bodies are intentionally withheld; do not weaken privacy as a workaround |
| Translation reports changed tokens | No translation should be accepted; inspect the private inputs and policy. Do not manually delete safeguards to force a render |
| Jev reports `OPENROUTER_JEV_API_KEY` missing or HTTP 401 | Load the Jev OpenRouter key in the same process environment; see [OpenRouter setup](OpenRouter-Setup.md); report the check as unavailable until it succeeds. See [Jev checks](Jev-Checks.md) |
| Jev rejects identifiers or locators | Review the anonymous advert, analysis/document, checklist and custom requests locally. Remove identifying links and use the reviewed private policy; do not send raw inputs |
| Jev preview contains no score | Expected without `--send`: the preview is an offline request for tuning. Use a new output filename when running the live check |
| Privacy screen flags an Obsidian state file | The vault now lives under the private `JobSearch/` tree, so workspace state is created there. If a stray `.obsidian/` file appears in the public tree, remove it; the app can recreate vault state when reopened |
| Public `git status` does not show an application change | Expected: use `git -C JobSearch status` for the independent private repository |

The authoritative [activity procedures](../PROCEDURES.md) and
[CV reference](../CV/README.md) cover detailed formats. When reporting a bug,
provide the command shape, tool versions and a synthetic reproduction. Do not
attach a real CV, identity JSON, API key or private application path.
