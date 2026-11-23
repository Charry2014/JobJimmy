#!/usr/bin/env python3
"""Local workflow steps for importing an advert and preparing documents.

Each command does one routine step of the import or document workflow
locally and prints generic status only: counts, PASS/FAIL and vault-relative
paths that a hosted agent may see. Private values (the original advert,
contacts, names, restored text) never appear in the output.

  capture   Read an advert or recruiter email from the clipboard or a file,
            keep the original verbatim in a private inbox, add the contacts
            and email-header names it finds to the redaction policy, and write
            a checked safe copy for the model.
  add-name  Add a name you spotted in a safe copy to the policy (run this in
            your own terminal: the name is typed locally, never into chat),
            then re-prepare the capture's safe copy.
  records   Create the linked application, research, company and recruiter
            notes from the canonical templates and a JSON spec, archive the
            captured original verbatim, and restore any tokens in the spec.
            A rerun is a no-op.
  update    Replace one section of an application, research or company note
            (and optionally set front-matter fields) from a safe Markdown file
            written by the model, restoring its tokens locally.
  bundle    Write checked safe copies of everything a drafting session needs:
            the advert, research and application notes, knowledge articles,
            baselines and the current CV and letter drafts.
  restore   Restore the model's drafts from the bundle's out/ folder into the
            application's CV/ folder, refusing a draft the user changed since
            the bundle was made.
  render    Fold, render and export the CV and/or the letter with every
            mechanical check; stop with a reason on anything unexpected.

Never pass the policy, token registry, inbox originals or restored documents
to a remote model.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import redact_md as rm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = Path(__file__).resolve().parent

ADVERT_START = "<!-- advert:start (verbatim original; do not edit) -->"
ADVERT_END = "<!-- advert:end -->"

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
APP_SLUG = re.compile(r"\d{4}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*")
CAPTURE_ID = re.compile(r"\d{8}-\d{6}")

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+|\b00)\d[\d ()/.-]{6,}\d|\b0\d{2,5}[ /-]?\d{3,}(?:[ -]\d{2,})*\b")
LINKEDIN = re.compile(r"(?:https?://)?(?:[\w-]+\.)?linkedin\.com/in/[\w%.-]+/?", re.I)
HEADER = re.compile(r"^[ \t>]*(?:From|To|Cc|Bcc|Reply-To|Sender|Von|An|Kopie|Absender|Antwort an)"
                    r"[ \t]*:[ \t]*(.+)$", re.I | re.M)
QUOTED_NAME = re.compile(r'"([^"]+)"\s*<[^>]*>')
BARE_NAME = re.compile(r"(?:^|[,;])\s*([^\"<>,;@]+?)\s*<[^>]*>")
NAME = re.compile(r"[^\W\d_][\w'’.-]*(?:,? [^\W\d_][\w'’.-]*){1,3}")

LANGUAGE_PAIRS = {"en": ("letter-template-en.odt", "letter-anchors-en.json"),
                  "de": ("letter-template-de.odt", "letter-anchors-de.json")}


class Vault:
    """Private paths, relative to a public project root (tests use a temporary one)."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.private = self.root / "JobSearch"
        self.policy = self.private / "Templates" / "redaction-policy.json"
        self.registry = self.private / "Templates" / "redaction-tokens.json"
        self.inbox = self.private / "Outputs" / "inbox"
        self.safe = self.private / "Outputs" / "safe"
        self.templates = self.root / "Templates"
        self.knowledge = self.private / "Knowledge"

    def require(self):
        if not self.private.is_dir():
            raise ValueError("Private JobSearch/ tree is not attached.")
        if self.private.is_symlink():
            raise ValueError("The private repository mount must not be a symlink.")

    def rel(self, path):
        try:
            return str(Path(path).relative_to(self.root))
        except ValueError:
            return Path(path).name

    def app_dir(self, slug):
        if not APP_SLUG.fullmatch(slug or ""):
            raise ValueError("Application slug must look like YYYY-MM-company-role.")
        return self.private / "Applications" / slug

    def application(self, slug):
        return self.app_dir(slug) / f"{slug}.md"

    def research(self, slug):
        return self.app_dir(slug) / "Activities" / f"{slug}-research.md"

    def capture_dir(self, capture="latest"):
        if capture in (None, "", "latest"):
            found = sorted(p for p in self.inbox.glob("*") if CAPTURE_ID.fullmatch(p.name))
            if not found:
                raise ValueError("No captured advert in the inbox; run capture first.")
            return found[-1]
        if not CAPTURE_ID.fullmatch(capture):
            raise ValueError("Capture id must look like YYYYMMDD-HHMMSS.")
        path = self.inbox / capture
        if not path.is_dir():
            raise ValueError("Capture not found in the inbox.")
        return path


def today():
    return datetime.date.today().strftime("%d-%m-%Y")


def write_private(path, text, mode=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    if mode is not None:
        temporary.chmod(mode)
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --- capture ---------------------------------------------------------------

def read_clipboard():
    for command in (["pbpaste"], ["wl-paste", "--no-newline"], ["xclip", "-selection", "clipboard", "-o"]):
        if shutil.which(command[0]):
            result = subprocess.run(command, capture_output=True)
            if result.returncode == 0:
                return result.stdout.decode("utf-8", errors="replace")
    raise ValueError("No clipboard reader available; save the text to a file and use --file.")


def header_names(text):
    """Display names from email header lines such as `From: Jane Doe <j@example.com>`."""
    names = []
    for value in HEADER.findall(text):
        found = QUOTED_NAME.findall(value) + BARE_NAME.findall(value)
        if not found and "@" not in value and NAME.fullmatch(value.strip()):
            found = [value.strip()]
        for name in found:
            name = " ".join(name.replace('"', "").split())
            if NAME.fullmatch(name) and all(word[0].isupper() for word in name.replace(",", "").split()):
                names.append(name)
    return names


def discover(text):
    """Return [(value, label)] for contacts and header names found in text."""
    found = []
    for match in LINKEDIN.findall(text):
        found.append((match.rstrip("/."), "LINKEDIN"))
    for match in EMAIL.findall(text):
        found.append((match.rstrip("."), "EMAIL"))
    for match in PHONE.findall(text):
        found.append((match.strip(" .-/("), "PHONE"))
    for name in header_names(text):
        found.append((name, "PERSON"))
        if "," in name:  # "Doe, Jane" -> also "Jane Doe"
            last, first = [part.strip() for part in name.split(",", 1)]
            found.append((f"{first} {last}", "PERSON"))
    unique = {}
    for value, label in found:
        if len(value) >= 4 and not rm.RESERVED.search(value):
            unique.setdefault(value, label)
    return list(unique.items())


def add_to_policy(vault, additions):
    """Append new (value, label) entries to the reviewed policy; return those added."""
    try:
        policy = json.loads(vault.policy.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("Cannot read the private redaction policy; create and review it first.") from None
    known = {value for value, _ in rm.policy_entries(vault.policy)}
    added = [(v, l) for v, l in additions if v not in known]
    if added:
        policy["redact_values"].extend({"value": v, "label": l} for v, l in added)
        write_private(vault.policy, json.dumps(policy, ensure_ascii=False, indent=2) + "\n", 0o600)
    return added


def prepare_text(vault, text):
    """Return (safe text, replaced count, check reasons); saves new tokens."""
    entries = rm.policy_entries(vault.policy)
    registry = rm.load_registry(vault.registry)
    before = dict(registry)
    safe, replaced = rm.redact(text, entries, registry)
    if registry != before:
        rm.save_registry(vault.registry, registry)
    return safe, replaced, rm.scan_reasons(safe, [v for v, _ in entries])


def capture(vault, text, url=""):
    vault.require()
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n") + "\n"
    if not text.strip():
        raise ValueError("Nothing to capture: the clipboard or file is empty.")
    if rm.RESERVED.search(text) or rm.PROVIDER.search(text):
        raise ValueError("The text already contains privacy tokens or provider placeholders; "
                         "copy it again from the original source.")
    added = add_to_policy(vault, discover(text))
    moment = datetime.datetime.now()
    while (vault.inbox / moment.strftime("%Y%m%d-%H%M%S")).exists():
        moment += datetime.timedelta(seconds=1)
    stamp = moment.strftime("%Y%m%d-%H%M%S")
    folder = vault.inbox / stamp
    folder.mkdir(parents=True, exist_ok=False)
    folder.chmod(0o700)
    write_private(folder / "original.txt", text, 0o600)
    safe, replaced, reasons = prepare_text(vault, text)
    write_private(folder / "advert-safe.md", safe)
    write_private(folder / "capture.json",
                  json.dumps({"captured": today(), "url": url, "characters": len(text)}, indent=2) + "\n")
    counts = {label: sum(1 for _, l in added if l == label) for label in ("EMAIL", "PHONE", "LINKEDIN", "PERSON")}
    return {"capture": stamp, "characters": len(text), "added": counts, "replaced": replaced,
            "safe": vault.rel(folder / "advert-safe.md"), "reasons": reasons}


def add_name(vault, name, label="PERSON", capture_id="latest"):
    vault.require()
    name = " ".join(name.split())
    if len(name) < 2 or rm.RESERVED.search(name) or not rm.LABEL.fullmatch(label):
        raise ValueError("Give a real name and a label of capital letters.")
    added = add_to_policy(vault, [(name, label)])
    try:
        folder = vault.capture_dir(capture_id)
    except ValueError:
        return {"added": len(added), "replaced": 0, "reasons": [], "safe": None}
    safe, replaced, reasons = prepare_text(vault, (folder / "original.txt").read_text(encoding="utf-8"))
    write_private(folder / "advert-safe.md", safe)
    return {"added": len(added), "replaced": replaced, "reasons": reasons,
            "safe": vault.rel(folder / "advert-safe.md")}


# --- note editing ----------------------------------------------------------

def split_front(text):
    if not text.startswith("---\n"):
        raise ValueError("Note has no YAML front matter.")
    end = text.index("\n---\n", 4)
    return text[4:end], text[end + 5:]


def yaml_value(value):
    if value is None or value == "":
        return ""
    value = str(value)
    if value.startswith("[[") or re.search(r'^[\[{"\'#&*!|>%@`-]|: | #', value) or value != value.strip():
        return json.dumps(value, ensure_ascii=False)
    return value


def set_fields(text, fields):
    front, body = split_front(text)
    lines = front.split("\n")
    for key, value in fields.items():
        pattern = re.compile(rf"^{re.escape(key)}:")
        for index, line in enumerate(lines):
            if pattern.match(line):
                lines[index] = f"{key}: {yaml_value(value)}".rstrip()
                break
        else:
            lines.append(f"{key}: {yaml_value(value)}".rstrip())
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def get_field(text, key):
    front, _ = split_front(text)
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", front, re.M)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def heading_lines(lines):
    """Yield (index, level, title) for headings outside code fences and the advert archive."""
    fence = advert = False
    for index, line in enumerate(lines):
        if line.strip() == ADVERT_START:
            advert = True
        elif line.strip() == ADVERT_END:
            advert = False
        elif advert:
            continue
        elif line.startswith("```"):
            fence = not fence
        elif not fence:
            match = re.match(r"(#{1,6}) +(.+?)\s*$", line)
            if match:
                yield index, len(match.group(1)), match.group(2)


def section_span(text, title):
    """Return (lines, start, end): body lines are lines[start:end]; None if missing."""
    lines = text.split("\n")
    heads = list(heading_lines(lines))
    for position, (index, level, name) in enumerate(heads):
        if name == title:
            end = next((i for i, l, _ in heads[position + 1:] if l <= level), len(lines))
            return lines, index + 1, end
    return lines, None, None


def replace_section(text, title, body, level=2):
    lines, start, end = section_span(text, title)
    block = [""] + body.strip("\n").split("\n") + [""]
    if start is None:
        return text.rstrip("\n") + "\n\n" + "#" * level + " " + title + "\n" + "\n".join(block)
    if end < len(lines) and block[-1] == "" and lines[end].strip() == "":
        block = block[:-1]
    return "\n".join(lines[:start] + block + lines[end:])


def section_text(text, title):
    lines, start, end = section_span(text, title)
    return None if start is None else "\n".join(lines[start:end]).strip("\n") + "\n"


def advert_text(text):
    if ADVERT_START in text and ADVERT_END in text:
        return text.split(ADVERT_START, 1)[1].split(ADVERT_END, 1)[0].strip("\n") + "\n"
    return section_text(text, "Original job advert")


# --- records ---------------------------------------------------------------

def restore_tree(value, registry):
    if isinstance(value, str):
        return rm.restore(value, registry)
    if isinstance(value, dict):
        return {k: restore_tree(v, registry) for k, v in value.items()}
    if isinstance(value, list):
        return [restore_tree(v, registry) for v in value]
    return value


def slugify(value):
    value = value.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        value = value.replace(a, b)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def template(vault, name):
    path = vault.templates / f"{name}.md"
    if not path.is_file():
        raise ValueError(f"Canonical template Templates/{name}.md is missing.")
    return path.read_text(encoding="utf-8")


def add_list_link(text, title, link):
    """Add `- link` to a bullet list section, replacing an empty `-` placeholder."""
    body = section_text(text, title)
    if body is None:
        return replace_section(text, title, f"- {link}")
    if link in body:
        return text
    items = [line for line in body.split("\n") if line.strip() not in ("", "-")]
    return replace_section(text, title, "\n".join(items + [f"- {link}"]))


def existing_url(vault, url, slug):
    if not url:
        return None
    for note in sorted((vault.private / "Applications").glob("*/*.md")):
        if note.parent.name != slug and note.stem == note.parent.name:
            try:
                if get_field(note.read_text(encoding="utf-8"), "advert_url") == url:
                    return note.parent.name
            except ValueError:
                continue
    return None


def find(vault, company_slug):
    """Existing application slugs and notes for one (public) target organisation."""
    vault.require()
    if not SLUG.fullmatch(company_slug or ""):
        raise ValueError("Give the company or agency slug in lowercase words joined by hyphens.")
    applications = sorted(p.name for p in (vault.private / "Applications").glob("*")
                          if p.is_dir() and f"-{company_slug}-" in f"-{p.name[8:]}-")
    return {"applications": applications,
            "company note": (vault.private / "Companies" / f"{company_slug}.md").is_file(),
            "agency recruiter notes": len(list((vault.private / "Recruiters").glob(f"{company_slug}-*.md")))}


def template_drift(vault):
    """Names of private working templates that differ from the canonical ones."""
    drift = []
    for name in ("Application", "Research", "Company", "Recruiter"):
        private = vault.private / "Templates" / f"{name}.md"
        if private.is_file():
            strip = lambda t: [line.rstrip() for line in t.strip().split("\n")]  # noqa: E731
            if strip(private.read_text(encoding="utf-8")) != strip(template(vault, name)):
                drift.append(name)
    return drift


def records(vault, spec):
    vault.require()
    registry = rm.load_registry(vault.registry)
    spec = restore_tree(spec, registry)
    slug = spec.get("slug", "")
    position = (spec.get("position") or "").strip()
    if not position:
        raise ValueError("The spec needs the exact position title.")
    publisher = spec.get("publisher_type", "unknown")
    if publisher not in ("employer", "recruiter", "unknown"):
        raise ValueError("publisher_type must be employer, recruiter or unknown.")
    company = spec.get("company") or None
    recruiter = spec.get("recruiter") or None
    if company and not SLUG.fullmatch(company.get("slug", "")):
        raise ValueError("company.slug must be lowercase words joined by hyphens.")
    if recruiter and not SLUG.fullmatch(recruiter.get("agency_slug", "")):
        raise ValueError("recruiter.agency_slug must be lowercase words joined by hyphens.")
    url = (spec.get("advert_url") or "").strip()
    duplicate = existing_url(vault, url, slug)
    if duplicate:
        raise ValueError(f"This advert URL is already recorded in application {duplicate}; enrich that one instead.")

    status = {}
    drift = template_drift(vault)
    if drift:
        status["template drift"] = (", ".join(drift) + ": the private working copy differs from the canonical "
                                    "template; the canonical one was used. Ask the user to review the difference.")
    app_path, research_path = vault.application(slug), vault.research(slug)
    company_link = f'[[Companies/{company["slug"]}]]' if company else ""
    recruiter_link = ""

    if recruiter:
        name = (recruiter.get("name") or "").strip()
        person = slugify(name) if name else "contact"
        rslug = f'{recruiter["agency_slug"]}-{person}'
        recruiter_link = f"[[Recruiters/{rslug}]]"
        path = vault.private / "Recruiters" / f"{rslug}.md"
        if path.exists():
            status["recruiter"] = "exists"
        else:
            text = template(vault, "Recruiter")
            text = set_fields(text, {"recruitment_company": recruiter.get("agency", ""),
                                     "recruiter_name": name,
                                     "email": recruiter.get("email", ""),
                                     "phone": recruiter.get("phone", ""),
                                     "linkedin": recruiter.get("linkedin", ""),
                                     "website": recruiter.get("website", ""),
                                     "last_verified": today()})
            text = text.replace("# Recruitment company — Recruiter name",
                                f'# {recruiter.get("agency", "")} — {name or "Contact"}')
            write_private(path, text)
            status["recruiter"] = "created"
    else:
        status["recruiter"] = "none"

    app_link = f"[[Applications/{slug}/{slug}]]"
    if app_path.exists():
        status["application"] = "exists"
    else:
        text = template(vault, "Application").replace("{{title}}", slug)
        text = set_fields(text, {"company": company_link, "position": position,
                                 "status": "researching", "priority": "medium", "fit": "",
                                 "location": spec.get("location", ""), "source": spec.get("source", ""),
                                 "publisher_type": publisher, "recruiter": recruiter_link,
                                 "advert_url": url, "date_found": spec.get("date_found") or today(),
                                 "date_applied": "", "next_action": "Send Application",
                                 "next_action_date": "", "notion_id": ""})
        organisation = (company or {}).get("name") or (recruiter or {}).get("agency", "") or "Undisclosed client"
        text = text.replace("# Position title — Company", f"# {position} — {organisation}")
        write_private(app_path, text)
        status["application"] = "created"

    if research_path.exists():
        status["research"] = "exists"
    else:
        text = template(vault, "Research").replace("{{date:DD-MM-YYYY}}", today())
        fields = {"application": app_link, "advert_url": url}
        capture_id = spec.get("capture")
        if capture_id:
            folder = vault.capture_dir(capture_id)
            original = (folder / "original.txt").read_text(encoding="utf-8")
            meta = json.loads((folder / "capture.json").read_text(encoding="utf-8"))
            fields["advert_captured"] = meta.get("captured", today())
            if not url and meta.get("url"):
                fields["advert_url"] = meta["url"]
            text = replace_section(text, "Original job advert",
                                   f"{ADVERT_START}\n\n{original.strip(chr(10))}\n\n{ADVERT_END}")
            meta["application"] = slug
            write_private(folder / "capture.json", json.dumps(meta, indent=2) + "\n")
            status["advert"] = f"archived verbatim ({original.count(chr(10))} lines)"
        else:
            status["advert"] = "not captured"
        write_private(research_path, set_fields(text, fields))
        status["research"] = "created"

    if company:
        path = vault.private / "Companies" / f'{company["slug"]}.md'
        if path.exists():
            text = path.read_text(encoding="utf-8")
            updated = add_list_link(text, "Applications", app_link)
            status["company"] = "linked" if updated != text else "exists"
            if updated != text:
                write_private(path, updated)
        else:
            text = template(vault, "Company")
            name = company.get("name") or company["slug"]
            text = set_fields(text, {"company": name, "website": company.get("website", ""),
                                     "location": company.get("location", ""), "last_reviewed": today()})
            text = text.replace("\n# Company name\n", f"\n# {name}\n", 1)
            write_private(path, add_list_link(text, "Applications", app_link))
            status["company"] = "created"
    else:
        status["company"] = "none"
    return status


# --- update ----------------------------------------------------------------

def note_path(vault, slug, which):
    if which == "application":
        return vault.application(slug)
    if which == "research":
        return vault.research(slug)
    if which in ("company", "recruiter"):
        folder = "Companies" if which == "company" else "Recruiters"
        link = get_field(vault.application(slug).read_text(encoding="utf-8"), which)
        match = re.fullmatch(rf"\[\[{folder}/([a-z0-9-]+)(?:\|.*)?\]\]", link)
        if not match:
            raise ValueError(f"The application links no {which} note.")
        return vault.private / folder / f"{match.group(1)}.md"
    raise ValueError("Note must be application, research, company or recruiter.")


def update(vault, slug, which, section=None, content=None, fields=None, level=2, append=False):
    vault.require()
    path = note_path(vault, slug, which)
    if not path.is_file():
        raise ValueError(f"The {which} note does not exist; run records first.")
    registry = rm.load_registry(vault.registry)
    text = path.read_text(encoding="utf-8")
    if section:
        if section == "Original job advert" and ADVERT_START in text:
            raise ValueError("The archived original advert is never rewritten.")
        if content is None:
            raise ValueError("A section update needs --from.")
        content = rm.restore(content, registry)
        if append:
            current = section_text(text, section) or ""
            content = (current.rstrip("\n") + "\n\n" + content.strip("\n")).strip("\n")
        text = replace_section(text, section, content, level)
    if fields:
        text = set_fields(text, {k: rm.restore(v, registry) for k, v in fields.items()})
    split_front(text)
    write_private(path, text)


# --- bundle and restore ----------------------------------------------------

DRAFT = re.compile(r".+-(?:cv-draft|cover-letter-prose)(?:-[a-z]{2})?\.md")


def bundle(vault, slug, knowledge=None, baselines=()):
    vault.require()
    app_path, research_path = vault.application(slug), vault.research(slug)
    if not app_path.is_file() or not research_path.is_file():
        raise ValueError("Application or research note missing; run records first.")
    out = vault.safe / slug
    for child in ("advert.md", "research.md", "application.md", "company.md"):
        (out / child).unlink(missing_ok=True)
    for child in ("knowledge", "baseline", "drafts"):
        shutil.rmtree(out / child, ignore_errors=True)
    (out / "out").mkdir(parents=True, exist_ok=True)

    sources = []
    research = research_path.read_text(encoding="utf-8")
    advert = advert_text(research)
    if advert:
        sources.append(("advert.md", advert))
    lines, start, end = section_span(research, "Original job advert")
    rest = research if start is None else "\n".join(lines[:start] + ["", "(See advert.md.)", ""] + lines[end:])
    sources.append(("research.md", rest))
    sources.append(("application.md", app_path.read_text(encoding="utf-8")))
    try:
        sources.append(("company.md", note_path(vault, slug, "company").read_text(encoding="utf-8")))
    except (ValueError, OSError):
        pass
    articles = (sorted(vault.knowledge.glob("*.md")) if knowledge is None
                else [vault.knowledge / f"{name}.md" for name in knowledge])
    for article in articles:
        if not article.is_file():
            raise ValueError(f"Knowledge article {article.name} not found.")
        sources.append((f"knowledge/{article.name}", article.read_text(encoding="utf-8")))
    for name in baselines:
        path = vault.private / "Templates" / f"{name}.md"
        if not path.is_file():
            raise ValueError(f"Baseline {name}.md not found in JobSearch/Templates/.")
        sources.append((f"baseline/{name}.md", path.read_text(encoding="utf-8")))
    manifest = {}
    cv_dir = vault.app_dir(slug) / "CV"
    for draft in sorted(cv_dir.glob("*.md")) if cv_dir.is_dir() else []:
        if DRAFT.fullmatch(draft.name):
            sources.append((f"drafts/{draft.name}", draft.read_text(encoding="utf-8")))
            manifest[draft.name] = digest(draft)

    contacts = [(v, l) for _, text in sources for v, l in discover(text) if l != "PERSON"]
    added = add_to_policy(vault, contacts)
    results = []
    if added:
        results.append(("policy", "UPDATED", f"{len(added)} contact value(s) added (values withheld)"))
    for name, text in sources:
        try:
            safe, replaced, reasons = prepare_text(vault, text)
        except ValueError as error:
            results.append((name, "WITHHELD", str(error)))
            continue
        if reasons:
            results.append((name, "WITHHELD", ", ".join(reasons)))
            continue
        write_private(out / name, safe)
        results.append((name, "PASS", f"{replaced} replaced"))
    write_private(out / "out" / ".bundle.json", json.dumps({"drafts": manifest}, indent=2) + "\n")
    return out, results


def restore_drafts(vault, slug):
    vault.require()
    out = vault.safe / slug / "out"
    manifest_path = out / ".bundle.json"
    if not manifest_path.is_file():
        raise ValueError("No bundle for this application; run bundle first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))["drafts"]
    registry = rm.load_registry(vault.registry)
    cv_dir = vault.app_dir(slug) / "CV"
    results = []
    for response in sorted(out.glob("*.md")):
        if not DRAFT.fullmatch(response.name):
            results.append((response.name, "SKIPPED", "not a CV draft or letter prose file name"))
            continue
        target = cv_dir / response.name
        if target.exists() and manifest.get(response.name) != digest(target):
            results.append((response.name, "REFUSED", "the draft changed since the bundle; run bundle and revise again"))
            continue
        try:
            text = rm.restore(response.read_text(encoding="utf-8"), registry)
        except ValueError as error:
            results.append((response.name, "REFUSED", str(error)))
            continue
        write_private(target, text)
        manifest[response.name] = digest(target)
        response.unlink()
        results.append((response.name, "RESTORED", vault.rel(target)))
    write_private(manifest_path, json.dumps({"drafts": manifest}, indent=2) + "\n")
    return results


# --- render ----------------------------------------------------------------

def document_language(vault, slug, override=None):
    language = override or get_field(vault.research(slug).read_text(encoding="utf-8"), "document_language")
    if not re.fullmatch(r"[a-z]{2}", language or ""):
        raise ValueError("document_language is not set on the research note; decide it before rendering.")
    return language


def find_one(folder, pattern, what):
    found = sorted(p for p in folder.glob(pattern) if not p.name.endswith((".tmp",)))
    if len(found) != 1:
        raise ValueError(f"Expected exactly one {what} ({pattern}); found {len(found)}.")
    return found[0]


def run_script(script, *args, extra=None):
    command = [sys.executable, str(SCRIPTS / script), *map(str, args)]
    if extra:
        command = extra + command[1:]
    result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    return result.returncode, (result.stdout + result.stderr).strip()


def export_odt(odt, pdf):
    from office import find_soffice, soffice_env
    with tempfile.TemporaryDirectory(prefix="export-", dir=pdf.parent) as temporary:
        result = subprocess.run([find_soffice(), "--headless", "--convert-to", "pdf", "--outdir",
                                 temporary, str(odt)], capture_output=True, env=soffice_env())
        rendered = Path(temporary) / (odt.stem + ".pdf")
        if result.returncode or not rendered.is_file():
            raise ValueError("LibreOffice PDF export failed.")
        rendered.replace(pdf)


def render_cv(vault, slug, baseline, language, accept_fallbacks=False, replace=False, accept_layout=False):
    cv_dir = vault.app_dir(slug) / "CV"
    suffix = "" if language == "en" else f"-{language}"
    pattern = "*-cv-draft.md" if language == "en" else f"*-cv-draft-{language}.md"
    try:
        draft = find_one(cv_dir, pattern, "CV draft")
    except ValueError:
        if language != "en":
            raise
        draft = find_one(cv_dir, "*-cv-draft-en.md", "CV draft")
    prefix = draft.name.split("-cv-draft")[0]
    odt_template = vault.private / "Templates" / f"{baseline}.odt"
    if not odt_template.is_file():
        raise ValueError(f"Baseline {baseline}.odt not found; for the personal-master pipeline use populate_cv.py.")
    blocks = cv_dir / f"{prefix}-cv-blocks{suffix}.md"
    report = cv_dir / f"{prefix}-cv-blocks{suffix}-report.json"
    odt, pdf = cv_dir / f"{prefix}-cv{suffix}.odt", cv_dir / f"{prefix}-cv{suffix}.pdf"
    preview = cv_dir / f"{prefix}-cv{suffix}-preview.pdf"
    lines = []
    if pdf.exists() and not replace:
        raise StepFailure(lines, "a final CV PDF exists; rerun with --replace once the user approves replacing it")
    code, _ = run_script("align_md.py", draft, odt_template, blocks, "--report", report)
    if code:
        raise StepFailure(lines, "fold failed (align_md.py); check the draft's structure")
    data = json.loads(report.read_text(encoding="utf-8"))
    dropped, fallbacks = len(data["dropped_source"]), len(data["fallback_blocks"])
    lines.append(f"fold: {data['pairs']} matched, {fallbacks} baseline fallbacks, {dropped} source units dropped")
    if dropped:
        raise StepFailure(lines, "draft text was dropped by the fold; correct the draft structure and rerun")
    if fallbacks and not accept_fallbacks:
        raise StepFailure(lines, "baseline fallbacks need the user's confirmation (unchanged baseline text kept); "
                                 "rerun with --accept-fallbacks once confirmed")
    code, _ = run_script("cv.py", "render", blocks, odt_template, odt)
    if code:
        raise StepFailure(lines, "ODT render failed")
    lines.append("odt: rendered")
    preview.unlink(missing_ok=True)
    export_odt(odt, preview)
    lines.append("preview pdf: exported with the template fonts (tools/soffice environment)")
    config = vault.private / "Templates" / f"{baseline}-layout-pages.json"
    uv = shutil.which("uv")
    if not config.is_file() or not uv:
        lines.append("layout: automated check unavailable (no layout profile for this baseline, or uv missing)")
    else:
        tailored = layout(preview, config, uv)
        reference = layout(baseline_pdf(vault, baseline, odt_template), config, uv)
        lines.append("layout: " + describe(tailored) + " | unchanged baseline: " + describe(reference))
        sparse = [str(page) for page, blank in tailored["blank"].items() if blank > 5]
        if accept_layout:
            lines.append("layout: accepted by the user (--accept-layout); record the exception with the document")
        elif tailored["structural"] or tailored["pages"] != reference["pages"]:
            raise StepFailure(lines, "page allocation differs from the baseline (overflow, moved sections or page "
                                     "count); the preview PDF is kept for inspection. Do not shrink text or move "
                                     "breaks; ask the user")
        elif sparse:
            raise StepFailure(lines, f"underfill: more than five blank lines at the bottom of page(s) "
                                     f"{', '.join(sparse)}. Show the user these figures and the baseline's; they "
                                     "accept the space (--accept-layout) or direct sourced content changes")
    preview.replace(pdf)
    lines.append("pdf: final CV PDF written")
    return lines


UNDERFILL = re.compile(r"blank lines at bottom")


def layout(pdf, config, uv):
    """Run check_layout.py locally; return page count, blank lines and structural error count."""
    with tempfile.TemporaryDirectory(prefix="layout-", dir=pdf.parent) as temporary:
        report = Path(temporary) / "layout.json"
        run_script("check_layout.py", pdf, "--config", config, "--report", report,
                   extra=[uv, "run", "--no-project", "--with", "pymupdf", "python"])
        if not report.is_file():
            raise ValueError("Layout check could not run (PyMuPDF unavailable?).")
        result = json.loads(report.read_text(encoding="utf-8"))
    return {"pages": len(result["pages"]),
            "blank": {page["page"]: round(page["bottom_blank_lines"], 1) for page in result["pages"]},
            "structural": sum(1 for error in result["errors"] if not UNDERFILL.search(error))}


def describe(result):
    blank = ", ".join(f"p{page} {lines}" for page, lines in result["blank"].items())
    return f"{result['pages']} pages, blank lines at bottom {blank}, {result['structural']} allocation errors"


def baseline_pdf(vault, baseline, odt_template):
    """The unchanged baseline's PDF, rendered once into Outputs/Baselines/ when missing."""
    folder = vault.private / "Outputs" / "Baselines"
    for name in (f"{baseline}-baseline.pdf", f"{baseline}.pdf"):
        if (folder / name).is_file():
            return folder / name
    reference = vault.private / "Templates" / f"{baseline}.md"
    odt = folder / f"{baseline}-baseline.odt"
    folder.mkdir(parents=True, exist_ok=True)
    code, _ = run_script("cv.py", "render", reference, odt_template, odt)
    if code:
        raise ValueError("Could not render the unchanged baseline for comparison.")
    export_odt(odt, folder / f"{baseline}-baseline.pdf")
    return folder / f"{baseline}-baseline.pdf"


def render_letter(vault, slug, language, replace=False):
    import cover_letter as cl
    cv_dir = vault.app_dir(slug) / "CV"
    if language not in LANGUAGE_PAIRS:
        raise ValueError(f"No validated letter template pair for '{language}'.")
    suffix = "" if language == "en" else f"-{language}"
    pattern = "*-cover-letter-prose.md" if language == "en" else f"*-cover-letter-prose-{language}.md"
    try:
        prose = find_one(cv_dir, pattern, "letter prose")
    except ValueError:
        if language != "en":
            raise
        prose = find_one(cv_dir, "*-cover-letter-prose-en.md", "letter prose")
    prefix = prose.name.split("-cover-letter-prose")[0]
    identity = vault.private / "Templates" / "letter-identity.json"
    template_name, anchors_name = LANGUAGE_PAIRS[language]
    letter_template = vault.private / "Templates" / template_name
    anchors = vault.private / "Templates" / anchors_name
    if not letter_template.is_file() or not anchors.is_file():
        raise ValueError(f"Letter template pair for '{language}' is missing.")
    complete = cv_dir / f"{prefix}-cover-letter{suffix}.md"
    odt, pdf = cv_dir / f"{prefix}-cover-letter{suffix}.odt", cv_dir / f"{prefix}-cover-letter{suffix}.pdf"
    preview = cv_dir / f"{prefix}-cover-letter{suffix}-preview.pdf"
    lines = []
    if pdf.exists() and not replace:
        raise StepFailure(lines, "a final letter PDF exists; rerun with --replace once the user approves replacing it")
    cl.load_identity(identity)
    lines.append("identity: complete (values withheld)")
    values = cl.read_markdown(prose, identity)
    text = "\n\n".join("## " + name + "\n\n" + ("\n\n" if name == "Body" else "\n").join(values[name])
                       for name in cl.SECTIONS) + "\n"
    if complete.exists() and complete.read_text(encoding="utf-8") != text:
        if complete.stat().st_mtime > prose.stat().st_mtime:
            raise StepFailure(lines, "the complete letter was edited after its prose; carry those edits "
                                     "into the prose file, then rerun")
    write_private(complete, text)
    lines.append("complete letter: hydrated locally")
    preview.unlink(missing_ok=True)
    cl.render(complete, letter_template, odt, config_path=anchors)
    try:
        cl.export_pdf(odt, preview)
        lines.append("preview pdf: exactly one page")
    except ValueError as error:
        if "pages" not in str(error):
            raise StepFailure(lines, str(error)) from None
        cl.render(complete, letter_template, odt, config_path=anchors, compact_title_gap=True)
        try:
            cl.export_pdf(odt, preview)
        except ValueError:
            raise StepFailure(lines, "the letter overflows one page even with the compact title gap; "
                                     "ask the user how to proceed") from None
        lines.append("preview pdf: exactly one page after the one allowed compact-title-gap retry")
    preview.replace(pdf)
    lines.append("pdf: final letter PDF written")
    return lines


class StepFailure(Exception):
    def __init__(self, lines, reason):
        super().__init__(reason)
        self.lines = lines


# --- command line ----------------------------------------------------------

def print_results(results):
    failed = False
    for name, state, detail in results:
        print(f"{state} {name}" + (f": {detail}" if detail else ""))
        failed = failed or state in ("WITHHELD", "REFUSED")
    return failed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("capture", help="capture an advert or email from the clipboard or a file")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--clipboard", action="store_true")
    source.add_argument("--file", type=Path)
    p.add_argument("--url", default="", help="the advert's public URL, if known")
    p = commands.add_parser("add-name", help="add a name to the policy (type it in your own terminal)")
    p.add_argument("--label", default="PERSON")
    p.add_argument("--capture", default="latest")
    p = commands.add_parser("find", help="existing applications and notes for one company or agency slug")
    p.add_argument("company_slug")
    p = commands.add_parser("records", help="create the linked notes from a JSON spec")
    p.add_argument("spec", type=Path)
    p = commands.add_parser("update", help="replace a note section or set fields from safe Markdown")
    p.add_argument("slug")
    p.add_argument("note", choices=["application", "research", "company", "recruiter"])
    p.add_argument("--section")
    p.add_argument("--level", type=int, default=2, choices=[2, 3])
    p.add_argument("--from", dest="source", type=Path)
    p.add_argument("--append", action="store_true", help="add to the end of the section instead of replacing it")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p = commands.add_parser("bundle", help="write checked safe copies for a drafting session")
    p.add_argument("slug")
    p.add_argument("--knowledge", action="append", help="article name without .md (default: all)")
    p.add_argument("--baseline", action="append", default=[], help="baseline name, e.g. VP-CTO")
    p = commands.add_parser("restore", help="restore drafts from the bundle's out/ folder")
    p.add_argument("slug")
    p = commands.add_parser("render", help="fold, render and export with all checks")
    p.add_argument("slug")
    p.add_argument("--cv", metavar="BASELINE", help="render the CV with this extracted baseline")
    p.add_argument("--letter", action="store_true", help="render the cover letter")
    p.add_argument("--language", help="override document_language from the research note")
    p.add_argument("--accept-fallbacks", action="store_true",
                   help="the user confirmed the baseline fallbacks the fold reported")
    p.add_argument("--accept-layout", action="store_true",
                   help="the user accepted the measured layout differences from the baseline")
    p.add_argument("--replace", action="store_true", help="replace existing final PDFs (user-approved)")
    args = parser.parse_args(argv)
    vault = Vault()
    try:
        if args.command == "capture":
            text = read_clipboard() if args.clipboard else args.file.read_text(encoding="utf-8")
            result = capture(vault, text, args.url)
            added = ", ".join(f"{n} {k.lower()}" for k, n in result["added"].items() if n) or "nothing new"
            print(f"Captured {result['characters']} characters as {result['capture']}.")
            print(f"Redaction policy: added {added} (values withheld).")
            print(f"Safe copy: {result['safe']} ({result['replaced']} replaced; "
                  f"check {'FAIL: ' + ', '.join(result['reasons']) if result['reasons'] else 'PASS'}).")
            print("Read only the safe copy. If it still shows a person's name, ask the user to run "
                  "`tools/py CV/Scripts/jobflow.py add-name` in their own terminal.")
            if args.file:
                print("The source file was left in place; delete it once the capture is archived.")
            return 1 if result["reasons"] else 0
        if args.command == "add-name":
            if not sys.stdin.isatty():
                raise ValueError("Run add-name in your own terminal; the name is typed locally.")
            result = add_name(vault, input("Name or other value to redact: "), args.label, args.capture)
            print(f"Policy: {result['added']} added.")
            if result["safe"]:
                print(f"Safe copy re-prepared: {result['safe']} ({result['replaced']} replaced; "
                      f"check {'FAIL' if result['reasons'] else 'PASS'}). Rerun bundle for other safe copies.")
            return 0
        if args.command == "find":
            result = find(vault, args.company_slug)
            print("applications: " + (", ".join(result["applications"]) or "none"))
            print(f"company note: {'exists' if result['company note'] else 'none'}")
            print(f"agency recruiter notes: {result['agency recruiter notes']}")
            return 0
        if args.command == "records":
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            for kind, state in records(vault, spec).items():
                print(f"{kind}: {state}")
            return 0
        if args.command == "update":
            fields = {}
            for item in args.set:
                key, sep, value = item.partition("=")
                if not sep or not re.fullmatch(r"[a-z_]+", key):
                    raise ValueError("--set takes key=value with a lowercase key.")
                fields[key] = value
            content = args.source.read_text(encoding="utf-8") if args.source else None
            update(vault, args.slug, args.note, args.section, content, fields, args.level, args.append)
            print(f"{args.note} note updated" + (f": section '{args.section}'" if args.section else "")
                  + (f"; {len(fields)} field(s) set" if fields else "") + ".")
            return 0
        if args.command == "bundle":
            out, results = bundle(vault, args.slug, args.knowledge, args.baseline)
            print(f"Safe bundle: {vault.rel(out)}/ (write drafts to its out/ folder, named like the CV/ drafts)")
            return 1 if print_results(results) else 0
        if args.command == "restore":
            results = restore_drafts(vault, args.slug)
            if not results:
                print("Nothing to restore in out/.")
            return 1 if print_results(results) else 0
        if args.command == "render":
            if not args.cv and not args.letter:
                raise ValueError("Choose --cv BASELINE and/or --letter.")
            language = document_language(vault, args.slug, args.language)
            failed = False
            for name, job in (("CV", args.cv and (lambda: render_cv(vault, args.slug, args.cv, language,
                                                                       args.accept_fallbacks, args.replace,
                                                                       args.accept_layout))),
                              ("Letter", args.letter and (lambda: render_letter(vault, args.slug, language,
                                                                                  args.replace)))):
                if not job:
                    continue
                try:
                    for line in job():
                        print(f"{name} {line}")
                    print(f"{name}: OK ({language}). Inspect the PDF locally before approval.")
                except StepFailure as failure:
                    for line in failure.lines:
                        print(f"{name} {line}")
                    print(f"{name}: STOPPED: {failure}")
                    failed = True
                except ValueError as error:
                    print(f"{name}: STOPPED: {error}")
                    failed = True
            return 1 if failed else 0
    except OSError:
        print("Error: cannot read or write a private file.", file=sys.stderr)
        return 1
    except (ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
