# Shared JobJimmy instructions

For every Kilo mode and model family, read the project-root `AGENTS.md` and follow
its task routing. Skills are agent-agnostic under `.kilo/skills/`; read their
SKILL.md directly if discovery does not expose them. Do not duplicate rules for
individual providers. Read `PRIVACY.md` before exposing private content to a model.
Run commands from the public project root; `JobSearch/` is the separate private
Obsidian vault. Switching models does not establish approval for a new data route.
In every phase, private raw notes, filenames and tool output must stay out of
a hosted model: run local redaction first and use only checked safe Markdown.
Curated `JobSearch/Knowledge/**` articles are the exception — once
`tools/py CV/Scripts/redact_md.py check` passes they may be sent directly; run
it after every knowledge edit and fix the article on failure, do not send it.
Never read private identity JSON, document binaries or private Git diffs into
the model. A user message already containing identifiers cannot be redacted
here; report that limitation rather than claiming an automatic boundary.

This project has no in-tree Python virtual environment, overriding the global
"create a venv if it does not exist" rule. Never run `uv venv`, `uv sync`,
`uv add` or `uv pip install` in this checkout: a `.venv` exposes installed
third-party metadata and interpreter symlinks to the deep privacy audit and
blocks public commits. Run scripts with `tools/py <script> [args]` (a wrapper for
`uv run --no-project python`), adding optional dependencies with
`JOBJIMMY_PY_WITH="pymupdf certifi"`. See the "Python tooling" section of the
project `AGENTS.md`.
