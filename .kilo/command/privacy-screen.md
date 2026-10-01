---
description: "Privacy-screen all outer-repository changes for personal data"
---

Run the privacy screening gate from the repository root:

```sh
python3 tools/privacy_screen.py
```

If it reports violations, treat every finding as a blocker: fix each one by
moving the personal content into the private `JobSearch/` tree, replacing it
with a generic placeholder, or removing it, then re-run the screen until it is
clean. Never stage, commit or push while findings exist, and never copy the
personal values into other public files or commit messages — report findings
in chat with categories and locations only.

For a deep audit of the whole outer repository use
`python3 tools/privacy_screen.py --all`; the pattern screen is necessary but
not sufficient, so also review the diff for personal data the patterns cannot
recognise (see the "Privacy screening (hard gate)" section of `AGENTS.md`).