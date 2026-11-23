import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path
from unittest import mock

import office


class FontconfigTests(unittest.TestCase):
    def test_config_is_valid_xml_with_mac_dirs_and_substitutes(self):
        text = office.fontconfig_text(Path('/tmp/example/fonts.conf'))
        document = xml.dom.minidom.parseString(text.split('\n', 2)[2])
        dirs = [d.firstChild.data for d in document.getElementsByTagName('dir')]
        self.assertIn('~/Library/Fonts', dirs)
        self.assertIn('/System/Library/Fonts', dirs)
        families = [f.firstChild.data for f in document.getElementsByTagName('family')]
        self.assertEqual(families[:2], ['Calibri', 'Carlito'])
        include = document.getElementsByTagName('include')[0]
        self.assertEqual(include.getAttribute('ignore_missing'), 'yes')
        self.assertEqual(include.firstChild.data, '/tmp/example/fonts.conf')

    def test_private_include_is_absolute(self):
        self.assertTrue(office.PRIVATE_FONTS.is_absolute())
        self.assertEqual(office.PRIVATE_FONTS.parts[-3:], ('JobSearch', 'Templates', 'fonts.conf'))

    def test_write_config_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'sub' / 'fonts.conf'
            office.write_config(path)
            first = path.stat().st_mtime_ns
            office.write_config(path)
            self.assertEqual(path.stat().st_mtime_ns, first)
            self.assertEqual(path.read_text(encoding='utf-8'), office.fontconfig_text())


class EnvironmentTests(unittest.TestCase):
    def test_macos_sets_fontconfig_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'fonts.conf'
            with mock.patch.object(office, 'config_path', return_value=target):
                env = office.soffice_env({}, 'darwin')
            self.assertEqual(env['FONTCONFIG_FILE'], str(target))
            self.assertTrue(target.is_file())

    def test_explicit_fontconfig_file_is_kept(self):
        env = office.soffice_env({'FONTCONFIG_FILE': '/custom.conf'}, 'darwin')
        self.assertEqual(env['FONTCONFIG_FILE'], '/custom.conf')

    def test_other_platforms_unchanged(self):
        self.assertEqual(office.soffice_env({'A': '1'}, 'linux'), {'A': '1'})


class DiscoveryTests(unittest.TestCase):
    def test_missing_soffice_raises(self):
        with mock.patch.object(office, 'MAC_SOFFICE', Path('/nonexistent/soffice')), \
                mock.patch.object(office.shutil, 'which', return_value=None):
            with self.assertRaises(ValueError):
                office.find_soffice()

    def test_path_fallback(self):
        with mock.patch.object(office, 'MAC_SOFFICE', Path('/nonexistent/soffice')), \
                mock.patch.object(office.shutil, 'which', return_value='/usr/bin/soffice'):
            self.assertEqual(office.find_soffice(), '/usr/bin/soffice')


if __name__ == '__main__':
    unittest.main()
