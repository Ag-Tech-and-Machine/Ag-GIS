"""Portable security/contract tests; no QGIS, network or profile writes."""
import importlib.util
from pathlib import Path
import unittest
import json
import hashlib
import os
import tempfile
import zipfile
import stat
import warnings
import subprocess
import sys
import struct
from unittest.mock import patch

SCRATCH = (Path.home() / 'AppData/Local/hermes/cache/scratch' if os.name == 'nt'
           else Path.home() / '.cache/hermes/scratch')
SCRATCH.mkdir(parents=True, exist_ok=True)
META = '[general]\nname=Ag-GIS\nversion=0.12.3\nqgisMinimumVersion=3.28\nexperimental=True\n'


def package(path, metadata=META, extra=()):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('ag_tech_tooling/metadata.txt', metadata)
        archive.writestr('ag_tech_tooling/__init__.py', 'def classFactory(iface): pass\n')
        archive.writestr('ag_tech_tooling/plugin.py', '# test fixture\n')
        for name, data in extra:
            if isinstance(name, str) and '\\' in name:
                # ZipInfo normalises backslashes on Windows; keep a hostile raw name.
                raw_name = zipfile.ZipInfo('placeholder.py')
                raw_name.filename = name
                raw_name.orig_filename = name
                name = raw_name
            archive.writestr(name, data)
    data = path.read_bytes()
    return release(size=len(data), sha256=hashlib.sha256(data).hexdigest(), qgis_maximum='')

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = Path(os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(ROOT / 'plugins'))) / 'ag_tech_tooling'
SPEC = importlib.util.spec_from_file_location('update_catalog', PLUGIN_ROOT / 'update_catalog.py')
assert SPEC is not None and SPEC.loader is not None


def module():
    assert SPEC is not None and SPEC.loader is not None
    result = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(result)
    return result


def release(**changes) -> dict:
    result = dict(version='0.12.3', channel='preview', qgis_minimum='3.28', qgis_maximum='3.99',
                  url='https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v0.12.3/ag_tech_tooling-0.12.3.zip',
                  sha256='a' * 64, size=1000, notes='Test release', restart_required=True, data_upgrade=False)
    result.update(changes)
    return result


def catalog(*releases):
    return json.dumps(dict(schema_version=1, releases=list(releases))).encode()


class CatalogTests(unittest.TestCase):
    def test_rejects_untrusted_or_malformed_catalog(self):
        api = module()
        bad = [b'{}', b'{"schema_version":1,"schema_version":1,"releases":[]}', catalog(release(), release()),
               catalog(release(channel='stable'), release(channel='preview')),
               b'x' * (api.MAX_CATALOG_BYTES + 1), catalog(*[release(version=f'1.0.{n}') for n in range(257)])]
        for changes in ({'url': 'https://evil.test/a.zip'}, {'url': release()['url'] + '?x=1'},
                        {'url': release()['url'].replace('github.com', 'user@github.com')},
                        {'url': release()['url'].replace('.zip', '.exe')}, {'url': release()['url'].replace('Ag-GIS', 'other')},
                        {'sha256': 'A' * 64}, {'size': True}, {'size': 0}, {'size': api.MAX_PACKAGE_BYTES + 1},
                        {'qgis_minimum': '4.0'}, {'channel': 'nightly'}, {'notes': 'x' * 20001},
                        {'restart_required': 'true'}, {'data_upgrade': 0}, {'notes': '<script>bad</script>'},
                        {'version': '1.0rc1'}, {'qgis_maximum': None}):
            bad.append(catalog(release(**changes)))
        for data in bad:
            with self.subTest(data=data[:100]), self.assertRaises(ValueError):
                api.parse_catalog(data, 'preview', '0.12.2', '3.44')
        with self.assertRaises(ValueError):
            api.parse_catalog(catalog(), 'nightly', '0.12.2', '3.44')

    def test_selects_numeric_compatible_channel(self):
        api = module()
        self.assertTrue(hasattr(api, 'parse_catalog'), 'catalog selection missing')
        parse = api.parse_catalog
        data = catalog(release(), release(version='0.12.10', channel='stable'), release(version='0.13.0', qgis_minimum='4.0', qgis_maximum='4.99'))
        chosen = parse(data, 'stable', '0.12.2', '3.44.14')
        self.assertEqual(chosen['status'], 'available')
        self.assertEqual(chosen['release']['version'], '0.12.10')
        self.assertEqual(parse(data, 'preview', '0.12.10', '3.44')['status'], 'incompatible')
        self.assertEqual(parse(catalog(release()), 'stable', '0.12.2', '3.44'), dict(status='empty', release=None))
        self.assertEqual(parse(catalog(release()), 'preview', '0.12.3', '3.44')['status'], 'current')


class MetadataTests(unittest.TestCase):
    def test_reads_actual_metadata_and_numeric_versions(self):
        assert SPEC is not None and SPEC.loader is not None
        self.assertTrue(SPEC.origin and Path(SPEC.origin).is_file(), 'update catalogue foundation is missing')
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        installed = module.read_installed(PLUGIN_ROOT)
        self.assertEqual(installed['version'], '0.12.2')
        self.assertTrue(installed['experimental'])
        self.assertEqual(installed['qgis_minimum'], '3.28')
        self.assertEqual(installed['qgis_maximum'], '')
        self.assertGreater(module.version_key('0.12.10'), module.version_key('0.12.9'))
        self.assertEqual(module.version_key('3.44.0'), module.version_key('3.44'))
        for value in ('1.0rc1', 'v1.2', '1..2', '', '1.2-3', '01.2'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.version_key(value)


class PackageTests(unittest.TestCase):
    def test_rejects_encryption_and_bounded_archive_limits(self):
        api = module()
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            path = Path(temporary) / 'bad.zip'
            package(path)
            data = bytearray(path.read_bytes())
            # Mark both local and central metadata entries encrypted.
            struct.pack_into('<H', data, 6, struct.unpack_from('<H', data, 6)[0] | 1)
            central = data.index(b'PK\x01\x02')
            struct.pack_into('<H', data, central + 8, struct.unpack_from('<H', data, central + 8)[0] | 1)
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')
            package(path)
            with patch.object(api, 'MAX_PACKAGE_BYTES', path.stat().st_size - 1):
                with self.assertRaises(ValueError):
                    api.verify_package(path, None, '3.44')
            package(path, metadata=META + '#' * 65536)
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')
            package(path, extra=[(f'ag_tech_tooling/file{n}.py', '# small') for n in range(4096)])
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')
            item = package(path, metadata=META.replace('experimental=True', 'experimental=False'))
            item['channel'] = 'stable'
            self.assertFalse(api.verify_package(path, item, '3.44')['experimental'])

    def test_corrupted_deflate_is_a_validation_error(self):
        api = module()
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            path = Path(temporary) / 'corrupted.zip'
            package(path)
            data = bytearray(path.read_bytes())
            with zipfile.ZipFile(path) as archive:
                entry = archive.getinfo('ag_tech_tooling/plugin.py')
                start = entry.header_offset + 30
                name_len, extra_len = struct.unpack_from('<HH', data, entry.header_offset + 26)
                start += name_len + extra_len
                data[start:start + entry.compress_size] = b'\xff' * entry.compress_size
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')

    def test_rejects_self_extracting_prefix(self):
        api = module()
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            path = Path(temporary) / 'sfx.zip'
            package(path)
            path.write_bytes(b'MZ executable prefix' + path.read_bytes())
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')

    def test_rejects_dependency_installs_and_alternate_metadata_targets(self):
        api = module()
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            path = Path(temporary) / 'bad.zip'
            package(path, metadata=META + 'plugin_dependencies=some_other_plugin\n')
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')
            for extra in ([('ag_tech_tooling/aaa/metadata.txt', META)],
                          [('ag_tech_tooling/A/a.py', '# a'), ('ag_tech_tooling/a/b.py', '# b')],
                          [('ag_tech_tooling//odd.py', '# a')]):
                package(path, extra=extra)
                with self.subTest(extra=extra), self.assertRaises(ValueError):
                    api.verify_package(path, None, '3.44')

    def test_rejects_unsafe_archives_and_bad_metadata(self):
        api = module()
        names = ['../escape.py', 'other/plugin.py', 'ag_tech_tooling/../escape.py',
                 'ag_tech_tooling\\escape.py', '/ag_tech_tooling/a.py',
                 'ag_tech_tooling/PLUGIN.py', 'ag_tech_tooling/plugin.py',
                 'ag_tech_tooling/a.exe', 'ag_tech_tooling/a:stream.py',
                 'ag_tech_tooling/CON.py', 'ag_tech_tooling/a./b.py',
                 'ag_tech_tooling/farm.gpkg', 'ag_tech_tooling/a.py/child.py']
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            path = Path(temporary) / 'bad.zip'
            for name in names:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    package(path, extra=[(name, b'x'), ('ag_tech_tooling/a.py', b'x')])
                with self.subTest(name=name), self.assertRaises(ValueError):
                    api.verify_package(path, None, '3.44')
            link = zipfile.ZipInfo('ag_tech_tooling/link.py')
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            package(path, extra=[(link, b'../../outside')])
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')
            package(path, extra=[('ag_tech_tooling/bomb.txt', b'0' * 2000000)])
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')
            for metadata in ('[general]\nversion=1.0\n', META.replace('True', 'maybe'),
                             META + 'version=1.0\n', META + 'qgisMaximumVersion=3.0\n',
                             '[DEFAULT]\nversion=0.12.3\n' + META.replace('version=0.12.3\n', '')):
                package(path, metadata=metadata)
                with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                    api.verify_package(path, None, '3.44')
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('ag_tech_tooling/metadata.txt', META)
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')
            path.write_bytes(b'not a zip')
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.44')

    def test_verifies_integrity_and_metadata_without_extracting(self):
        api = module()
        self.assertTrue(hasattr(api, 'verify_package'), 'package verification missing')
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            path = Path(temporary) / 'plugin.zip'
            item = package(path)
            result = api.verify_package(path, item, '3.44.14')
            self.assertEqual(result['version'], '0.12.3')
            self.assertTrue(result['experimental'])
            self.assertEqual(api.verify_package(path, None, '3.44'), result)
            self.assertEqual(list(Path(temporary).iterdir()), [path])
            for changes in ({'size': item['size'] + 1}, {'sha256': '0' * 64}, {'version': '0.12.4'},
                            {'channel': 'stable'}, {'qgis_minimum': '3.30'}):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    api.verify_package(path, dict(item, **changes), '3.44')
            with self.assertRaises(ValueError):
                api.verify_package(path, None, '3.22')


class SnapshotTests(unittest.TestCase):
    def test_snapshot_rejects_links_and_cleans_failed_copy(self):
        api = module()
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            root = Path(temporary)
            plugin = root / 'ag_tech_tooling'
            plugin.mkdir()
            (plugin / 'metadata.txt').write_text(META, encoding='utf-8')
            (plugin / '__init__.py').write_text('# init', encoding='utf-8')
            (plugin / 'plugin.py').write_text('# plugin', encoding='utf-8')
            recovery = root / 'recovery'
            original = api.shutil.copyfile
            def corrupt(source, target):
                original(source, target)
                Path(target).write_bytes(b'corrupted')
            with patch.object(api.shutil, 'copyfile', side_effect=corrupt):
                with self.assertRaises(ValueError):
                    api.snapshot_plugin(plugin, recovery)
            self.assertEqual(list(recovery.iterdir()), [])
            outside = root / 'outside'
            outside.mkdir()
            (outside / 'private.txt').write_text('private', encoding='utf-8')
            link = plugin / 'escape'
            try:
                os.symlink(outside, link, target_is_directory=True)
            except OSError:
                if os.name != 'nt':
                    raise
                result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            try:
                with self.assertRaises(ValueError):
                    api.snapshot_plugin(plugin, recovery)
            finally:
                if link.is_symlink():
                    link.unlink()
                else:
                    link.rmdir()
            self.assertEqual((outside / 'private.txt').read_text(), 'private')

    def test_snapshots_only_plugin_source_and_never_overwrites(self):
        api = module()
        self.assertTrue(hasattr(api, 'snapshot_plugin'), 'recovery snapshot missing')
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            root = Path(temporary)
            plugin = root / 'ag_tech_tooling'
            plugin.mkdir()
            for name, data in [('metadata.txt', META), ('__init__.py', '# init'), ('plugin.py', '# plugin'), ('farm.gpkg', 'private')]:
                (plugin / name).write_text(data, encoding='utf-8')
            (plugin / '__pycache__').mkdir()
            (plugin / '__pycache__/plugin.pyc').write_bytes(b'cache')
            (plugin / 'farm').mkdir()
            (plugin / 'farm/private.txt').write_text('private farm data', encoding='utf-8')
            first = api.snapshot_plugin(plugin, root / 'recovery')
            second = api.snapshot_plugin(plugin, root / 'recovery')
            self.assertNotEqual(first, second)
            self.assertTrue(first.is_dir())
            self.assertEqual((first / 'plugin.py').read_text(), '# plugin')
            self.assertFalse((first / 'farm.gpkg').exists())
            self.assertFalse((first / '__pycache__').exists())
            self.assertFalse((first / 'farm').exists())
            self.assertEqual((plugin / 'farm.gpkg').read_text(), 'private')
            with self.assertRaises(ValueError):
                api.snapshot_plugin(plugin, plugin / 'recovery')


class BuilderTests(unittest.TestCase):
    def test_cli_records_explicit_data_upgrade_warning(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            folder = Path(temporary)
            path = folder / 'plugin.zip'
            item = package(path)
            notes = folder / 'notes.txt'
            notes.write_text('Requires a separately reviewed workspace upgrade.', encoding='utf-8')
            output = folder / 'candidate.json'
            command = [sys.executable, str(ROOT / 'tools/build_update_catalog.py'),
                       '--package', str(path), '--channel', 'preview', '--url', item['url'],
                       '--notes', str(notes), '--output', str(output), '--data-upgrade']
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(json.loads(output.read_bytes())['releases'][0]['data_upgrade'])

    def test_cli_builds_from_real_zip_and_preserves_existing_releases(self):
        script = ROOT / 'tools/build_update_catalog.py'
        self.assertTrue(script.is_file(), 'catalogue builder missing')
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            folder = Path(temporary)
            path = folder / 'plugin.zip'
            item = package(path)
            notes = folder / 'notes.txt'
            notes.write_text('Plain release notes\n', encoding='utf-8')
            output = folder / 'candidate.json'
            existing = release(version='0.12.1', channel='stable')
            output.write_bytes(catalog(existing))
            command = [sys.executable, str(script), '--package', str(path), '--channel', 'preview',
                       '--url', item['url'], '--notes', str(notes), '--output', str(output)]
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            document = json.loads(output.read_bytes())
            self.assertEqual(len(document['releases']), 2)
            self.assertEqual(document['releases'][0], existing)
            result = document['releases'][1]
            self.assertEqual(result['sha256'], item['sha256'])
            self.assertEqual(result['size'], path.stat().st_size)
            self.assertEqual(result['notes'], notes.read_text())
            self.assertIn('not published', run.stdout.lower())
            before = output.read_bytes()
            repeat = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertEqual(before, output.read_bytes())
            command[command.index('preview')] = 'stable'
            command[-1] = str(folder / 'stable.json')
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)



if __name__ == '__main__':
    unittest.main()
