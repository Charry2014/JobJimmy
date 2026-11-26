# Shared JobJimmy instructions

For every Kilo mode and model family, read the project-root `AGENTS.md` and follow
its task routing. Skills are agent-agnostic under `.kilo/skills/`; read their
SKILL.md directly if discovery does not expose them. Do not duplicate rules for
individual providers. Read `PRIVACY.md` before exposing private content to a model.
For document language and hosted-drafting route decisions, follow
`.kilo/rules/document-language.md`.
Run commands from the public project root; `JobSearch/` is the separate private
Obsidian vault.

**Global software-project rules do not apply to job-search work here.** The
global agent instructions (Serena code navigation, the knowledge-graph memory,
vault tickets and progress calendars, Architecture Reference upkeep, branch,
worktree and stash checks) are written for code projects. For application
records, fit assessments, CVs and cover letters, skip them: do not start
Serena, search or write memory, create tickets or inspect branches. Apply them
only when the user asks for a change to the JobJimmy engine itself (scripts,
templates, skills or documentation). This project's `AGENTS.md`,
`PROCEDURES.md` and the skills govern the work. Keep context small: read the
sections you need rather than whole long files, and do not re-read a file you
have already read in this session. **Exception: the voice and style guides**
(the bundled `knowledge/Writing-guide.md` and `knowledge/Reasoning-profile.md`,
and `CV/Style-guide.md` for CVs) are read in full before any drafting or
wording review; skipping them produces flat, generic documents. Drafting itself
goes to the `writer` subagent (`.kilo/agents/writer.md`), one document per
call, as the `tailor-cv` and `write-cover-letter` skills describe. The `writer`
subagent itself is exempt from reading `AGENTS.md`, `PRIVACY.md` and the skills:
its own brief and permissions confine it to the safe bundle.

**Use project-relative paths with every file tool** (`PROCEDURES.md`,
`.kilo/skills/create-application/SKILL.md`, `JobSearch/Templates/...`), never
absolute paths. The OpenRouter sensitive-information guardrail redacts names
in the request, including the account name inside the workspace path, so an
absolute path can reach you as `/Users/[PERSON_NAME]/...`. A path containing a
redaction token such as `[PERSON_NAME]`, `[EMAIL]` or `[PHONE]` does not exist on
disk: drop everything up to the project root and retry with the relative path.
If a "File not found" error shows such a token, the file is usually present. Switching models does not establish approval for a new data route.
In every phase, private raw notes, filenames and tool output must stay out of
a hosted model: run local redaction first and use only checked safe Markdown.
Curated `JobSearch/Knowledge/**` articles are private content too: redact them
with the reversible workflow before any remote read. `redact_md.py check` is a
local safety scanner; a pass is not proof of anonymity and does not authorise
remote use. Never read private identity JSON, document binaries or private Git
diffs into the model. A user message already containing identifiers cannot be
redacted here; report that limitation rather than claiming an automatic boundary.
Never ask the user to paste an advert or email into chat: ask them to copy it
to the clipboard and run `tools/py CV/Scripts/jobflow.py capture --clipboard`.
Routine steps (records, note sections, safe bundles, draft restore, rendering)
are `jobflow.py` commands; use them instead of hand-written tool sequences.

This project has no in-tree Python virtual environment, overriding the global
"create a venv if it does not exist" rule. Never run `uv venv`, `uv sync`,
`uv add` or `uv pip install` in this checkout: a `.venv` exposes installed
third-party metadata and interpreter symlinks to the deep privacy audit and
blocks public commits. Run scripts with `tools/py <script> [args]` (a wrapper for
`uv run --no-project python`), adding optional dependencies with
`JOBJIMMY_PY_WITH="pymupdf certifi"`. See the "Python tooling" section of the
project `AGENTS.md`.
