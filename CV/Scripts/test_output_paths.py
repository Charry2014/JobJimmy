"""Synthetic path-boundary regressions; never read private documents."""
from pathlib import Path
import tempfile
import unittest
from output_paths import check_output


class OutputPathTests(unittest.TestCase):
    def test_private_input_cannot_escape_or_follow_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'workspace'
            private = root / 'JobSearch'
            private.mkdir(parents=True)
            source = private / 'body.md'
            self.assertEqual(check_output(private / 'out.odt', source, root=root), private / 'out.odt')
            for dest in (root / 'CV/out.odt', Path(tmp) / 'outside.odt'):
                with self.assertRaises(ValueError):
                    check_output(dest, source, root=root)
            (private / 'escape').symlink_to(Path(tmp), target_is_directory=True)
            with self.assertRaises(ValueError):
                check_output(private / 'escape/out.odt', source, root=root)

    def test_public_output_is_rejected_even_for_external_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'workspace'
            root.mkdir()
            with self.assertRaises(ValueError):
                check_output(root / 'CV/out.odt', Path(tmp) / 'source.odt', root=root)
            check_output(Path(tmp) / 'synthetic.odt', root=root)
