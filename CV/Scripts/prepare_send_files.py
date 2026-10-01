#!/usr/bin/env python3
"""Create recruiter-friendly copies of approved PDFs without exposing the name.

Reads the vault owner's display name from the same local-only identity JSON used
for cover letters, then writes renamed *copies* beside each approved source PDF.
Source files are never modified or moved. All identity values stay local: this
command prints generic status only and never the resolved name or filename.
"""
import argparse
import hashlib
import shutil
from pathlib import Path

from cover_letter import load_identity
from output_paths import ROOT, check_output

DEFAULT_IDENTITY = ROOT / 'JobSearch/Templates/letter-identity.json'
LABELS = {'cv': 'CV', 'cover-letter': 'Cover Letter'}
UNSAFE_NAME = set('/\\\x00<>:"|?*')


def display_name(identity):
    """Return the local display name as a safe single filename component."""
    name = load_identity(identity)['Signature'][0].strip()
    if (not name or name in ('.', '..') or name != name.rstrip('. ')
            or any(char in UNSAFE_NAME or ord(char) < 32 for char in name)):
        raise ValueError('The local identity display name is not a safe filename.')
    return name


def is_pdf(path):
    with Path(path).open('rb') as stream:
        return b'%PDF-' in stream.read(1024)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()


def plan(identity, sources, root=None):
    """Resolve copy destinations without writing; one (source, destination) per job."""
    name = display_name(identity)
    planned = []
    destinations = set()
    for source, label in sources:
        source = Path(source)
        if not source.is_file():
            raise ValueError('An approved source PDF is missing.')
        if source.suffix.lower() != '.pdf' or not source.stat().st_size or not is_pdf(source):
            raise ValueError('Approved sources must be nonempty PDF files.')
        destination = source.parent / f'{name} - {label}.pdf'
        if destination.exists():
            raise ValueError('A send-ready copy already exists; check it against the approved source.')
        if destination.resolve() == source.resolve():
            raise ValueError('Source and copy must differ.')
        check_output(destination, source, identity, root=root)
        key = destination.resolve()
        if key in destinations:
            raise ValueError('Duplicate copy destination.')
        destinations.add(key)
        planned.append((source, destination))
    return planned


def create(planned):
    """Copy each planned source, verifying byte-for-byte; roll back on failure."""
    created = []
    try:
        for source, destination in planned:
            shutil.copyfile(source, destination)
            created.append(destination)
            if not destination.is_file() or sha256(source) != sha256(destination):
                raise ValueError('A copy does not match the approved source.')
    except BaseException:
        for destination in created:
            destination.unlink(missing_ok=True)
        raise
    return [destination for _, destination in planned]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identity', type=Path, default=DEFAULT_IDENTITY,
                        help='local-only identity JSON; never sent to a model')
    parser.add_argument('--cv', type=Path, help='approved final CV PDF')
    parser.add_argument('--cover-letter', type=Path, help='approved final cover-letter PDF')
    args = parser.parse_args()
    jobs = [(path, LABELS[key]) for key in ('cv', 'cover-letter')
            if (path := getattr(args, key.replace('-', '_'))) is not None]
    if not jobs:
        parser.error('Provide --cv and/or --cover-letter.')
    try:
        create(plan(args.identity, jobs))
    except OSError:
        parser.exit(1, 'Error: Cannot read or write private send-file copies.\n')
    except ValueError as error:
        parser.exit(1, f'Error: {error}\n')
    print('Send-ready copies created; originals unchanged and copies verified byte-for-byte.')


if __name__ == '__main__':
    main()
