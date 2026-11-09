"""Synthetic shared ZIP safety and adapter contract; no customer exports."""
import io
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(Path(__file__).resolve().parents[1] / 'plugins')))
from ag_tech_tooling.archive_sources import validated_members
from ag_tech_tooling import deere_zip


class ArchiveTest(unittest.TestCase):
    def inventory(self, names, **limits):
        stream = io.BytesIO()
        with ZipFile(stream, 'w') as archive:
            for name in names:
                archive.writestr(name, b'fixture')
        stream.seek(0)
        with ZipFile(stream) as archive:
            return validated_members(archive, **limits)

    def test_original_names_and_opaque_nested_archive(self):
        result = self.inventory(['Folder/', 'Folder/Original-Value.fdShape', 'Folder/inner.zip'])
        self.assertEqual(list(result), ['Folder/Original-Value.fdShape', 'Folder/inner.zip'])

    def test_unsafe_and_ambiguous_paths_rejected(self):
        raw_backslash = ZipInfo('Folder/member')
        raw_backslash.filename = 'Folder\\member'  # Bypass Windows ZipInfo separator normalization.
        for name in ['../escape', '/absolute', 'C:/drive', raw_backslash,
                     'Folder//member', 'Folder/./member', './member']:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Unsafe'):
                self.inventory([name])
        for names in [['a.xml', 'A.XML'], ['folder/', 'FOLDER']]:
            with self.subTest(names=names), self.assertRaisesRegex(ValueError, 'duplicate'):
                self.inventory(names)

    def test_links_rejected(self):
        link = ZipInfo('link')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(ValueError, 'linked'):
            self.inventory([link])

    def test_encrypted_header_rejected_without_password(self):
        stream = io.BytesIO()
        with ZipFile(stream, 'w') as archive:
            archive.writestr('data.xml', 'fixture')
        data = bytearray(stream.getvalue())
        central = data.index(b'PK\x01\x02')
        struct.pack_into('<H', data, central + 8, 1)
        struct.pack_into('<H', data, 6, 1)
        with ZipFile(io.BytesIO(data)) as archive:
            with self.assertRaisesRegex(ValueError, 'encrypted'):
                validated_members(archive)

    def test_entry_byte_limits_and_mid_inventory_cancel(self):
        with self.assertRaisesRegex(ValueError, 'limits'):
            self.inventory(['a', 'b'], max_entries=1)
        with self.assertRaisesRegex(ValueError, 'limits'):
            self.inventory(['a'], max_bytes=3)
        calls = []
        def cancel():
            calls.append(True)
            if len(calls) == 3:
                raise RuntimeError('cancelled during inventory')
        with self.assertRaisesRegex(RuntimeError, 'cancelled'):
            self.inventory(['a', 'b', 'c'], check=cancel)

    def test_deere_zip_integrity_and_mid_parse_cancel(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'machine.zip'
            with ZipFile(source, 'w', ZIP_DEFLATED) as archive:
                archive.writestr('profile/RCD/EIC/setup.fds',
                    f'<SetupFile xmlns="{deere_zip.SETUP_NS}"><Client erid="Original-ID" name="Original Name"/></SetupFile>')
            original = source.read_bytes()
            actual = deere_zip._xml_data
            def mutate(data):
                tree = actual(data)
                metadata = source.stat()
                os.utime(source, ns=(metadata.st_atime_ns, metadata.st_mtime_ns + 1000000000))
                return tree
            with patch.object(deere_zip, '_xml_data', side_effect=mutate):
                with self.assertRaisesRegex(RuntimeError, 'Source changed'):
                    deere_zip.inspect_zip(source)
            self.assertEqual(source.read_bytes(), original)
            cancelled = []
            def cancel_after_parse(data):
                tree = actual(data)
                cancelled.append(True)
                return tree
            with patch.object(deere_zip, '_xml_data', side_effect=cancel_after_parse):
                with self.assertRaisesRegex(RuntimeError, 'cancelled'):
                    deere_zip.inspect_zip(source, cancelled=lambda: bool(cancelled))
            result = deere_zip.inspect_zip(source)
            self.assertEqual(result['entities'][0]['id'], 'Original-ID')
            self.assertTrue(result['source_unchanged'])
            self.assertFalse(result['geometry_import_supported'])
            self.assertEqual(source.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
