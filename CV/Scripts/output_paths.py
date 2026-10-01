"""Keep personal artifacts out of the public workspace; no filesystem writes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check_output(output, *sources, root=None):
    root = Path(root or ROOT).resolve()
    private = root / 'JobSearch'
    destination = Path(output).absolute()
    resolved = destination.resolve()
    if private.is_symlink():
        raise ValueError('The private repository mount must not be a symlink.')
    private_input = any(Path(p).absolute().is_relative_to(private)
                        or Path(p).resolve().is_relative_to(private) for p in sources)
    private_output = destination.is_relative_to(private)
    if (private_input or private_output) and not resolved.is_relative_to(private):
        raise ValueError('Private artifact destination escapes JobSearch/.')
    if (destination.is_relative_to(root) or resolved.is_relative_to(root)) and not resolved.is_relative_to(private):
        raise ValueError('Generated artifacts must not be written into the public project; use JobSearch/.')
    return Path(output)
